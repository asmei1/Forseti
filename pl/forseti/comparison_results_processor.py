import logging
import dataclasses
import copy
import numpy as np


@dataclasses.dataclass
class ComparisonResultsProcessorConfig:
    assign_functions_based_on_types: bool = True
    minimal_similarity_threshold: float = 0.5
    maximal_similarity_threshold: float = 1.0


class ComparisonResultsProcessor:
    def __init__(self, raw_comparison_results, config: ComparisonResultsProcessorConfig) -> None:
        self.__raw_comparison_results = raw_comparison_results
        self.__config = config
        self.__similarity_threshold, self.__processed_results, self.__programs = self.__proces_comparison_results__(self.__raw_comparison_results)

    @property
    def similarity_treshold(self):
        return self.__similarity_threshold

    @property
    def processed_results(self):
        return self.__processed_results

    def get_filtered_processed_results(self):
        filtered = {}
        for program_a_author, results_to_a in self.__processed_results.items():
            temp = {}
            for program_b_author, results_b in results_to_a.items():
                if self.__similarity_threshold < results_b["similarity"]:
                    temp[program_b_author] = results_b

            if temp:
                filtered[program_a_author] = temp
        return filtered

    def get_flat_filtered_processed_results(self):
        filtered = {}
        for program_a_author, results_to_a in self.__processed_results.items():
            for program_b_author, results_b in results_to_a.items():
                key_a_to_b = (program_a_author, program_b_author)
                key_b_to_a = (program_b_author, program_a_author)

                if key_a_to_b in filtered or key_b_to_a in filtered:
                    continue
                if self.__similarity_threshold <= results_b["similarity"]:
                    filtered[key_a_to_b] = results_b

        return filtered

    def __format_data__(self, data):
        d = {}
        data.sort(key=lambda x: x[1], reverse=True)
        for k, v in data:
            d[k] = v
        return d

    def get_tokenized_program(self, author_name):
        return self.__programs[author_name]

    def get_summary(self):
        similarities = []
        program_1_overlap = []
        program_2_overlap = []
        authors_cache = []
        for program_a_author, results_to_a in self.__processed_results.items():
            for program_b_author, results_b in results_to_a.items():
                key_a_to_b = program_a_author + " " + program_b_author
                key_b_to_a = program_b_author + " " + program_a_author

                if key_a_to_b not in authors_cache and key_b_to_a not in authors_cache:
                    similarities.append((key_b_to_a, results_b["similarity"]))
                    program_1_overlap.append((key_a_to_b, results_b["overlap_1"]))
                    program_2_overlap.append((key_a_to_b, results_b["overlap_2"]))
                    authors_cache.append(key_a_to_b)
                    authors_cache.append(key_b_to_a)

        return (self.__format_data__(similarities), self.__format_data__(program_1_overlap), self.__format_data__(program_2_overlap))

    def get_code_units_metrics(self):
        metrics = {}
        for pair_names, comparison_results in self.get_flat_filtered_processed_results().items():
            for code_units_name, code_unit_compare_res in comparison_results["code_unit_matches"].items():
                if code_units_name not in metrics:
                    metrics[code_units_name] = {}
                if self.__similarity_threshold < code_unit_compare_res["similarity"]:
                    metrics[code_units_name][(pair_names[0], pair_names[1])] = code_unit_compare_res["similarity"]

        return metrics

    def __proces_comparison_results__(self, raw_comparison_results):
        programs = {}
        program_to_program = {}
        for elem in raw_comparison_results:
            pair = elem.pair

            if pair.program_a.author not in program_to_program:
                program_to_program[pair.program_a.author] = {}
                programs[pair.program_a.author] = pair.program_a
            if pair.program_b.author not in program_to_program:
                program_to_program[pair.program_b.author] = {}
                programs[pair.program_b.author] = pair.program_b

            stats_prototype = {}
            stats_prototype["similarity"] = 0.0
            stats_prototype["overlap_1"] = 0.0
            stats_prototype["overlap_2"] = 0.0
            stats_prototype["code_unit_matches"] = {}

            program_to_program[pair.program_a.author][pair.program_b.author] = copy.deepcopy(stats_prototype)
            program_to_program[pair.program_b.author][pair.program_a.author] = copy.deepcopy(stats_prototype)

        for comparison_result in raw_comparison_results:
            matches_a, matches_b, pair, raw_comparison_result = (
                comparison_result.matches_a,
                comparison_result.matches_b,
                comparison_result.pair,
                comparison_result.result,
            )
            a_to_b_data = {}
            a_to_b_data["similarity"] = 0.0
            a_to_b_data["overlap_1"] = 0.0
            a_to_b_data["overlap_2"] = 0.0
            a_to_b_data["temp_matches_1"] = np.sum(matches_a)
            a_to_b_data["temp_matches_2"] = np.sum(matches_b)
            a_to_b_data["matches"] = []
            if raw_comparison_result:
                for raw_code_unit_entry in raw_comparison_result:
                    a_to_b_data["matches"].append(
                        {
                            "position_1": raw_code_unit_entry["position_of_token_1"],
                            "position_2": raw_code_unit_entry["position_of_token_2"],
                            "length": raw_code_unit_entry["length"],
                        }
                    )
                    a_to_b_data["similarity"] += 2 * raw_code_unit_entry["length"]

            a_to_b_data["overlap_1"] = np.sum(matches_a) / len(matches_a)
            a_to_b_data["overlap_2"] = np.sum(matches_b) / len(matches_b)

            b_to_a_data = {}
            b_to_a_data["similarity"] = a_to_b_data["similarity"]
            b_to_a_data["temp_matches_1"] = np.sum(matches_b)
            b_to_a_data["temp_matches_2"] = np.sum(matches_a)
            b_to_a_data["matches"] = []

            if raw_comparison_result:
                for raw_code_unit_entry in raw_comparison_result:
                    b_to_a_data["matches"].append(
                        {
                            "position_1": raw_code_unit_entry["position_of_token_2"],
                            "position_2": raw_code_unit_entry["position_of_token_1"],
                            "length": raw_code_unit_entry["length"],
                        }
                    )

            b_to_a_data["overlap_1"] = np.sum(matches_b) / len(matches_b)
            b_to_a_data["overlap_2"] = np.sum(matches_a) / len(matches_a)

            a_to_b_data["similarity"] = a_to_b_data["similarity"] / (len(matches_a) + len(matches_b))
            b_to_a_data["similarity"] = b_to_a_data["similarity"] / (len(matches_a) + len(matches_b))

            a_to_b_key = (pair.tokens_a[0].name, pair.tokens_b[0].name)
            program_to_program[pair.program_a.author][pair.program_b.author]["code_unit_matches"][a_to_b_key] = a_to_b_data
            b_to_a_key = (pair.tokens_b[0].name, pair.tokens_a[0].name)
            program_to_program[pair.program_b.author][pair.program_a.author]["code_unit_matches"][b_to_a_key] = b_to_a_data

        similarities = []
        for compared_to_name, compared_to in program_to_program.items():
            for compared_program_name, compared_program in compared_to.items():
                similarity = 0.0
                overlap_1 = 0.0
                overlap_2 = 0.0
                number_of_comparisons = 0

                for _, matches in compared_program["code_unit_matches"].items():
                    similarity += matches["similarity"]
                    overlap_1 += matches["temp_matches_1"]
                    overlap_2 += matches["temp_matches_2"]
                    del matches["temp_matches_1"]
                    del matches["temp_matches_2"]
                    number_of_comparisons += similarity > 0.0 or self.__config.assign_functions_based_on_types

                compared_program["similarity"] = similarity / number_of_comparisons if number_of_comparisons != 0 else 0.0
                compared_program["overlap_1"] = (
                    overlap_1 / np.sum([len(ast.ast) for ast in programs[compared_to_name].code_units])
                    if self.__config.assign_functions_based_on_types
                    else number_of_comparisons
                )
                compared_program["overlap_2"] = (
                    overlap_2 / np.sum([len(ast.ast) for ast in programs[compared_program_name].code_units])
                    if self.__config.assign_functions_based_on_types
                    else number_of_comparisons
                )
                similarities.append(compared_program["similarity"])

        if len(similarities):
            sd = np.std(np.array(similarities), axis=0)
            similarity_threshold = min((min(similarities) + self.__config.minimal_similarity_threshold + sd * 2), self.__config.maximal_similarity_threshold)
        else:
            similarity_threshold = 0.0

        logging.info(f"Minimal similarity threshold: {self.__config.minimal_similarity_threshold}")
        logging.info(f"Similarity threshold: {similarity_threshold}")
        return (similarity_threshold, program_to_program, programs)
