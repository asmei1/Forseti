import argparse
import os
import logging
import itertools
import time
import multiprocessing
from typing import List
from .files_scanner import scan_for_files
from .programs_reader import read_programs_sets
from pl.forseti.c_code.ccode_parser import CCodeParser
from pl.forseti.c_code.ccode_filter import CCodeFilter, CCodeFilterConfig
from pl.forseti.code_tokenizer import CodeTokenizer
from pl.forseti.detection_engine import DetectionEngine
from pl.forseti.detection_config import DetectionConfig
from pl.forseti.report_generation.report_generator import ReportGenerator
from pl.forseti.report_generation.report_generation_config import ReportGenerationConfig

def get_available_number_of_cores():
    return multiprocessing.cpu_count() - 1 if multiprocessing.cpu_count() - 1 else 1
def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
    
class CommandLineApp:

    def __init__(self, sys_args) -> None:
        self.parser = argparse.ArgumentParser(description='Performs plagiarism detection')

        self.parser.add_argument(
            '-log',
            '--loglevel',
            default='warning',
            help=
            'Provide logging level. Example --loglevel debug, default=warning')

        program_sources_options = self.parser.add_argument_group('programs sources')
        program_sources_options.add_argument(
            '--paths',
            nargs='+',
            action='append',
            help='Paths to programs which will be checked.',
            required=False)
        program_sources_options.add_argument(
            '--file_patterns',
            nargs='+',            
            default=["*.c", "*.h"],
            help='If folder scanning was enabled, application will look for files with fit to one of the patterns.',
            required=False)

        processing_options = self.parser.add_argument_group('processing programs configuration')
        processing_options.add_argument('--n_processors', type=int, required=False, default=get_available_number_of_cores(),
                                        help="Number of processors used in programs tokenization. Value -1 means that all available processors will be used.")
        processing_options.add_argument('--filter_struct_declaration', type=str2bool, nargs='?', const=True,required=False, default=True,
                                        help="Defines, if tokens related structure declaration should be filtered.")
        processing_options.add_argument('--filter_function_declaration', type=str2bool, nargs='?', const=True,required=False, default=True,
                                        help="Defines, if structure declaration should be filtered.")
        processing_options.add_argument('--filter_aliasses', type=str2bool, nargs='?', const=True,required=False, default=True,
                                        help="Defines, if alias (typedef) should be filtered.")
        processing_options.add_argument('--filter_mixed_declarations', type=str2bool, nargs='?', const=True,required=False, default=True,
                                        help="""Defines, if cursors for mixing declarations with statments or expressions(DECL_STMT) should be filtered. 
                                        In most cases they should be, due to noise which are introduced in sequence.""")
        processing_options.add_argument('--filter_brackets', type=str2bool, nargs='?', const=True,required=False, default=True,
                                        help="Defines, if brackets from compund statments - {statment; stamtent;} should be filtered. In most cases yes, due to noise reduction.")
        processing_options.add_argument('--filter_parent_expression', type=str2bool, nargs='?', const=True,required=False, default=True,
                                        help="Defines, if parent expression should be filtered. Parent expression for example is int var = (x + y).")


        report_generation_options = self.parser.add_argument_group('report generation configuration')
        report_generation_options.add_argument('--generate_heatmap_for_whole_programs', type=str2bool, nargs='?', const=True,default=False, required=False)
        report_generation_options.add_argument('--generate_heatmap_for_code_units', type=str2bool, nargs='?', const=True,default=False, required=False)
        report_generation_options.add_argument('--generate_jsons', type=str2bool, nargs='?', const=True,default=True, required=False)
        report_generation_options.add_argument('--generate_html_diffs', type=str2bool, nargs='?', const=True,default=True, required=False)
        report_generation_options.add_argument('--output_path', type=str, required=True)
        report_generation_options.add_argument('--minimal_similarity_threshold', type=float, required=False, default=0.5)
        report_generation_options.add_argument('--maximal_similarity_threshold', type=float, required=False, default=1.0)
        

        algorithm_options = self.parser.add_argument_group('detection algorithm configuration')
        algorithm_options.add_argument('--minimal_search_length', type=int, default=8, required=False)
        algorithm_options.add_argument('--initial_search_length', type=int, default=20, required=False)
        algorithm_options.add_argument('--compare_function_names_in_function_calls', type=str2bool, nargs='?', const=True,default=True, required=False)
        algorithm_options.add_argument('--distinguish_operators_symbols', type=str2bool, nargs='?', const=True,default=True, required=False)
        algorithm_options.add_argument('--unroll_ast', type=str2bool, nargs='?', const=True,default=True, required=False)
        algorithm_options.add_argument('--remove_unrolled_function', type=str2bool, nargs='?', const=True,default=True, required=False)
        algorithm_options.add_argument('--unroll_only_simple_functions', type=str2bool, nargs='?', const=True,default=True, required=False)
        algorithm_options.add_argument('--compare_whole_program', type=str2bool, nargs='?', const=True,default=False, required=False)
        algorithm_options.add_argument('--max_number_of_differences_in_single_comparison_pair', type=int, default=-1, required=False)
        algorithm_options.add_argument('--selected_programs_to_compare', nargs='+', required=False, default=[])

        self.__args = self.parser.parse_args(args=sys_args)

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
    
    def args_to_detection_config(self):
        config = DetectionConfig()
        #TODO add rest
        config.n_processors = self.__args.n_processors 
        config.minimal_search_length = self.__args.minimal_search_length
        config.initial_search_length = self.__args.initial_search_length
        config.distinguish_operators_symbols = self.__args.distinguish_operators_symbols
        config.compare_function_names_in_function_calls = self.__args.compare_function_names_in_function_calls
        config.unroll_ast = self.__args.unroll_ast
        config.unroll_only_simple_functions = config.unroll_ast and self.__args.unroll_only_simple_functions
        config.remove_unrolled_function = config.unroll_ast and self.__args.remove_unrolled_function
        config.compare_whole_program = self.__args.compare_whole_program
        config.max_number_of_differences_in_single_comparison_pair = self.__args.max_number_of_differences_in_single_comparison_pair
        return config
    
    def args_to_report_generation_config(self):
        config = ReportGenerationConfig()
        config.generate_heatmap_for_whole_programs = self.__args.generate_heatmap_for_whole_programs 
        config.generate_heatmap_for_code_units = self.__args.generate_heatmap_for_code_units 
        config.generate_jsons = self.__args.generate_jsons
        config.generate_html_diffs = self.__args.generate_html_diffs
        config.n_processors = self.__args.n_processors
        config.minimal_similarity_threshold = self.__args.minimal_similarity_threshold
        config.maximal_similarity_threshold = self.__args.maximal_similarity_threshold
        return config
    
    def run(self) -> None:
        filepaths_sets = []
        if self.__args.paths:
            filepaths_sets = scan_for_files(self.__args.paths, self.__args.file_patterns)
            if not filepaths_sets:
                logging.error('No programs found, please ensure that you pass valid arguments for --path option')
                return
        else:
            self.parser.print_help()
            logging.error('Invalid arguments, please input valid one')
            return
        if -1 == self.__args.n_processors:
            self.__args.n_processors = multiprocessing.cpu_count() - 1
        self.__validate_paths__(filepaths_sets)

        programs_sets = read_programs_sets(filepaths_sets)

        ccode_filter_config = self.args_to_ccode_filtration_config()
        tokenization_start_time = time.process_time()
        tokenized_programs = CodeTokenizer(CCodeParser(CCodeFilter(ccode_filter_config)), n_processors=self.__args.n_processors).parse_programs(programs_sets)
        tokenization_end_time = time.process_time()

        detection_config = self.args_to_detection_config()
        detection_start_time = time.process_time()
        comparison_results = DetectionEngine().analyze(tokenized_programs, detection_config, self.__args.selected_programs_to_compare)
        detection_end_time = time.process_time()

        report_generation_config = self.args_to_report_generation_config()
        report_generator = ReportGenerator(comparison_results, report_generation_config, self.__args.output_path)
        report_generator.generate_reports()
        
        # with 

        print("Tokenization time ", tokenization_end_time - tokenization_start_time)
        print("Detection time ", detection_end_time - detection_start_time)
        

    def __validate_paths__(self, filepaths_sets: List[List[str]]):
        if len(filepaths_sets) <= 1:
            raise Exception("Invalid number of programs to analyze. Required at least 2 programs to be able to analyze them!")
        

    def __set_logging_level(self, args):
        if args.loglevel:
            logging.basicConfig(level=args.loglevel.upper())
            logging.info('Logging now setup.')
