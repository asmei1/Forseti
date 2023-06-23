import logging
import time
from typing import List, Dict
from scipy.stats import ks_2samp
import numpy as np

from .comparison_pair import ComparisonPair
from .comparison_pairs_generator import ComparisonPairsGenerator
from .comparison_result import ComparisonResult
from .detection.rkr_gst import rkr_gst
from .detection.tiles_manager import TilesManager
from .detection_config import DetectionConfig
from .flatten_code_units import FlattenCodeUnits
from .token import Token, TokenKind
from .tokenized_program import TokenizedProgram
from .unroll_code_units import UnrollCodeUnits
from .utils.multiprocessing import execute_function_in_multiprocesses


class DetectionEngine:
    @staticmethod
    def get_sequence_from_tokens(tokens:List[Token]) -> str:
        return ''.join([token.token_kind.short_name for token in tokens])    
    
    @staticmethod
    def token_comparison_function(distinguish_operators_symbols:bool,compare_function_names_in_function_calls:bool, token_a: Token, token_b: Token):
        if token_a.token_kind == token_b.token_kind:
            if token_a.token_kind in [TokenKind.CharacterLiteral]:
                return token_a.name == token_b.name
            if compare_function_names_in_function_calls:
                if token_a.token_kind == TokenKind.FunctionCall:
                    return token_a.name == token_b.name
            if distinguish_operators_symbols:
                if token_a.token_kind in [TokenKind.BinaryOp, TokenKind.UnaryOp, TokenKind.CompoundAssigmentOp] :
                    return token_a.name == token_b.name
            return True

        return False
    
    @staticmethod
    def compare_tokens(config_and_comparison_pair):
        config, comparison_pair = config_and_comparison_pair
        distinguish_operators_symbols, compare_function_names_in_function_calls, minimal_search_length, initial_search_length = config
        tokens_a, tokens_b = (comparison_pair.tokens_a, comparison_pair.tokens_b)
        # a = " ".join([t.token_kind.short_name for t in tokens_a])
        # b = " ".join([t.token_kind.short_name for t in tokens_b])
        tiles_a = TilesManager(tokens_a)
        tiles_b = TilesManager(tokens_b)

        logging.debug("analyzing comparison pair...")
        start_time = time.process_time()
        token_comparison_function = lambda token_a, token_b: DetectionEngine.token_comparison_function(distinguish_operators_symbols, compare_function_names_in_function_calls, token_a, token_b)
        matches = rkr_gst(tiles_a, tiles_b, minimal_search_length, initial_search_length, DetectionEngine.get_sequence_from_tokens, token_comparison_function)
        # matches, marks_a, marks_b = scored_string_tilling(tokens_a, tokens_b, minimal_search_length, compare_function=token_comparison_function)
        # return ComparisonResult(comparison_pair, matches, marks_a, marks_b)
        logging.debug(f"done {time.process_time() - start_time} ...")
        return ComparisonResult(comparison_pair, matches, tiles_a.marks, tiles_b.marks)
    
    def __generate_comparison_pairs__(self, tokenized_programs: List[TokenizedProgram], config: DetectionConfig, selected_programs_to_compare: List[str]) -> List[ComparisonPair]:
        for tokenized_program in tokenized_programs:
            if config.unroll_ast:
                logging.info("unrolling program...")
                tokenized_program = UnrollCodeUnits.unroll(tokenized_program, config.remove_unrolled_function, config.unroll_only_simple_functions)
            logging.info("flattening program...")
            tokenized_program = FlattenCodeUnits.flatten(tokenized_program)

        logging.info("generating comparison pairs...") 
        tokenized_programs = sorted(tokenized_programs, key=lambda p: p.author)
        comparison_pairs_generator = ComparisonPairsGenerator(config.compare_whole_program, config.max_number_of_differences_in_single_comparison_pair, config.assign_functions_based_on_types)
        pairs = comparison_pairs_generator.generate(tokenized_programs, selected_programs_to_compare)

        filtered_pairs: List[ComparisonPair] = []

        if config.ks_condition_value == -1:
            for p in pairs:
                a:List[Token] = p.tokens_a
                b:List[Token] = p.tokens_b

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

                if ks_2samp(np_a, np_b).pvalue > config.ks_condition_value:
                    filtered_pairs.append(p)
        else:
            filtered_pairs = pairs
        
        logging.info(f"({len(pairs)}, {len(filtered_pairs)}) pairs are left after filtering using ks test")

        return filtered_pairs


    def analyze(self, tokenized_programs: List[TokenizedProgram], config: DetectionConfig = DetectionConfig(), selected_programs_to_compare: List[str] = []):
        comparison_pairs: List[ComparisonPair] = self.__generate_comparison_pairs__(tokenized_programs, config, selected_programs_to_compare)
        logging.info(f"analyzing {len(comparison_pairs)} comparison_pairs...")
        
        rkr_gst_config = (config.distinguish_operators_symbols, config.compare_function_names_in_function_calls, config.minimal_search_length, config.initial_search_length)
        if config.n_processors == 1:
            comparison_results = [DetectionEngine.compare_tokens((rkr_gst_config, pair)) for pair in comparison_pairs]
        else:
            comparison_results = execute_function_in_multiprocesses(DetectionEngine.compare_tokens, list(zip([rkr_gst_config]*len(comparison_pairs), comparison_pairs)), config.n_processors)
        return comparison_results







        