from typing import List
import logging
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from ..token import Token
from .report_generation_config import ReportGenerationConfig
from ..comparison_result import ComparisonResult
from ..utils.slugify import slugify
from .html_diff_generator import generate_html_diff_page, generate_summary_page
from .generate_heatmap import generate_heatmap
from ..utils.multiprocessing import execute_function_in_multiprocesses
from ..comparison_results_processor import ComparisonResultsProcessor


def key_to_json(data):
    if data is None or isinstance(data, (bool, int, str)):
        return data
    if isinstance(data, (tuple, frozenset)):
        return str(data)
    raise TypeError

def to_json(data):
    if data is None or isinstance(data, (bool, float, int, tuple, range, str, list)):
        return data
    if isinstance(data, (set, frozenset)):
        return sorted(data)
    if isinstance(data, dict):
        return {key_to_json(key): to_json(data[key]) for key in data}
    raise TypeError

class ReportGenerator:
    def __create_folders__(self):
        if (self.__report_generation_config.generate_heatmap_for_code_units \
            or self.__report_generation_config.generate_heatmap_for_whole_programs) \
                and not os.path.exists(self.__heatmaps_output_path):
            logging.debug("Creating folder: % ...", self.__heatmaps_output_path,)
            os.makedirs(self.__heatmaps_output_path)

        if (self.__report_generation_config.generate_jsons or self.__report_generation_config.generate_code_unit_metrics) \
            and not os.path.exists(self.__json_output_path):
            
            os.makedirs(self.__json_output_path)
            logging.debug("Creating folder: % ...", self.__json_output_path)

        if self.__report_generation_config.generate_html_diffs and not os.path.exists(self.__html_output_path):
            os.makedirs(self.__html_output_path) 
            logging.debug("Creating folder: % ...", self.__html_output_path)

        
    def __init__(self, comparison_results_processor: ComparisonResultsProcessor, report_generation_config: ReportGenerationConfig) -> None:
        self.__comparison_results_processor = comparison_results_processor
        self.__report_generation_config = report_generation_config

        if self.__report_generation_config.output_path:
            self.__heatmaps_output_path = os.path.abspath(os.path.join(self.__report_generation_config.output_path, "heatmaps"))
            self.__json_output_path = os.path.abspath(os.path.join(self.__report_generation_config.output_path, "jsons"))
            self.__html_output_path = os.path.abspath(os.path.join(self.__report_generation_config.output_path, "html"))
            self.__create_folders__()
        else:
            self.__heatmaps_output_path = None
            self.__json_output_path = None
            self.__html_output_path = None


    def generate_reports(self):
        if self.__report_generation_config.generate_heatmap_for_code_units:
            # self.dump_heatmap_per_compared_code_units()
            print("self.dump_heatmap_per_compared_code_units()")

        if self.__report_generation_config.generate_heatmap_for_whole_programs:
            # self.dump_heatmap_for_whole_programs()
            print("self.dump_heatmap_for_whole_programs()")

        if self.__report_generation_config.generate_html_diffs:
            similarity_report_data = []
            overlap1_report_data = []
            overlap2_report_data = []
            for authors, results in self.__comparison_results_processor.get_flat_filtered_processed_results().items():
                html_report_path = os.path.join(self.__html_output_path, slugify(authors[0] + " " + authors[1]) + ".html")
                similarity_report_data.append((authors, html_report_path, results["similarity"])) 
                overlap1_report_data.append((authors, html_report_path, results["overlap_1"])) 
                overlap2_report_data.append((authors, html_report_path, results["overlap_2"])) 
                
                with open(html_report_path, 'w', encoding='latin-1') as outfile:
                    outfile.write(generate_html_diff_page(results, self.__comparison_results_processor.get_tokenized_program(authors[0]), self.__comparison_results_processor.get_tokenized_program(authors[1])))
            
            with open(os.path.join(self.__html_output_path, "similarity.html"), 'w', encoding='latin-1') as outfile:
                outfile.write(generate_summary_page("Similarity", similarity_report_data))

            with open(os.path.join(self.__html_output_path, "overlap_1.html"), 'w', encoding='latin-1') as outfile:
                outfile.write(generate_summary_page("Overlap 1", overlap1_report_data))

            with open(os.path.join(self.__html_output_path, "overlap_2.html"), 'w', encoding='latin-1') as outfile:
                outfile.write(generate_summary_page("Overlap 2", overlap2_report_data))

        if self.__report_generation_config.generate_jsons:
            self.dump_comparison_results_in_json()

        if self.__report_generation_config.generate_code_unit_metrics:
            self.dump_code_unit_metrics()


    @staticmethod 
    def dump_comparison_result_in_json(data_pack):
        config, (name, data) = data_pack
        if type(name) is tuple:
            name = name[0] + " " + name[1]

        filename = slugify(name) + ".json"

        with open(os.path.join(config, filename), 'w', encoding='latin-1') as outfile:
            json.dump(to_json(data), outfile, indent=4)

    def dump_comparison_results_in_json(self):
        filtered_results = self.__comparison_results_processor.get_flat_filtered_processed_results()
        config = (self.__json_output_path)

        if self.__report_generation_config.n_processors == 1:
            for name, data_dict in filtered_results.items():
                ReportGenerator.dump_comparison_result_in_json((config, (name, data_dict)))
        else:
            execute_function_in_multiprocesses(ReportGenerator.dump_comparison_result_in_json, zip([config]*len(filtered_results), filtered_results), self.__report_generation_config.n_processors)

        summary, overlap_1, overlap_2 = self.__comparison_results_processor.get_summary()
        ReportGenerator.dump_comparison_result_in_json((config, ("summary", summary)))
        ReportGenerator.dump_comparison_result_in_json((config, ("overlap_1", overlap_1)))
        ReportGenerator.dump_comparison_result_in_json((config, ("overlap_2", overlap_2)))

    def dump_code_unit_metrics(self):
        config = (self.__json_output_path)
        code_unit_metrics = self.__comparison_results_processor.get_code_units_metrics()
        ReportGenerator.dump_comparison_result_in_json((config, ("code_unit_metrics", code_unit_metrics)))
    
 