import argparse
import logging
import os
import time
import multiprocessing
from typing import List
from .files_scanner import scan_for_files
from .programs_reader import read_programs_sets
from .command_line_app_utils import (
    configure_arg_parser,
    set_logging_level,
    args_to_ccode_filtration_config,
    args_to_detection_config,
    args_to_report_generation_config,
    args_to_comparison_results_processor_config,
)
from pl.forseti.c_code.ccode_parser import CCodeParser
from pl.forseti.c_code.ccode_filter import CCodeFilter
from pl.forseti.code_tokenizer import CodeTokenizer
from pl.forseti.detection_engine import DetectionEngine
from pl.forseti.comparison_results_processor import ComparisonResultsProcessor
from pl.forseti.report_generation.report_generator import ReportGenerator


class CommandLineApp:
    def __init__(self, sys_args) -> None:
        self.parser = argparse.ArgumentParser(description="Performs plagiarism detection")

        program_sources_options = self.parser.add_argument_group("programs sources")
        program_sources_options.add_argument(
            "--paths",
            nargs="+",
            action="append",
            help="Paths to programs which will be checked.",
            required=False,
        )
        program_sources_options.add_argument(
            "--file_patterns",
            nargs="+",
            default=["*.c", "*.h", "*.cpp"],
            help="If folder scanning was enabled, application will look for files with fit to one of the patterns.",
            required=False,
        )

        configure_arg_parser(self.parser)

        self.__args = self.parser.parse_args(args=sys_args)

        set_logging_level(self.__args)

    def run(self) -> None:
        filepaths_sets = []
        if self.__args.paths:
            filepaths_sets = scan_for_files(self.__args.paths, self.__args.file_patterns)
            if not filepaths_sets:
                logging.error("No programs found, please ensure that you pass valid arguments for --path option")
                return
        else:
            self.parser.print_help()
            logging.error("Invalid arguments, please input valid one")
            return
        if -1 == self.__args.n_processors:
            self.__args.n_processors = multiprocessing.cpu_count() - 1
        self.__validate_paths__(filepaths_sets)

        programs_sets = read_programs_sets(filepaths_sets)

        ccode_filter_config = args_to_ccode_filtration_config(self.__args)
        tokenization_start_time = time.process_time()
        tokenized_programs = CodeTokenizer(
            CCodeParser(CCodeFilter(ccode_filter_config)),
            n_processors=self.__args.n_processors,
        ).parse_programs(programs_sets)
        if len(tokenized_programs) <= 1:
            raise Exception("There are no programs which can be parsed and compared.")

        tokenization_end_time = time.process_time()

        detection_config = args_to_detection_config(self.__args)
        detection_start_time = time.process_time()
        raw_comparison_results = DetectionEngine().analyze(
            tokenized_programs,
            detection_config,
            self.__args.selected_programs_to_compare,
        )
        detection_end_time = time.process_time()

        report_generation_config = args_to_report_generation_config(self.__args)
        comparison_results_processor_config = args_to_comparison_results_processor_config(self.__args)
        comparison_results_processor = ComparisonResultsProcessor(raw_comparison_results, comparison_results_processor_config)
        report_generator = ReportGenerator(comparison_results_processor, report_generation_config)
        report_generator.generate_reports()

        print("Tokenization time ", tokenization_end_time - tokenization_start_time)
        print("Detection time ", detection_end_time - detection_start_time)

    def __validate_paths__(self, filepaths_sets: List[List[str]]):
        if len(filepaths_sets) <= 1:
            raise Exception("Invalid number of programs to analyze. Required at least 2 programs to be able to analyze them!")
