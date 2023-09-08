import logging
import time
import tqdm
from typing import List, Dict
from scipy.spatial import distance
import numpy as np

from .comparison_pair import ComparisonPair
from .comparison_pairs_generator import ComparisonPairsGenerator
from .comparison_result import ComparisonResult

from .code_unit import CodeUnit
from .detection.gst import gst
from .detection.tiles_manager import TilesManager

from .detection_config import DetectionConfig
from .flatten_code_units import FlattenCodeUnits
from .token import Token, TokenKind
from .tokenized_program import TokenizedProgram
from .unroll_code_units import UnrollCodeUnits
from .utils.multiprocessing import execute_function_in_multiprocesses


class DetectionEngine:
    @staticmethod
    def get_sequence_from_tokens(tokens: List[Token]) -> str:
        return "".join([token.token_kind.short_name for token in tokens])

    @staticmethod
    def token_to_str(distinguish_operators_symbols: bool, compare_function_names_in_function_calls: bool, token: Token):
        token_str = token.token_kind.short_name

        if token.token_kind in [TokenKind.StringLiteral]:
            token_str += token.name
        if token.token_kind == TokenKind.FunctionCall:
            token_str += token.name
        elif distinguish_operators_symbols:
            if token.token_kind in [TokenKind.BinaryOp, TokenKind.UnaryOp, TokenKind.CompoundAssigmentOp]:
                token_str += token.name
        return token_str

    @staticmethod
    def compare_tokens(config_and_comparison_pair):
        config, comparison_pair = config_and_comparison_pair
        distinguish_operators_symbols, compare_function_names_in_function_calls, minimal_search_length, initial_search_length = config
        tokens_a, tokens_b = (comparison_pair.tokens_a, comparison_pair.tokens_b)

        logging.debug("analyzing comparison pair...")
        start_time = time.process_time()
        token_to_str = lambda token: DetectionEngine.token_to_str(distinguish_operators_symbols, compare_function_names_in_function_calls, token)

        tiles_a = TilesManager(tokens_a, token_to_str)
        tiles_b = TilesManager(tokens_b, token_to_str)
        matches = gst(tiles_a, tiles_b, minimal_search_length, initial_search_length)
        # matches, marks_a, marks_b = scored_string_tilling(tokens_a, tokens_b, minimal_search_length, compare_function=token_comparison_function)
        # return ComparisonResult(comparison_pair, matches, marks_a, marks_b)
        logging.debug(f"done {time.process_time() - start_time} ...")
        return ComparisonResult(comparison_pair, matches, tiles_a.marks, tiles_b.marks)

    def apply_cos_condition(self, pairs, config: DetectionConfig):
        filtered_pairs: List[ComparisonPair] = []

        if config.ks_condition_value == -1:
            for p in pairs:
                a: List[Token] = p.tokens_a
                b: List[Token] = p.tokens_b

                histogram_a: Dict[TokenKind, int] = dict.fromkeys(TokenKind.cursors_unique_list_of_short_names, 0)
                histogram_b: Dict[TokenKind, int] = dict.fromkeys(TokenKind.cursors_unique_list_of_short_names, 0)

                for t in a:
                    if t.token_kind.short_name not in histogram_a:
                        histogram_a[t.token_kind.short_name] = 0
                    histogram_a[t.token_kind.short_name] += 1

                for t in b:
                    if t.token_kind.short_name not in histogram_b:
                        histogram_b[t.token_kind.short_name] = 0
                    histogram_b[t.token_kind.short_name] += 1
                np_a = np.fromiter(histogram_a.values(), dtype=int)
                np_b = np.fromiter(histogram_b.values(), dtype=int)

                if distance.cosine(np_a, np_b) > config.ks_condition_value:
                    filtered_pairs.append(p)
            logging.info(f"({len(pairs)}, {len(filtered_pairs)}) pairs are left after filtering using cosine similarity.")
        else:
            filtered_pairs = pairs

        return filtered_pairs

    def __generate_comparison_pairs__(
        self, tokenized_programs: List[TokenizedProgram], config: DetectionConfig, selected_programs_to_compare: List[str]
    ) -> List[ComparisonPair]:
        for tokenized_program in tqdm.tqdm(tokenized_programs):
            if config.unroll_ast:
                tokenized_program = UnrollCodeUnits.unroll(tokenized_program, config.remove_unrolled_function, config.unroll_only_simple_functions)
            tokenized_program = FlattenCodeUnits.flatten(tokenized_program)

        logging.info("generating comparison pairs...")
        tokenized_programs = sorted(tokenized_programs, key=lambda p: p.author)
        comparison_pairs_generator = ComparisonPairsGenerator(
            config.compare_whole_program, config.max_number_of_differences_in_single_comparison_pair, config.assign_functions_based_on_types
        )
        pairs = comparison_pairs_generator.generate(tokenized_programs, selected_programs_to_compare)

        return self.apply_cos_condition(pairs, config)

    def analyze(self, tokenized_programs: List[TokenizedProgram], config: DetectionConfig = DetectionConfig(), selected_programs_to_compare: List[str] = []):
        comparison_pairs: List[ComparisonPair] = self.__generate_comparison_pairs__(tokenized_programs, config, selected_programs_to_compare)
        if config.compare_whole_program:
            for p in tokenized_programs:
                merged_code_ast = []
                for code_unit in p.code_units:
                    merged_code_ast += code_unit.ast
                p.code_units = [CodeUnit(merged_code_ast)]
        logging.info(f"analyzing {len(comparison_pairs)} comparison_pairs...")

        rkr_gst_config = (
            config.distinguish_operators_symbols,
            config.compare_function_names_in_function_calls,
            config.minimal_search_length,
            config.initial_search_length,
        )
        if config.n_processors == 1:
            comparison_results = [DetectionEngine.compare_tokens((rkr_gst_config, pair)) for pair in tqdm.tqdm(comparison_pairs)]
        else:
            chunksize = int(len(comparison_pairs) / (config.n_processors * 10)) if len(comparison_pairs) > (config.n_processors * 10) else 1
            chunksize = max([1, chunksize])
            comparison_results = execute_function_in_multiprocesses(
                DetectionEngine.compare_tokens, list(zip([rkr_gst_config] * len(comparison_pairs), comparison_pairs)), config.n_processors, 1.0, chunksize
            )
        return comparison_results
