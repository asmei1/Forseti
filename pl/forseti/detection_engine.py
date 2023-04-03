import logging
import dataclasses
from typing import List
from collections import deque
from .tokenized_program import TokenizedProgram
from .flatten_code_units import FlattenCodeUnits
from .unroll_code_units import UnrollCodeUnits
from .submission import Submission
from .comparison_result import ComparisonResult
from .submission_generator import SubmissionGenerator
from .detection.tiles_manager import TilesManager
from .detection.rkr_gst import rkr_gst
from .detection.get_sequence_from_tokens import get_sequence_from_tokens

@dataclasses.dataclass
class DetectionConfig:
    unroll_ast: bool = True
    remove_unrolled_function: bool = True
    unroll_only_simple_functions: bool = True


class DetectionEngine:
    def __init__(self) -> None:
        pass
    
    def __generate_submissions__(self, tokenized_programs: List[TokenizedProgram], config: DetectionConfig) -> List[Submission]:
        for tokenized_program in tokenized_programs:
            if config.unroll_ast:
                logging.info("unrolling program...")
                tokenized_program = UnrollCodeUnits.unroll(tokenized_program, config.remove_unrolled_function, config.unroll_only_simple_functions)
            logging.info("flattening program...")
            tokenized_program = FlattenCodeUnits.flatten(tokenized_program)

        logging.info("generating submission pairs...")
        submission_generator = SubmissionGenerator(compare_whole_programs=False)

        return submission_generator.generate(tokenized_programs)

    def analyze(self, tokenized_programs: List[TokenizedProgram], config: DetectionConfig = DetectionConfig()):
        logging.info("analyzing submissions...")
        submissions: List[Submission] = self.__generate_submissions__(tokenized_programs, config)
        comparison_results: List[ComparisonResult] = []
        token_comparision_function = lambda token_a, token_b: token_a.token_kind == token_b.token_kind
        for submission in submissions:
            tokens_a, tokens_b = (submission.tokens_a, submission.tokens_b)
            tiles_a = TilesManager(tokens_a)
            tiles_b = TilesManager(tokens_b)

            logging.info("analyzing submission...")
            matches = rkr_gst(tiles_a, tiles_b, 5, 8, get_sequence_from_tokens, token_comparision_function)
            logging.info("done...")
            comparison_results.append(ComparisonResult(submission, matches))
            

            # # print(" ".join([t.token_kind.short_name for t in tokens_a]))
            # # print(" ".join([t.token_kind.short_name for t in tokens_b]))
            # if res:
            #     print(2 * res[0]["length"] / (len(tokens_a) + len(tokens_b)))
            # else:
            #     print(0.0)

            
        return comparison_results







        