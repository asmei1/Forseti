import os
import re
import copy
from ..tokenized_program import TokenizedProgram
from ..token import TokenKind
from jinja2 import Environment, FileSystemLoader


def __to_html_snippet__(format_data, path, code):
    snippet = copy.deepcopy(code)

    added = {}
    prev_locations = []
    start_token_regex = r"##__##start_(\d+_\d+)##__##"
    end_token_regex = r"##__##end_(\d+_\d+)##__##"

    for (comparison_index, index), location in format_data.items():
        for start_line, start_col, end_line, end_col, match_path in location:
            if path != match_path:
                continue
            start_token = f"##__##start_{comparison_index}_{index}##__##"
            end_token = f"##__##end_{comparison_index}_{index}##__##"
            for (prev_comparison_index, prev_index), p in prev_locations:
                if p[0] == end_line and p[1] <= end_col:
                    end_token = end_token + f"##__##end_{prev_comparison_index}_{prev_index}##__##" + f"##__##start_{prev_comparison_index}_{prev_index}##__##"

            prev_locations.append(((comparison_index, index), (start_line, start_col, end_line, end_col)))

            for line_index in [start_line, end_line]:
                offset = 0
                end_offset = 0
                if line_index not in added:
                    added[line_index] = []

                l = list(snippet[line_index])

                if line_index == start_line and line_index != end_line:
                    for addings in added[line_index]:
                        if addings[0] <= start_col:
                            offset += addings[1]
                    offset += start_col
                    added[line_index].append((start_col, len(start_token)))
                    l.insert(offset, start_token)
                elif line_index == end_line:
                    if line_index == start_line:
                        for addings in added[line_index]:
                            if addings[0] <= start_col:
                                offset += addings[1]
                        offset += start_col
                        l.insert(offset, start_token)
                    else:
                        start_col = 0

                    for addings in added[line_index]:
                        if addings[0] <= end_col:
                            end_offset += addings[1]
                    end_offset += end_col + 1
                    added[line_index].append((start_col, len(start_token)))
                    added[line_index].append((end_col - len(end_token), len(end_token)))
                    l.insert(end_offset if end_offset else len(l), end_token)

                snippet[line_index] = "".join(l)

                if start_line == end_line:
                    break

    remove_forbidden_tags = lambda x: x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    snippet = list(map(remove_forbidden_tags, snippet))
    snippet = "".join(snippet)

    snippet = re.sub(start_token_regex, '<span class="s_\\1 modified">', snippet)
    snippet = re.sub(end_token_regex, "</span>", snippet)
    return snippet


def __get_preformat_info(comparison_results, prefix, code_units):
    data = {}
    for comparison_index, (code_unit_names, comparison) in enumerate(comparison_results["code_unit_matches"].items()):
        for index, localization in enumerate(comparison["matches"]):
            for code_unit in code_units:
                if code_unit.ast[0].name == code_unit_names[prefix - 1] and len(code_unit.ast) >= 2:
                    first_token_index = localization["position_" + str(prefix)]
                    last_token_index = first_token_index + localization["length"] - 1

                    c_token = code_unit.ast[first_token_index]
                    n_token = code_unit.ast[first_token_index + 1]
                    data[(comparison_index, index)] = []
                    for i in range(first_token_index + 1, min(last_token_index, len(code_unit.ast) - 1)):
                        if (
                            abs(c_token.location.line - n_token.location.line) > localization["length"]
                            and "forseti_function_call_result"
                            not in [
                                c_token.name,
                                n_token.name,
                            ]
                        ) or c_token.location.path != n_token.location.path:
                            n_token = code_unit.ast[i - 1]

                            forward_token = n_token
                            for c in range(code_unit.ast.index(c_token) + 1, i):
                                if code_unit.ast[c].location.line > forward_token.location.line or (
                                    code_unit.ast[c].location.line == forward_token.location.line
                                    and code_unit.ast[c].location.column > forward_token.location.column
                                ):
                                    forward_token = code_unit.ast[c]

                            c_token_column = c_token.location.column
                            if c_token.token_kind == TokenKind.VariableDecl:
                                c_token_column -= 1 + len(c_token.type_name)
                            data[(comparison_index, index)].append(
                                (
                                    c_token.location.line - 1,
                                    c_token_column,
                                    forward_token.location.line - 1,
                                    len(forward_token.name) + forward_token.location.column,
                                    c_token.location.path,
                                )
                            )
                            c_token = code_unit.ast[i]
                        n_token = code_unit.ast[i + 1]

                    forward_token = n_token
                    for c in range(code_unit.ast.index(c_token) + 1, i):
                        if code_unit.ast[c].location.line > forward_token.location.line or (
                            code_unit.ast[c].location.line == forward_token.location.line and code_unit.ast[c].location.column > forward_token.location.column
                        ):
                            forward_token = code_unit.ast[c]

                    c_token_column = c_token.location.column
                    if c_token.token_kind == TokenKind.VariableDecl:
                        c_token_column -= 1 + len(c_token.type_name)
                    data[(comparison_index, index)].append(
                        (
                            c_token.location.line - 1,
                            c_token_column,
                            forward_token.location.line - 1,
                            len(forward_token.name) + forward_token.location.column,
                            c_token.location.path,
                        )
                    )
                    break

    return data


def __get_matches_list__(data, program_1, program_2):
    matches_list = []
    for comparison_index, (code_unit_names, match_data) in enumerate(data["code_unit_matches"].items()):
        single_match = {}

        single_match["code_unit_name_1"] = code_unit_names[0]
        single_match["code_unit_name_2"] = code_unit_names[1]
        single_match["similarity"] = match_data["similarity"]
        single_match["class"] = f"s_{comparison_index}"

        fragments = []
        for index, localization in enumerate(match_data["matches"]):
            fragment = {}

            fragment["start_line_1"] = (
                next(filter(lambda x: x.ast[0].name == code_unit_names[0], program_1.code_units)).ast[localization["position_1"]].location.line
            )
            fragment["start_line_2"] = (
                next(filter(lambda x: x.ast[0].name == code_unit_names[1], program_2.code_units)).ast[localization["position_2"]].location.line
            )
            fragment["length"] = localization["length"]
            fragment["class"] = f"s_{comparison_index}_{index}"

            fragments.append(fragment)
        single_match["fragments"] = fragments
        matches_list.append(single_match)

    return matches_list


def __get_files_content__(data, program_1, program_2):
    format_data = __get_preformat_info(data, 1, program_1.code_units)
    files_1 = []
    for path, code in zip(program_1.filenames, program_1.raw_codes):
        snippet = __to_html_snippet__(format_data, path, code)
        files_1.append({"path": path, "code": snippet})

    format_data = __get_preformat_info(data, 2, program_2.code_units)
    files_2 = []
    for path, code in zip(program_2.filenames, program_2.raw_codes):
        snippet = __to_html_snippet__(format_data, path, code)
        files_2.append({"path": path, "code": snippet})

    return files_1, files_2


def generate_html_diff_page(data, program_1: TokenizedProgram, program_2: TokenizedProgram):
    environment = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates/")))
    template = environment.get_template("report.html")
    files_1, files_2 = __get_files_content__(data, program_1, program_2)
    context = {
        "overall_similarity": data["similarity"],
        "overlap_1": data["overlap_1"][0],
        "overlap_2": data["overlap_2"][0],
        "matched_tokens": data["overlap_1"][1],
        "tokens_number_1": data["overlap_1"][2],
        "tokens_number_2": data["overlap_2"][2],
        "matches_list": __get_matches_list__(data, program_1, program_2),
        "files_1": files_1,
        "files_2": files_2,
    }
    return template.render(context)


def generate_summary_page(title, data):
    data = sorted(data, key=lambda x: x[2], reverse=True)
    similarity_list = []
    for authors, html_diff_path, similarity in data:
        similarity_list.append({"name_1": authors[0], "name_2": authors[1], "path": html_diff_path.replace("\\", "\\\\"), "value": similarity})

    environment = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates/")))
    template = environment.get_template("summary.html")
    return template.render({"title": title, "report_name": title, "similarity_list": similarity_list})
