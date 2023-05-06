from typing import Tuple
import argparse
from pl.forseti.c_code.ccode_parser import CCodeParser
from pl.forseti.c_code.ccode_filter import CCodeFilter
from pl.forseti.program import Program
from pl.forseti.code_tokenizer import CodeTokenizer
from pl.forseti.detection_engine import DetectionEngine
from pl.forseti.report_generation.report_generator import ReportGenerator
from pl.forseti.report_generation.html_diff_generator import generate_html_diff_page
from app.command_line_app_utils import *

    files_1 = {}
    files_2 = {}
    for f in data['filenames_1']:
        files_1[f] =  __load_file(f)
    for f in data['filenames_2']:
        files_2[f] =  __load_file(f)

# if this function will be used only in Dante, I suggest to set --minimal_similarity_threshold to 0.0
def run_detection(file_1: Tuple[str, str], file_2: Tuple[str, str], forseti_args=['--minimal_similarity_threshold', '0.0']):
    parser = argparse.ArgumentParser()
    configure_arg_parser(parser)
    if '--output_path' not in forseti_args:
        # This argument is necessary to use configuration from command line (I don't want to rewrite it again). 
        # --output_path is not used anywhere.
        forseti_args.append('--output_path')
        forseti_args.append('C:\\')

    programs_sets = [Program([file_1[0]], [file_1[1]], file_1[0]), Program([file_2[0]], [file_2[1]], file_2[0])]

    args = parser.parse_args(forseti_args if forseti_args else None)
    ccode_filter_config = args_to_ccode_filtration_config(args)
    tokenized_programs = CodeTokenizer(CCodeParser(CCodeFilter(ccode_filter_config)), n_processors=args.n_processors).parse_programs(programs_sets)

    detection_config = args_to_detection_config(args)
    comparison_results = DetectionEngine().analyze(tokenized_programs, detection_config, args.selected_programs_to_compare)
    files_1 = {}
    files_1[file_1[0]] = file_1[1]
    files_2 = {}
    files_2[file_2[0]] = file_2[1]
    report_generation_config = args_to_report_generation_config(args, files_1, files_2)
    report_generator = ReportGenerator(comparison_results, report_generation_config, args.output_path)

    comparison_results, metrics = report_generator.get_comparison_results()
    code_units_metrics = report_generator.generate_code_unit_metrics()

    return metrics, code_units_metrics, generate_html_diff_page(comparison_results[0][1])

    
if __name__ == '__main__':
    name_1 = "C:\\Projects\\Forseti\\test_data\\dante\\DZIAL5_small\\T_620\\T_620_ID_46332_PLAGIAT.c"
    file_1 = open(name_1, mode='r', encoding='latin-1')
    file_1_content = file_1.read()
    file_1.close()
    
    name_2 = "C:\\Projects\\Forseti\\test_data\\dante\\DZIAL5_small\\T_620\\T_620_ID_47372_PLAGIAT.c"
    file_2 = open(name_2, mode='r', encoding='latin-1')
    file_2_content = file_2.read()
    file_2.close()
    
    m, c, h = run_detection((name_1, file_1_content), (name_2, file_2_content))
    with open("C:\\Projects\\Forseti\\test_data\\dante\\DZIAL5_small\\d.html", 'w', encoding='utf8') as file:
        file.write(h)
            