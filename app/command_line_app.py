import argparse
import os
import sys
import logging
import itertools
import time
from typing import List
from .files_scanner import scan_for_files
from .programs_reader import read_programs_sets
from pl.forseti.c_code.ccode_parser import CCodeParser
from pl.forseti.c_code.ccode_filter import CCodeFilter, CCodeFilterConfig
from pl.forseti.code_tokenizer import CodeTokenizer
from pl.forseti.detection_engine import DetectionEngine
from pl.forseti.report_generator import ReportGenerator

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
        program_sources_options.add_argument(
            '--patterns',
            nargs='+',            
            default=["*.c", "*.h"],
            help='If folder scanning was enabled, application will look for files with fit to one of the patterns.',
            required=False)

        processing_options = self.parser.add_argument_group(
            'processing programs configuration')
        processing_options.add_argument('--n_processors', type=int, required=False, default=-1,
                                        help="Number of processors used in programs tokenization. Value -1 means that multiprocessing is disabled.")
        processing_options.add_argument('--filter_struct_declaration', type=bool, required=False, default=True,
                                        help="Defines, if tokens related structure declaration should be filtered.")
        processing_options.add_argument('--filter_function_declaration', type=bool, required=False, default=True,
                                        help="Defines, if structure declaration should be filtered.")
        processing_options.add_argument('--filter_aliasses', type=bool, required=False, default=True,
                                        help="Defines, if alias (typedef) should be filtered.")
        processing_options.add_argument('--filter_mixed_declarations', type=bool, required=False, default=True,
                                        help="""Defines, if cursors for mixing declarations with statments or expressions(DECL_STMT) should be filtered. 
                                        In most cases they should be, due to noise which are introduced in sequence.""")
        processing_options.add_argument('--filter_brackets', type=bool, required=False, default=True,
                                        help="Defines, if brackets from compund statments - {statment; stamtent;} should be filtered. In most cases yes, due to noise reduction.")
        processing_options.add_argument('--filter_parent_expression', type=bool, required=False, default=True,
                                        help="Defines, if parent expression should be filtered. Parent expression for example is int var = (x + y).")


        algorithm_options = self.parser.add_argument_group(
            'detection algorithm configuration')
        algorithm_options.add_argument('--sample_option', type=str, required=False)

        report_options = self.parser.add_argument_group(
            'report generation configuration')
        report_options.add_argument('--output_path', type=str, required=True)

        self.__args = self.parser.parse_args(args=None if sys.argv[1:] else ['--help'])

        self.__set_logging_level(self.__args)

    def args_to_ccode_filtration_config(self):
        config = CCodeFilterConfig()
        config.filter_aliasses = self.__args.filter_aliasses
        config.filter_brackets = self.__args.filter_brackets
        config.filter_function_declaration = self.__args.filter_function_declaration
        config.filter_mixed_declarations = self.__args.filter_mixed_declarations
        config.filter_parent_expression = self.__args.filter_parent_expression
        config.filter_struct_declaration = self.__args.filter_struct_declaration
        return config
    
    def run(self) -> None:
        filepaths_sets = []
        if self.__args.paths:
            filepaths_sets = scan_for_files(self.__args.paths, self.__args.patterns)
            if not filepaths_sets:
                logging.error('No programs found, please ensure that you pass valid arguments for --path option')
                return
        else:
            self.parser.print_help()
            logging.error('Invalid arguments, please input valid one')
            return

        self.__validate_paths__(filepaths_sets)

        programs_sets = read_programs_sets(filepaths_sets)
        ccode_filter_config = self.args_to_ccode_filtration_config()
        tokenization_start_time = time.process_time()
        tokenized_programs = CodeTokenizer(CCodeParser(CCodeFilter(ccode_filter_config)), n_processors=self.__args.n_processors).parse_programs(programs_sets)
        tokenization_end_time = time.process_time()

        detection_start_time = time.process_time()
        comparison_results = DetectionEngine().analyze(tokenized_programs)
        detection_end_time = time.process_time()
        # write_comparison_result(comparison_results)
        report_generator = ReportGenerator(comparison_results, self.__args.output_path)
        report_generator.generate_heatmap_for_whole_programs()
        report_generator.generate_heatmaps()
        print(report_generator.get_comparison_result_in_json()[0])
        print("Tokenization time ", tokenization_end_time - tokenization_start_time)
        print("Detection time ", detection_end_time - detection_start_time)
        

    def __validate_paths__(self, filepaths_sets: List[List[str]]):
        if len(filepaths_sets) <= 1:
            raise Exception("Invalid number of programs to analyze. Required at least 2 programs to be able to analyze them!")
        

    def __set_logging_level(self, args):
        if args.loglevel:
            logging.basicConfig(level=args.loglevel.upper())
            logging.info('Logging now setup.')
