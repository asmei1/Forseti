from typing import List
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .token import Token
from .comparison_result import ComparisonResult
from .utils.slugify import slugify

import math


class ReportGenerator:
    def __generate_data_frame_for_whole_programs__(self, comparison_results: List[ComparisonResult]) -> pd.DataFrame:

        grouped_results = {}
        for result in comparison_results:
            key = (result.submission.program_a.author, result.submission.program_b.author) 
            if key not in grouped_results:
                grouped_results[key] = []
            grouped_results[key].append((result.result[0]['length'] if result.result else 0.0, len(result.submission.tokens_a), len(result.submission.tokens_b)))            

        
        index = set()
        for (program_a, program_b), _ in grouped_results.items():
            index.add(program_a)
            index.add(program_b)

        index = list(index)
        results = np.eye(len(index))
        for (program_a, program_b), matches in grouped_results.items():
            if matches:
                similarity = np.sum([(2*length / (len_a + len_b)) for length, len_a, len_b in matches]) / len(matches)
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
            token_name = result.submission.tokens_a[0].name
            if token_name not in grouped_results:
                grouped_results[token_name] = {}
            
            key = (result.submission.program_a.author, result.submission.program_b.author) 
            grouped_results[token_name][key] = (result.result[0]['length'] if result.result else 0.0, len(result.submission.tokens_a), len(result.submission.tokens_b))
        
        dfs: List[pd.DataFrame] = []
        token_names: List[str] = []
        for token_name, programs_and_results in grouped_results.items():
            index = set()
            for (program_a, program_b), _ in programs_and_results.items():
                index.add(program_a)
                index.add(program_b)

            index = list(index)

            results = np.eye(len(index))
            for (program_a, program_b), match in programs_and_results.items():
                if match:
                    length, len_a, len_b = match
                    similarity = 2 * length / (len_a + len_b)
                    row = index.index(program_a)
                    col = index.index(program_b)
                    results[row, col] = similarity
                    results[col, row] = similarity

            dfs.append(pd.DataFrame(results, index, index))
            token_names.append(token_name)
        return (dfs, token_names)


    def __init__(self, comparison_results: List[ComparisonResult], output_path) -> None:
        self.__comparison_results = comparison_results
        self.__whole_program_df = self.__generate_data_frame_for_whole_programs__(comparison_results)

        #TODO: name should be changed
        self.__dfs_per_tokens, self.__parsed_token_names = self.__generate_data_frames_for_tokens__(comparison_results)
        self.__output_path = output_path

        if not os.path.exists(self.__output_path):
            os.makedirs(self.__output_path)

    def __generate_heatmap__(self, df: pd.DataFrame, title: str):
        plot_width, plot_height = plt.rcParams['figure.figsize']

        # Turn interactive plotting off
        plt.ioff()
        mask = np.triu(np.ones_like(df.values, dtype=bool))
        
        heatmap = sns.heatmap(df, annot=True, mask=mask, xticklabels=True, yticklabels=True)
        figure = heatmap.get_figure()
        scale_factor = df.values.shape[0] / 4
        figure.set_size_inches(plot_width * scale_factor, plot_height * scale_factor)
        figure.suptitle(title, fontsize=20)
        figure.tight_layout()
        return figure

    def generate_heatmap_for_whole_programs(self):
        figure = self.__generate_heatmap__(self.__whole_program_df, "Whole programs heatmap")
        figure.savefig(os.path.join(self.__output_path, "whole_programs_similarity_heatmap.jpg"))
        plt.close(figure)

    def generate_heatmaps(self):
        for df, token_name in zip(self.__dfs_per_tokens, self.__parsed_token_names):
            figure = self.__generate_heatmap__(df, token_name + " heatmap")
            figure.savefig(os.path.join(self.__output_path, slugify(token_name) + ".jpg"))
            plt.close(figure)


    def __get_code_unit_info__(self, tokens: List[Token]) -> str:
        code_unit_info = {}    
        code_unit_info["first_token_name"] = tokens[0].name
        code_unit_info["first_token_location"] = tokens[0].location
        code_unit_info["length"] = len(tokens)
        return code_unit_info

    def get_comparison_result_in_json(self) -> None:
        jsons: List[str] = []
        for comparison_result in self.__comparison_results:
            data_dump = {}
            if comparison_result.result:
                data_dump["author_1"] = comparison_result.submission.program_a.author
                data_dump["author_2"] = comparison_result.submission.program_b.author
                data_dump["filenames_1"] = comparison_result.submission.program_a.filenames
                data_dump["filenames_2"] = comparison_result.submission.program_b.filenames

                data_dump["code_unit_1"] = self.__get_code_unit_info__(comparison_result.submission.tokens_a)
                data_dump["code_unit_2"] = self.__get_code_unit_info__(comparison_result.submission.tokens_b)

                data_dump["raw_results"] = comparison_result.result
                jsons.append(json.dumps(data_dump, indent=4))
        return jsons                            