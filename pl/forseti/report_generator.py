from typing import List
import json
from .token import Token
from .comparison_result import ComparisonResult
# from .tokenized_program import TokenizedProgram

# class ReportGenerator:

#     @staticmethod
#     def generate_heatmap(submissions: List[Submission], for_the_same_tokens: bool = True):
#         matrix = []
#         same_tokens = {}
#         for submission_a in submissions:
#             for submission_b in submissions:
#                 if submission_a != submission_b:
#                     continue

#                 # if for_the_same_tokens:
#                 #     if submission_a.tokens_a[0].name == submission_b.tokens_a[0].name

#         return matrix
        

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

            data_dump["results"] = comparison_result.result
            json_string = json.dumps(data_dump, indent=4)
            print(json_string)
                        