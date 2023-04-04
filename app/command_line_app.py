import argparse
import os
import sys
import logging
from typing import List
from .files_scanner import scan_for_files
from .programs_reader import read_programs_sets
from pl.forseti.c_code.ccode_parser import CCodeParser
from pl.forseti.c_code.ccode_filter import CCodeFilter, CCodeFilterConfig
from pl.forseti.code_tokenizer import CodeTokenizer
from pl.forseti.detection_engine import DetectionEngine
from pl.forseti.report_generator import write_comparison_result, ReportGenerator

class CommandLineApp:

    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(description='Performs plagiarism detection')

        self.parser.add_argument(
            '-log',
            '--loglevel',
            default='warning',
            help=
            'Provide logging level. Example --loglevel debug, default=warning')

        program_sources_options = self.parser.add_argument_group('program source')
        program_sources_options.add_argument(
            '--paths',
            nargs='+',
            action='append',
            help='Paths to programs which will be checked.',
            required=False)

        algorithm_options = self.parser.add_argument_group(
            'detection algorithm configuration')
        algorithm_options.add_argument('--sample_option', type=str, required=False)

        report_options = self.parser.add_argument_group(
            'report generation configuration')
        report_options.add_argument('--output_path', type=str, required=True)

        self.__args = self.parser.parse_args(args=None if sys.argv[1:] else ['--help'])

        self.__set_logging_level(self.__args)

    def run(self) -> None:
        filepaths_sets = []
        if self.__args.paths:
            extensions = [".c", ".h"]
            filepaths_sets = scan_for_files(self.__args.paths, extensions)
            if not filepaths_sets:
                logging.error('No programs found, please ensure that you pass valid arguments for --path option')
                return
        else:
            self.parser.print_help()
            logging.error('Invalid arguments, please input valid one')
            return

        self.__validate_paths__(filepaths_sets)

        programs_sets = read_programs_sets(filepaths_sets)
        tokenized_programs = CodeTokenizer(CCodeParser(CCodeFilter(CCodeFilterConfig()))).parse_programs(programs_sets)
        comparison_results = DetectionEngine().analyze(tokenized_programs)
        write_comparison_result(comparison_results)
        report_generator = ReportGenerator(comparison_results, self.__args.output_path)
        report_generator.generate_heatmap_for_whole_programs()
        report_generator.generate_heatmaps()

        

    def __validate_paths__(self, filepaths_sets: List[List[str]]):
        if len(filepaths_sets) <= 1:
            raise Exception("Invalid number of programs to analyze. Required at least 2 programs to be able to analyze them!")
        

    def __set_logging_level(self, args):
        if args.loglevel:
            logging.basicConfig(level=args.loglevel.upper())
            logging.info('Logging now setup.')
