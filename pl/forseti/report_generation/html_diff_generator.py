import re
import copy
from ..tokenized_program import TokenizedProgram


def __to_html_snippet(format_data, path, code):
    snippet = copy.deepcopy(code)

    added = {}
    for (comparison_index, index), locations in format_data.items():
        for start_line, start_col, end_line, end_col, match_path in locations:
            if path != match_path:
                continue
            for line_index in range(start_line, end_line + 1):
                start_token = f"##__##start_{comparison_index}_{index}##__##"
                end_token = "##__##end##__##"

                offset = 0
                end_offset = 0
                if line_index not in added:
                    added[line_index] = []

                if line_index == start_line and line_index != end_line:
                    for addings in added[line_index]:
                        if addings[0] <= start_col:
                            offset += addings[1]
                    offset += start_col
                    added[line_index].append((start_col, len(start_token)))
                elif line_index == end_line:
                    if line_index == start_line:
                        for addings in added[line_index]:
                            if addings[0] <= start_col:
                                offset += addings[1]
                        offset += start_col
                    else:
                        start_col = 0

                    for addings in added[line_index]:
                        if addings[0] <= end_col:
                            end_offset += addings[1]
                    end_offset += end_col + 1
                    added[line_index].append((start_col, len(start_token)))
                    added[line_index].append((end_col, len(end_token)))
                else:
                    # for addings in added[line_index]:
                    #     offset += addings[1]
                    added[line_index].append((0, len(start_token)))

                l = list(snippet[line_index])
                l.insert(offset, start_token)
                l.insert(end_offset if end_offset else len(l), end_token)
                snippet[line_index] = "".join(l)

    remove_forbidden_tags = lambda x: x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    snippet = list(map(remove_forbidden_tags, snippet))
    snippet = "".join([f"<code>{line}</code>" for line in snippet])
    start_token_regex = r"##__##start_(\d+_\d+)##__##"
    end_token_regex = r"##__##end##__##"
    snippet = re.sub(start_token_regex, '<span class="s_\\1 modified">', snippet)
    snippet = re.sub(end_token_regex, "</span>", snippet)
    return snippet


def __get_html_head__():
    return """        
    <head>
            <style>
                .diff { font-family: Courier; }
                .diff_header { background-color: #f8f8f8 }
                .empty_line { background-color: #cfc }
                .row {
                    display: flex;

                    flex-wrap: wrap;
                    padding: 10px;
                }
                .file_name{
                    font-size: 0.8em;
                }
                .row>* {
                    width: 100%;
                }

                .row>.left{
                    width: 20%;
                    padding: 1rem;
                    padding-left: 0px;
                    padding-top: 0px;
                }

                .row>.middle, .row>.right{
                    width: 34%;
                    padding-top: 0px;
                    padding: 1rem;
                }
                .row>.right, .row>.middle, .row>.left{
                    overflow-y: scroll;
                    max-height: 90vh;
                }
                .modified { background-color: #fdd }
                .highlighted { background-color: #faa }
                .row {
                    display: flex;
                }

                pre {
                }

                pre code {
                display: block;
                    counter-increment: line;
                }
                pre code:before {
                    
                    content: counter(line);
                    display: inline-block;
                    border-right: 1px solid #ddd;
                    padding: 0 .5em;
                    margin-right: .5em;
                    color: #888

                }
            </style>
        </head>"""


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
                        if abs(c_token.location.line - n_token.location.line) > localization["length"] and "forseti_function_call_result" not in [
                            c_token.name,
                            n_token.name,
                        ]:
                            n_token = code_unit.ast[i - 1]
                            data[(comparison_index, index)].append(
                                (
                                    c_token.location.line - 1,
                                    c_token.location.column - 1,
                                    n_token.location.line - 1,
                                    len(n_token.name) + n_token.location.column,
                                    c_token.location.path,
                                )
                            )
                            c_token = code_unit.ast[i]
                        n_token = code_unit.ast[i + 1]

                    data[(comparison_index, index)].append(
                        (
                            c_token.location.line - 1,
                            c_token.location.column - 1,
                            n_token.location.line - 1,
                            len(n_token.name) + n_token.location.column,
                            c_token.location.path,
                        )
                    )
                    break

    return data


def __get_html_body__(data, program_1: TokenizedProgram, program_2: TokenizedProgram):
    html = ""
    html += f"""
    <div class="row">
        <div class="left" id="similarity_list">
            <p>Overall similarity: {data['similarity']:.3f}</p>
            <p>Left program overlap: {data['overlap_1']:.3f}</p>
            <p>Right program overlap: {data['overlap_2']:.3f}</p>
            <ol>
                ###similarity_list###
            </ol>
        </div>
        <div class="middle diff" id="files_1">###1_files_1###</div>
        <div class="right diff" id="files_2">###2_files_2###</div>
    </div>
    """
    similarity_list_html = ""
    for comparison_index, (code_unit_names, match_data) in enumerate(data["code_unit_matches"].items()):
        name_token_1 = code_unit_names[0]
        name_token_2 = code_unit_names[1]
        similarity = match_data["similarity"]

        similarity_list_html += f"""
        <li class="s_{comparison_index}">
            <div style="font-family: Monospace;" class="s_{comparison_index}">
                {name_token_1}<br>
                {name_token_2}<br>
            </div>
        Fragment similarity: {similarity:.3f}<br>"""
        for index, localization in enumerate(match_data["matches"]):
            program_1_start_line = (
                next(filter(lambda x: x.ast[0].name == code_unit_names[0], program_1.code_units)).ast[localization["position_1"]].location.line
            )
            program_2_start_line = (
                next(filter(lambda x: x.ast[0].name == code_unit_names[1], program_2.code_units)).ast[localization["position_2"]].location.line
            )
            label = f"{program_1_start_line:>3}:{program_2_start_line:>3} | {localization['length']:>3}"
            similarity_list_html += f"""
                <span class="s_{comparison_index}_{index}">Localization: {label}</span><br>
            """

        similarity_list_html += "</li>"
    html = html.replace("###similarity_list###", similarity_list_html)

    files_page = ""
    file_index = 0
    format_data = __get_preformat_info(data, 1, program_1.code_units)
    for path, code in zip(program_1.filenames, program_1.raw_codes):
        path_label = f"""<div class="file_name">{path}</div>"""

        snippet = __to_html_snippet(format_data, path, code)

        content = f"""<div class="raw_code"><pre>{snippet}</pre></div>"""
        files_page += path_label + content
        file_index += 1

    html = html.replace("###1_files_1###", files_page)

    files_page = ""
    file_index = 0
    format_data = __get_preformat_info(data, 2, program_2.code_units)
    for path, code in zip(program_2.filenames, program_2.raw_codes):
        path_label = f"""<div class="file_name">{path}</div>"""

        snippet = __to_html_snippet(format_data, path, code)

        content = f"""<div class="raw_code"><pre>{snippet}</pre></div>"""
        files_page += path_label + content
        file_index += 1

    html = html.replace("###2_files_2###", files_page)

    return html


def __get_script_part__():
    return """
    
    function addScrollOnClick(item, panel2){
        item.addEventListener('click', ()=> {
            item.classList.forEach((item) => {
                if (item != "highlighted" && item != "modified" ){
                    
                    panel2.querySelector("span." + item).scrollIntoView({ behavior: 'auto', block: 'center', inline: 'center' });
                    panel2.scrollLeft = 0 
                
                }
            });
        });
    }
    function addListeners(panel_list, left_panel, right_panel) {
      // Add event listeners to each list item
      panel_list.querySelectorAll('div').forEach((list_item) => {
        list_item.addEventListener('mouseenter', () => {
            const itemClass = list_item.getAttribute('class');
            right_panel.querySelectorAll('[class^="'+itemClass +'_"]').forEach((item) => {
                item.classList.add('highlighted');
            });
            left_panel.querySelectorAll('[class^="'+itemClass +'_"]').forEach((item) => {
                item.classList.add('highlighted');
            });
            list_item.classList.add('highlighted');
        });
        list_item.addEventListener('mouseleave', () => {
            list_item.classList.remove('highlighted');
            const itemClass = list_item.getAttribute('class');
            right_panel.querySelectorAll('[class^="'+itemClass +'_"]').forEach((item) => {
                item.classList.remove('highlighted');
            });
            left_panel.querySelectorAll('[class^="'+itemClass +'_"]').forEach((item) => {
                item.classList.remove('highlighted');
            });
        });
      }); 


      panel_list.querySelectorAll('span').forEach((list_item) => {
        list_item.addEventListener('mouseenter', () => {
            // Get the id of the item
            const itemClass = list_item.getAttribute('class');
            // Highlight the corresponding items in the other panels
            panel_list.querySelectorAll("span." + itemClass).forEach((item) => {
                item.classList.add('highlighted');
            });
            right_panel.querySelectorAll("span." + itemClass).forEach((item) => {
                item.classList.add('highlighted');
            });
            left_panel.querySelectorAll("span." + itemClass).forEach((item) => {
                item.classList.add('highlighted');
            });
        });

        list_item.addEventListener('mouseleave', () => {
            panel_list.querySelectorAll("span").forEach((item) => {
                item.classList.remove('highlighted');
            });
            left_panel.querySelectorAll('span').forEach((item) => {
                item.classList.remove('highlighted');
            });
        
            right_panel.querySelectorAll('span').forEach((item) => {
                item.classList.remove('highlighted');
            });
        });
        
        addScrollOnClick(list_item, right_panel);
        addScrollOnClick(list_item, left_panel);
      });
    }
    function addListenersPanels(panel_list, panel1, panel2) {
      // Add event listeners to each list item
      panel1.querySelectorAll('span').forEach((item) => {
        item.addEventListener('mouseenter', () => {
            // Get the id of the item
            const itemClass = item.getAttribute('class').slice(0, -9);
            // Highlight the corresponding items in the other panels
            panel_list.querySelectorAll("span." + itemClass).forEach((item) => {
                item.classList.add('highlighted');
            });
            panel1.querySelectorAll("span." + itemClass).forEach((item) => {
                item.classList.add('highlighted');
            });
            panel2.querySelectorAll("span." + itemClass).forEach((item) => {
                item.classList.add('highlighted');
            });
        });

        item.addEventListener('mouseleave', () => {
            panel_list.querySelectorAll("span").forEach((item) => {
                item.classList.remove('highlighted');
            });
            panel1.querySelectorAll('span').forEach((item) => {
                item.classList.remove('highlighted');
            });
        
            panel2.querySelectorAll('span').forEach((item) => {
                item.classList.remove('highlighted');
            });
        });
        addScrollOnClick(item, panel2);
      });
    }
    
    const list = document.getElementById('similarity_list');
    const left_panel = document.getElementById('files_1');
    const right_panel = document.getElementById('files_2');
    
    addListeners(list, left_panel, right_panel);
    addListenersPanels(list, left_panel, right_panel);
    addListenersPanels(list, right_panel, left_panel);
    """


def generate_html_diff_page(data, program_1: TokenizedProgram, program_2: TokenizedProgram):
    # data = (similarity, overlap_1, overlap_2, code_unit_matches)
    html = ""
    html += f"""<html>{__get_html_head__()}"""
    html += f"""<body>{__get_html_body__(data, program_1, program_2)}</body>"""
    html += f"""<script>{__get_script_part__()}</script>"""
    html += """</html>"""

    return html


def generate_summary_page(title, data):
    html = """
<!DOCTYPE html>
<html>
  <head>
"""
    html += f"""
    <title>{title}</title>
"""
    html += """
  </head>
  <body>
    <style>
        body {
            font-family: Helvetica;
        }
        h1 {
            font-size: 50px;
            margin: 7% 0% 1% 0%;
        }
        h3 {
            font-size: 25px;
            margin: 0% 0% 7% 0%;
        }
        button {
            width: 70%;
            text-align: center;
            border: none;
            background-color: #E0E0E0;
            transition-duration: 0.4s;
        }
        button:hover {
            background-color: #F5F5F5;
        }
    </style>
    <body>
    <div style="justify-content: center; text-align: center;">
"""
    html += f"""
      <h1>{title}</h1>
      <h3>Report</h3>
      <div id="menu-div">
    """
    data = sorted(data, key=lambda x: x[2], reverse=True)
    for authors, html_diff_path, similarity in data:
        path = html_diff_path.replace("\\", "/")
        html += f"""
        <button style="padding:10px; margin-bottom: 5px;" onclick="window.location.href=&quot;{path}&quot;">
            <div style="display: inline-block;">{authors[0]}<br><br>{authors[1]}</div> 
            <div style="display: inline-block; padding-left: 150px;">{similarity}<br>&nbsp;</div> 
        </button>"""
    html += """
            </div>
          </div>
      </body>
</html>"""

    return html
