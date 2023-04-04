from typing import List
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .token import Token
from .comparison_result import ComparisonResult
# from .tokenized_program import TokenizedProgram
import unicodedata
import re

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')
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
        # remove common part of author's names
        commonprefix = os.path.commonprefix(index)
        index = [x[len(commonprefix):] for x in index]

        results = np.eye(len(index))
        for (program_a, program_b), matches in grouped_results.items():
            if matches:
                similarity = np.sum([(2*length / (len_a + len_b)) for length, len_a, len_b in matches]) / len(matches)
                row = index.index(program_a[len(commonprefix):])
                col = index.index(program_b[len(commonprefix):])
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
            # remove common part of author's names
            commonprefix = os.path.commonprefix(index)
            index = [x[len(commonprefix):] for x in index]

            results = np.eye(len(index))
            for (program_a, program_b), match in programs_and_results.items():
                if match:
                    length, len_a, len_b = match
                    similarity = 2 * length / (len_a + len_b)
                    row = index.index(program_a[len(commonprefix):])
                    col = index.index(program_b[len(commonprefix):])
                    results[row, col] = similarity
                    results[col, row] = similarity
            dfs.append(pd.DataFrame(results, index, index))
            token_names.append(token_name)
        return (dfs, token_names)

        # index = set()
        # for (program_a, program_b), _ in grouped_results.items():
        #     index.add(program_a)
        #     index.add(program_b)

        # index = list(index)
        # # remove common part of author's names
        # commonprefix = os.path.commonprefix(index)
        # index = [x[len(commonprefix):] for x in index]

        # results = np.eye(len(index))
        # for (program_a, program_b), matches in grouped_results.items():
        #     if matches:
        #         similarity = np.sum([(2*length / (len_a + len_b)) for length, len_a, len_b in matches]) / len(matches)
        #         row = index.index(program_a[len(commonprefix):])
        #         col = index.index(program_b[len(commonprefix):])
        #         results[row, col] = similarity
        #         results[col, row] = similarity
        
        # df = pd.DataFrame(results, index, index)

        # return dfs

    def __init__(self, comparison_results: List[ComparisonResult], output_path) -> None:
        self.__comparison_results = comparison_results
        self.__whole_program_df = self.__generate_data_frame_for_whole_programs__(comparison_results)
        #TODO: name should be changed
        self.__dfs_per_tokens, self.__parsed_token_names = self.__generate_data_frames_for_tokens__(comparison_results)
        self.__output_path = output_path

        if not os.path.exists(self.__output_path):
            os.makedirs(self.__output_path)

    def generate_heatmap_for_whole_programs(self):
        mask = np.triu(np.ones_like(self.__whole_program_df.values, dtype=bool))

        heatmap = sns.heatmap(self.__whole_program_df, annot=True, mask=mask)
        figure = heatmap.get_figure()
        figure.suptitle("Whole programs heatmap")
        figure.savefig(os.path.join(self.__output_path, "whole_programs_similarity_heatmap.jpg"))
        plt.close(figure)

    def generate_heatmaps(self, for_the_same_tokens: bool = True):
        for df, token_name in zip(self.__dfs_per_tokens, self.__parsed_token_names):
            mask = np.triu(np.ones_like(df.values, dtype=bool))

            heatmap = sns.heatmap(df, annot=True, mask=mask)
            # ax.set_title(token_name + " heatmap")
            figure = heatmap.get_figure()
            figure.suptitle(token_name + " heatmap")
            figure.savefig(os.path.join(self.__output_path, slugify(token_name) + ".jpg"))
            plt.close(figure)
        

#     @staticmethod
#     def generate_json_reports(submissions: List[Submission]):
#         tokenized_programs_submissions = {}

#         for submission_a in submissions:
#             for submission_b in submissions:
#                 if submission_a != submission_b:
#                     continue

#                 if submission_a.program_a == submission_b.program_a \
#                 or submission_a.program_b == submission_b.program_b \
#                 or submission_a.program_a == submission_b.program_b:
                    
#                     if submission_a in tokenized_programs_submissions:
#                         tokenized_programs_submissions[submission_b] = submission_a

def get_code_unit_info(tokens: List[Token]) -> str:
    code_unit_info = {}    
    code_unit_info["first_token_name"] = tokens[0].name
    code_unit_info["first_token_location"] = tokens[0].location
    code_unit_info["length"] = len(tokens)
    return code_unit_info

def write_comparison_result(comparison_results:List[ComparisonResult]) -> None:
    for comparison_result in comparison_results:
        data_dump = {}
        if comparison_result.result:
            data_dump["author_1"] = comparison_result.submission.program_a.author
            data_dump["author_2"] = comparison_result.submission.program_b.author
            data_dump["filenames_1"] = comparison_result.submission.program_a.filenames
            data_dump["filenames_2"] = comparison_result.submission.program_b.filenames

            data_dump["code_unit_1"] = get_code_unit_info(comparison_result.submission.tokens_a)
            data_dump["code_unit_2"] = get_code_unit_info(comparison_result.submission.tokens_b)

            data_dump["raw_results"] = comparison_result.result
            json_string = json.dumps(data_dump, indent=4)
            print(json_string)
                        