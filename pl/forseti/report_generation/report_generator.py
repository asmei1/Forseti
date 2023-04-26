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
from .html_diff_generator import generate_html_diff_page
from .generate_heatmap import generate_heatmap
from ..utils.multiprocessing import execute_function_in_multiprocesses


class ReportGenerator:
    @staticmethod
    def get_length_data(matches):
        if not matches:
            return [0.0]
        return [r['length'] for r in matches]
    
    def __generate_data_frame_for_whole_programs__(self, comparison_results: List[ComparisonResult]) -> pd.DataFrame:

        grouped_results = {}
        for result in comparison_results:
            key = (result.pair.program_a.author, result.pair.program_b.author) 
            if key not in grouped_results:
                grouped_results[key] = []
            if result.result:
                for m in result.result:
                    grouped_results[key].append((m['length'], len(result.pair.tokens_a), len(result.pair.tokens_b)))        

        
        index = set()
        for (program_a, program_b), _ in grouped_results.items():
            index.add(program_a)
            index.add(program_b)

        index = sorted(list(index))
        results = np.eye(len(index))
        for (program_a, program_b), matches in grouped_results.items():
            if matches:
                # similarity = np.sum([(2*length / (len_a + len_b)) for length, len_a, len_b in matches]) / len(matches)
                similarity = np.sum([(2*length / (len_a + len_b)) for length, len_a, len_b in matches]) 
                row = index.index(program_a)
                col = index.index(program_b)
                results[row, col] = similarity
                results[col, row] = similarity
        
        df = pd.DataFrame(results, index, index)
        return df
    
    def __generate_data_frames_for_tokens__(self, comparison_results: List[ComparisonResult]) -> List[pd.DataFrame]:
        dfs: List[pd.DataFrame] = []

        grouped_results = {}
        for result in comparison_results:
            token_name = result.pair.tokens_a[0].name
            if token_name not in grouped_results:
                grouped_results[token_name] = {}
            
            key = (result.pair.program_a.author, result.pair.program_b.author) 
            if result.result:
                grouped_results[token_name][key] = []
                for m in result.result:
                    grouped_results[token_name][key].append((m['length'], len(result.pair.tokens_a), len(result.pair.tokens_b)))  
        
        dfs: List[pd.DataFrame] = []
        token_names: List[str] = []
        for token_name, programs_and_results in grouped_results.items():
            index = set()
            for (program_a, program_b), _ in programs_and_results.items():
                index.add(program_a)
                index.add(program_b)

            index = sorted(list(index))

            results = np.eye(len(index))
            for (program_a, program_b), matches in programs_and_results.items():
                if matches:
                    # similarity = np.sum([(2*length / (len_a + len_b)) for length, len_a, len_b in matches]) / len(matches)
                    # similarity = (2*matches[0][0] / (matches[0][1] + matches[0][2])) 
                    similarity = np.sum([(2*length / (len_a + len_b)) for length, len_a, len_b in matches]) 
                    row = index.index(program_a)
                    col = index.index(program_b)
                    results[row, col] = similarity
                    results[col, row] = similarity

            dfs.append(pd.DataFrame(results, index, index))
            token_names.append(token_name)
        return (dfs, token_names)

    def __proces_comparison_results__(self):
        grouped_results = {}
        for result in self.__comparison_results:
            key = (result.pair.program_a.author, result.pair.program_b.author) 
            if key not in grouped_results and result.result:
                grouped_results[key] = {}
                grouped_results[key]['code_units'] = []
                grouped_results[key]['similarity'] = 0.0
                grouped_results[key]['length'] = 0
            if result.result:
                r = {}
                r['raw'] = result
                r['similarity'] = 0.0
                r['length'] = 0
                grouped_results[key]['code_units'].append(r)
        
        similarities = []
        longest_sequences = []
        for _, results in grouped_results.items():
            similarity = 0.0
            longest_sequence = 0
            for result in results['code_units']:
                raw = result['raw']
                aa = np.sum(raw.matches_a)
                bb = np.sum(raw.matches_b)
                code_unit_similarity = (aa + bb) / (len(raw.matches_a) + len(raw.matches_b))
                similarity += code_unit_similarity
                result['similarity'] = code_unit_similarity
                current_longest_match = max(raw.result, key=lambda x: x['length'])['length']
                result['length'] = current_longest_match
                longest_sequence = max([longest_sequence, current_longest_match])
            

            similarity = similarity / len(results['code_units'])
            similarities.append(similarity)
            longest_sequences.append(longest_sequence)
            
            results['similarity'] = similarity
            results['length'] = longest_sequence
        
        sd = np.std(np.array(similarities), axis=0)
        similarity_threshold = min((min(similarities) + self.__report_generation_config.minimal_similarity_threshold + sd * 2), self.__report_generation_config.maximal_similarity_threshold)
        longest_sequence_threshold = np.mean(np.array(longest_sequences)) + 2 * np.std(np.array(longest_sequences)) 
 
        comparisons_number = len(grouped_results)
        comparisons_number_after_filtration = 0
        for key, results in grouped_results.items():
            if results['similarity'] >= similarity_threshold:
                comparisons_number_after_filtration += 1

        logging.info(f"Minimal similarity threshold: {self.__report_generation_config.minimal_similarity_threshold}" )
        logging.info(f"Similarity threshold: {similarity_threshold}" )
        logging.info(f"Highest similarity: {max(similarities)}" )
        logging.info(f"Sequence length threshold: {longest_sequence_threshold}")
        logging.info(f"Max sequence length: {max(longest_sequences)}" )
        logging.info(f"Suspected comparisons: {comparisons_number}/{comparisons_number_after_filtration}" )

        return (similarity_threshold, longest_sequence_threshold, grouped_results)

    def __create_folders__(self):

        if (self.__report_generation_config.generate_heatmap_for_code_units \
            or self.__report_generation_config.generate_heatmap_for_whole_programs) \
                and not os.path.exists(self.__heatmaps_output_path):
            os.makedirs(self.__heatmaps_output_path)

        if self.__report_generation_config.generate_jsons and not os.path.exists(self.__json_output_path):
            os.makedirs(self.__json_output_path)

        if self.__report_generation_config.generate_html_diffs and not os.path.exists(self.__html_output_path):
            os.makedirs(self.__html_output_path) 

        
    def __init__(self, comparison_results: List[ComparisonResult], report_generation_config: ReportGenerationConfig, output_path) -> None:
        self.__comparison_results = comparison_results
        self.__report_generation_config = report_generation_config
        #TODO: name should be changed
        self.__heatmaps_output_path = os.path.join(output_path, "heatmaps")
        self.__json_output_path = os.path.join(output_path, "jsons")
        self.__html_output_path = os.path.join(output_path, "html")
        self.__similarity_threshold, self.__sequence_length_threshold, self.__preprocessed_comparison_results = self.__proces_comparison_results__()
        self.__create_folders__()



    def dump_heatmap_for_whole_programs(self):
        whole_program_df = self.__generate_data_frame_for_whole_programs__(self.__comparison_results)
        figure = generate_heatmap(whole_program_df, "Whole programs heatmap")
        figure.savefig(os.path.join(self.__heatmaps_output_path, "whole_programs_similarity_heatmap.jpg"))
        plt.close(figure)

    def dump_heatmap_per_compared_code_units(self):
        dfs_per_tokens, parsed_token_names = self.__generate_data_frames_for_tokens__(self.__comparison_results)
        for df, token_name in zip(dfs_per_tokens, parsed_token_names):
            figure = generate_heatmap(df, token_name + " heatmap")
            figure.savefig(os.path.join(self.__heatmaps_output_path, slugify(token_name) + ".jpg"))
            plt.close(figure)


    def __get_code_unit_info__(self, tokens: List[Token]) -> str:
        code_unit_info = {}    
        code_unit_info["first_token_name"] = tokens[0].name
        code_unit_info["length"] = len(tokens)
        return code_unit_info

    def get_comparison_results(self) -> None:
        results = []
        raw_overalls = []
        for _, comparison_result in self.__preprocessed_comparison_results.items():
            overall_similarity = comparison_result['similarity']
            if overall_similarity < self.__similarity_threshold:
                continue

            data_dump = {}
            code_units = comparison_result['code_units']
            pair = code_units[0]['raw'].pair

            name = slugify(pair.program_a.author) + "__" + slugify(pair.program_b.author)
            data_dump["author_1"] = pair.program_a.author
            data_dump["author_2"] = pair.program_b.author
            data_dump["filenames_1"] = pair.program_a.filenames
            data_dump["filenames_2"] = pair.program_b.filenames

            data_dump["overall_similarity"] = comparison_result['similarity']
            data_dump["longest_sequence"] = comparison_result['length']
            data_dump["raw_comparison_results"] = []
            for code_unit in code_units:
                pair = code_unit['raw'].pair
                data = {}
                data["code_unit_1"] = self.__get_code_unit_info__(pair.tokens_a)
                data["code_unit_2"] = self.__get_code_unit_info__(pair.tokens_b)
                data["localization"] = code_unit['raw'].result
                data["similarity"] = code_unit['similarity']
                data_dump["raw_comparison_results"].append(data)

            raw_overalls.append((name, data_dump["overall_similarity"]))
            results.append((name, data_dump))

        overalls = {}
        raw_overalls.sort(key=lambda x: x[1], reverse=True)
        for name, raw in raw_overalls:
            overalls[name] = raw
        results.append(('similarity', overalls))
        return results             
             
    @staticmethod 
    def dump_comparison_result_in_json(data_pack):
        config, (name, data) = data_pack
        if name == 'overall':
            with open(os.path.join(config[0], name + ".json"), 'w') as outfile:
                json.dump(data, outfile, indent=4)
    
    @staticmethod 
    def dump_comparison_result_in_json_and_html_diff(data_pack):
        config, (name, data) = data_pack
        # if True:
        json_output_path, html_output_path = config
        path_to_json = os.path.abspath(os.path.join(json_output_path, name + ".json"))
        path_to_html_diff = os.path.abspath(os.path.join(html_output_path, name + ".html"))
        with open(path_to_json, 'w') as outfile:
            json.dump(data, outfile, indent=4)
        if name != 'similarity':
            generate_html_diff_page(path_to_json, path_to_html_diff)

    def dump_comparison_results_in_json(self):
        results = self.get_comparison_results()
        config = (self.__json_output_path)
        if self.__report_generation_config.n_processors == 1:
            for name, data_dict in results:
                ReportGenerator.dump_comparison_result_in_json((config, (name, data_dict)))
        else:
            execute_function_in_multiprocesses(ReportGenerator.dump_comparison_result_in_json, zip([config]*len(results), results), self.__report_generation_config.n_processors)
    
    def dump_comparison_results_in_json_with_html_diffs(self):
        results = self.get_comparison_results()
        config = (self.__json_output_path, self.__html_output_path)
        if self.__report_generation_config.n_processors == 1:
            for name, data_dict in results:
                ReportGenerator.dump_comparison_result_in_json_and_html_diff((config, (name, data_dict)))
        else:
            execute_function_in_multiprocesses(ReportGenerator.dump_comparison_result_in_json_and_html_diff, list(zip([config]*len(results), results)), self.__report_generation_config.n_processors)
    
    def generate_reports(self):

        if self.__report_generation_config.generate_heatmap_for_code_units:
            self.dump_heatmap_per_compared_code_units()

        if self.__report_generation_config.generate_heatmap_for_whole_programs:
            self.dump_heatmap_for_whole_programs()

        if self.__report_generation_config.generate_html_diffs:
            self.dump_comparison_results_in_json_with_html_diffs()
        elif self.__report_generation_config.generate_jsons:
            self.dump_comparison_results_in_json()

        
