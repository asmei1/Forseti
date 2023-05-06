import argparse
import logging
import multiprocessing
from pl.forseti.detection_config import DetectionConfig
from pl.forseti.c_code.ccode_filter import CCodeFilterConfig
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

def configure_arg_parser(parser):
    parser.add_argument(
        '-log',
        '--loglevel',
        default='warning',
        help=
        'Provide logging level. Example --loglevel debug, default=warning')

    processing_options = parser.add_argument_group('processing programs configuration')
    processing_options.add_argument('--n_processors', type=int, required=False, default=get_available_number_of_cores(),
                                    help="Number of processors used in programs tokenization. Value -1 means that all available processors will be used.")
    processing_options.add_argument('--filter_struct_declaration', type=str2bool, nargs='?', const=True, required=False, default=True,
                                    help="Defines, if tokens related structure declaration should be filtered.")
    processing_options.add_argument('--filter_function_declaration', type=str2bool, nargs='?', const=True, required=False, default=True,
                                    help="Defines, if structure declaration should be filtered.")
    processing_options.add_argument('--filter_aliasses', type=str2bool, nargs='?', const=True, required=False, default=True,
                                    help="Defines, if alias (typedef) should be filtered.")
    processing_options.add_argument('--filter_mixed_declarations', type=str2bool, nargs='?', const=True, required=False, default=True,
                                    help="""Defines, if cursors for mixing declarations with statments or expressions(DECL_STMT) should be filtered. 
                                    In most cases they should be, due to noise which are introduced in sequence.""")
    processing_options.add_argument('--filter_brackets', type=str2bool, nargs='?', const=True, required=False, default=True,
                                    help="Defines, if brackets from compund statments - {statment; stamtent;} should be filtered. In most cases yes, due to noise reduction.")
    processing_options.add_argument('--filter_parent_expression', type=str2bool, nargs='?', const=True, required=False, default=True,
                                    help="Defines, if parent expression should be filtered. Parent expression for example is int var = (x + y).")


    report_generation_options = parser.add_argument_group('report generation configuration')
    report_generation_options.add_argument('--generate_heatmap_for_whole_programs', type=str2bool, nargs='?', const=True, default=False, required=False)
    report_generation_options.add_argument('--generate_heatmap_for_code_units', type=str2bool, nargs='?', const=True, default=False, required=False)
    report_generation_options.add_argument('--generate_jsons', type=str2bool, nargs='?', const=True, default=True, required=False)
    report_generation_options.add_argument('--generate_html_diffs', type=str2bool, nargs='?', const=True, default=True, required=False)
    report_generation_options.add_argument('--generate_code_unit_metrics', type=str2bool, nargs='?', const=True, default=True, required=False)
    report_generation_options.add_argument('--output_path', type=str, required=True)
    report_generation_options.add_argument('--minimal_similarity_threshold', type=float, required=False, default=0.5)
    report_generation_options.add_argument('--maximal_similarity_threshold', type=float, required=False, default=1.0)
    

    algorithm_options = parser.add_argument_group('detection algorithm configuration')
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

def args_to_ccode_filtration_config(args):
    config = CCodeFilterConfig()
    config.filter_aliasses = args.filter_aliasses
    config.filter_brackets = args.filter_brackets
    config.filter_function_declaration = args.filter_function_declaration
    config.filter_mixed_declarations = args.filter_mixed_declarations
    config.filter_parent_expression = args.filter_parent_expression
    config.filter_struct_declaration = args.filter_struct_declaration
    return config

def args_to_detection_config(args):
    config = DetectionConfig()
    #TODO add rest
    config.n_processors = args.n_processors 
    config.minimal_search_length = args.minimal_search_length
    config.initial_search_length = args.initial_search_length
    config.distinguish_operators_symbols = args.distinguish_operators_symbols
    config.compare_function_names_in_function_calls = args.compare_function_names_in_function_calls
    config.unroll_ast = args.unroll_ast
    config.unroll_only_simple_functions = args.unroll_ast and args.unroll_only_simple_functions
    config.remove_unrolled_function = args.unroll_ast and args.remove_unrolled_function
    config.compare_whole_program = args.compare_whole_program
    config.max_number_of_differences_in_single_comparison_pair = args.max_number_of_differences_in_single_comparison_pair
    return config

def args_to_report_generation_config(args):
    config = ReportGenerationConfig()
    config.generate_heatmap_for_whole_programs = args.generate_heatmap_for_whole_programs 
    config.generate_heatmap_for_code_units = args.generate_heatmap_for_code_units 
    config.generate_jsons = args.generate_jsons
    config.generate_html_diffs = args.generate_html_diffs
    config.generate_code_unit_metrics = args.generate_code_unit_metrics
    config.n_processors = args.n_processors
    config.minimal_similarity_threshold = args.minimal_similarity_threshold
    config.maximal_similarity_threshold = args.maximal_similarity_threshold
    return config

def set_logging_level(args):
    if args.loglevel:
        logging.basicConfig(level=args.loglevel.upper())
        logging.info('Logging now setup.')
