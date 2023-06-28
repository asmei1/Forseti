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
def run_detection(
    file_1: Tuple[str, str], file_2: Tuple[str, str], forseti_args=["--maximal_similarity_threshold", "0.0"]
) -> Tuple[Dict[str, Tuple[str, float]], Dict[str, List[Tuple[str, float]]]]:
    parser = argparse.ArgumentParser()
    configure_arg_parser(parser)
    if "--output_path" not in forseti_args:
        # --output_path is not used anywhere - this argument is necessary to use configuration from command line (I don't want to rewrite it again).
        forseti_args.append("--output_path")
        forseti_args.append("C:\\")
    if "--n_processors" not in forseti_args:
        forseti_args.append("--n_processors")
        forseti_args.append("1")
    if "--loglevel" not in forseti_args:
        forseti_args.append("--loglevel")
        forseti_args.append("info")

    programs_sets = [Program([file_1[0]], [file_1[1]], file_1[0]), Program([file_2[0]], [file_2[1]], file_2[0])]
    args = parser.parse_args(forseti_args if forseti_args else None)
    # set_logging_level(args)
    ccode_filter_config = args_to_ccode_filtration_config(args)
    tokenized_programs = CodeTokenizer(CCodeParser(CCodeFilter(ccode_filter_config)), n_processors=args.n_processors).parse_programs(programs_sets)
    if len(tokenized_programs) <= 1:
        raise Exception("One of the programs cannot be parse. Are you sure that passed file contains c code?")

    detection_config = args_to_detection_config(args)
    raw_comparison_results = DetectionEngine().analyze(tokenized_programs, detection_config, args.selected_programs_to_compare)
    comparison_results_processor_config = args_to_comparison_results_processor_config(args)
    comparison_results_processor = ComparisonResultsProcessor(raw_comparison_results, comparison_results_processor_config)
    authors, results = list(comparison_results_processor.get_flat_filtered_processed_results().items())[0]

    similarities, program_1_overlap, program_2_overlap = comparison_results_processor.get_summary()
    code_units_metrics = comparison_results_processor.get_code_units_metrics()

    return (
        list(similarities.values())[0],
        list(program_1_overlap.values())[0],
        list(program_2_overlap.values())[0],
        code_units_metrics,
        generate_html_diff_page(
            results, comparison_results_processor.get_tokenized_program(authors[0]), comparison_results_processor.get_tokenized_program(authors[1])
        ),
    )


if __name__ == "__main__":
    import os
    import itertools

    # program_1_filepath = r'C:\Projects\Forseti\file.c'
    # program_2_filepath = r'C:\Projects\Forseti\file2.c'
    # program_2_filepath_temp = r'C:\Projects\Forseti\file2sdfsdf.c'
    # program_2_filepath_temp2 = r'C:\Projects\Forseti\file2sdfsdfs.c'

    # path = r'C:\Projects\Forseti\new_test_data\dante\603'
    path = r"C:\Projects\Forseti\test_data\macro_test"
    folders = []
    codes = []
    for folder in os.listdir(path):
        folders.append(os.path.join(path, folder))
        for file in os.listdir(os.path.join(path, folder)):
            with open(os.path.join(path, folder, file), "r", encoding="latin-1") as f:
                codes.append([folder, f.read()])

    for c in codes:
        c[1] = [line + "\n" for line in c[1].split("\n")]

    for pair in itertools.combinations(codes, 2):
        a, b = pair
        (folder_a, code_a) = (a[0], a[1])
        (folder_b, code_b) = (b[0], b[1])

        print(folder_a, folder_b)
        try:
            s, o1, o2, function_metrics, diff_report = run_detection(["file1.c", code_a], ["file2.c", code_b])
            print(folder_a, folder_b, " = ", s, o1, o2)
        except Exception as e:
            print(e)
        except:
            print("Something goes wrong")
        print()
