from typing import Tuple, Dict, List
import argparse
from pl.forseti.c_code.ccode_parser import CCodeParser
from pl.forseti.c_code.ccode_filter import CCodeFilter
from pl.forseti.program import Program
from pl.forseti.code_tokenizer import CodeTokenizer
from pl.forseti.detection_engine import DetectionEngine
from pl.forseti.report_generation.report_generator import ReportGenerator
from pl.forseti.report_generation.html_diff_generator import generate_html_diff_page
from app.command_line_app_utils import *


# Compose plagiarism detection workflow using Forseti library. Its it simplified version of command line app, prepared for Dante.
# One can pass here almost all parameters which can be used in command line app.
# Setting --minimal_similarity_threshold to 0.0 is recommended.
# Function return 3 elements:
#   - dictonary with 3 overall metrics (similarity, program_1_overlap, program_2_overlap).
#   - dictonary with functions comparisons. Key of this dictonary is composed of function names and the values are tuple of author names and similarity ratio.
#   - html diff report as string.
def run_detection(file_1: Tuple[str, str], file_2: Tuple[str, str], forseti_args=['--minimal_similarity_threshold', '0.0']) -> Tuple[Dict[str, Tuple[str, float]], Dict[str, List[Tuple[str, float]]]]:
    parser = argparse.ArgumentParser()
    configure_arg_parser(parser)
    if '--output_path' not in forseti_args:
        # --output_path is not used anywhere - this argument is necessary to use configuration from command line (I don't want to rewrite it again). 
        forseti_args.append('--output_path')
        forseti_args.append('C:\\')
    if '--n_processors' not in forseti_args:
        forseti_args.append('--n_processors')
        forseti_args.append('1')
    if '--loglevel' not in forseti_args:
        forseti_args.append('--loglevel')
        forseti_args.append('info')

    programs_sets = [Program([file_1[0]], [file_1[1]], file_1[0]), Program([file_2[0]], [file_2[1]], file_2[0])]
    args = parser.parse_args(forseti_args if forseti_args else None)
    set_logging_level(args)
    ccode_filter_config = args_to_ccode_filtration_config(args)
    tokenized_programs = CodeTokenizer(CCodeParser(CCodeFilter(ccode_filter_config)), n_processors=args.n_processors).parse_programs(programs_sets)

    detection_config = args_to_detection_config(args)
    comparison_results = DetectionEngine().analyze(tokenized_programs, detection_config, args.selected_programs_to_compare)
    report_generation_config = args_to_report_generation_config(args)
    report_generator = ReportGenerator(comparison_results, report_generation_config, args.output_path)

    comparison_results, overall_metrics = report_generator.get_comparison_results()
    code_units_metrics = report_generator.generate_code_unit_metrics()

    files_1 = {}
    files_1[file_1[0]] = file_1[1].split('\n')
    files_2 = {}
    files_2[file_2[0]] = file_2[1].split('\n')
    return overall_metrics, code_units_metrics, generate_html_diff_page(comparison_results[0][1], files_1, files_2)

