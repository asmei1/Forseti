import logging
from typing import List

from .tokenized_program import TokenizedProgram
from .flatten_code_units import FlattenCodeUnits
from .unroll_code_units import UnrollCodeUnits
from .token import Token
from .submission import Submission
from .comparison_result import ComparisonResult
from .submission_generator import SubmissionGenerator
from .detection_config import DetectionConfig
from .utils.multiprocessing import execute_function_in_multiprocesses
from .detection.tiles_manager import TilesManager
from .detection.rkr_gst import rkr_gst
from .detection.get_sequence_from_tokens import get_sequence_from_tokens


    

class DetectionEngine:
    @staticmethod
    def token_comparison_function(token_a: Token, token_b: Token):
        return token_a.token_kind == token_b.token_kind
    
    @staticmethod
    def compare_tokens(submission):
        tokens_a, tokens_b = (submission.tokens_a, submission.tokens_b)
        tiles_a = TilesManager(tokens_a)
        tiles_b = TilesManager(tokens_b)

        logging.info("analyzing submission...")
        matches = rkr_gst(tiles_a, tiles_b, 5, 8, get_sequence_from_tokens, DetectionEngine.token_comparison_function)
        logging.info("done...")
        return ComparisonResult(submission, matches)
    
    def __generate_submissions__(self, tokenized_programs: List[TokenizedProgram], config: DetectionConfig) -> List[Submission]:
        for tokenized_program in tokenized_programs:
            if config.unroll_ast:
                logging.info("unrolling program...")
                tokenized_program = UnrollCodeUnits.unroll(tokenized_program, config.remove_unrolled_function, config.unroll_only_simple_functions)
            logging.info("flattening program...")
            tokenized_program = FlattenCodeUnits.flatten(tokenized_program)

        logging.info("generating submission pairs...")
        submission_generator = SubmissionGenerator(config.compare_whole_program, config.max_number_of_differences_in_single_submission, config.assign_functions_based_on_types)

        return submission_generator.generate(tokenized_programs)

        


    def analyze(self, tokenized_programs: List[TokenizedProgram], config: DetectionConfig = DetectionConfig()):
        logging.info("analyzing submissions...")
        submissions: List[Submission] = self.__generate_submissions__(tokenized_programs, config)
        if config.n_processors == -1:
            comparison_results = [DetectionEngine.compare_tokens(submission) for submission in submissions]
        else:
            comparison_results = execute_function_in_multiprocesses(DetectionEngine.compare_tokens, submissions, config.n_processors)
        return comparison_results







        