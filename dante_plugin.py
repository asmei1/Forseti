from typing import Tuple, Dict, List
import argparse
from pl.forseti.c_code.ccode_parser import CCodeParser
from pl.forseti.c_code.ccode_filter import CCodeFilter
from pl.forseti.program import Program
from pl.forseti.code_tokenizer import CodeTokenizer
from pl.forseti.detection_engine import DetectionEngine
from pl.forseti.report_generation.report_generator import ReportGenerator
from pl.forseti.report_generation.html_diff_generator import generate_html_diff_page
from pl.forseti.comparison_results_processor import ComparisonResultsProcessor
from pl.forseti.report_generation.report_generator import ReportGenerator

from app.command_line_app_utils import *


# Compose plagiarism detection workflow using Forseti library. Its it simplified version of command line app, prepared for Dante.
# One can pass here almost all parameters which can be used in command line app.
# Setting --maximal_similarity_threshold to 0.0 is recommended.
def run_detection(file_1: Tuple[str, str], file_2: Tuple[str, str], forseti_args=['--maximal_similarity_threshold', '0.0']) -> Tuple[Dict[str, Tuple[str, float]], Dict[str, List[Tuple[str, float]]]]:
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
    raw_comparison_results = DetectionEngine().analyze(tokenized_programs, detection_config, args.selected_programs_to_compare)
    comparison_results_processor_config = args_to_comparison_results_processor_config(args)
    comparison_results_processor = ComparisonResultsProcessor(raw_comparison_results, comparison_results_processor_config)
    authors, results = list(comparison_results_processor.get_flat_filtered_processed_results().items())[0]
    

    similarities, program_1_overlap, program_2_overlap = comparison_results_processor.get_summary()
    code_units_metrics = comparison_results_processor.get_code_units_metrics()

    return similarities, program_1_overlap, program_2_overlap, code_units_metrics, generate_html_diff_page(results, comparison_results_processor.get_tokenized_program(authors[0]), comparison_results_processor.get_tokenized_program(authors[1]))



if __name__ == "__main__":
    program_1_filepath = r'C:\file.c'
    program_2_filepath = r'C:\file2.c'
    file1 = open(program_1_filepath, mode='r', encoding='latin-1')
    file2 = open(program_2_filepath, mode='r', encoding='latin-1')
    program_1 = [program_1_filepath, file1.readlines()]
    program_2 = [program_2_filepath, file2.readlines()]
    s, o1, o2, function_metrics, diff_report = run_detection(program_1, program_2)
    import os
    # optional
    report_path = r'C:\report.html'
    with open(', 'w', encoding='latin-1') as outfile:
        outfile.write(diff_report)
                