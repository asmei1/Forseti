import json
from bs4 import BeautifulSoup
import re

def __load_file(filename):
    with open(filename, 'r', encoding='latin-1') as file:
        return file.readlines()

def __to_html_snippet(format_data, prefix, file_index, code):    
    snippet = code

    added = {}
    for (comparison_index, index), (start_line, start_col, end_line, end_col) in format_data.items():
        for line_index in range(start_line, end_line + 1):
            span_class = f"""{comparison_index}_{index}"""
            start_token = f'_________start_{span_class}_________'
            end_token = '_________end_________'
            number_of_added_chars = len(start_token) + len(end_token)

            offset = 0
            end_offset = -1
            if line_index not in added:
                added[line_index] = []

            if line_index == start_line:
                for addings in added[line_index]:
                    if addings[0] <= start_col:
                        offset += addings[1] 
                offset += start_col
                added[line_index].append((start_col, number_of_added_chars))
            elif line_index == end_line:
                end_offset = end_col
                added[line_index].append((end_col, number_of_added_chars))
            else:
                for addings in added[line_index]:
                    offset += addings[1] 
                added[line_index].append((0, number_of_added_chars))
            
            l = list(code[line_index])
            l.insert(offset, start_token)
            l.insert(end_offset, end_token)
            code[line_index] = ''.join(l)
    
    remove_forbidden_tags = lambda x: x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    snippet = list(map(remove_forbidden_tags, snippet))
    snippet = "".join([f"<code>{line}</code>" for line in snippet])
    snippet = re.sub('_________start_(\d+_\d+)_________', '<span class="s_\\1 modified">', snippet)
    snippet = re.sub('_________end_________', '</span>', snippet)
    return snippet

def __get_html_head__():
    return '''        
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
        </head>'''

def __get_preformat_info(comparison_results, prefix, filename):
    data = {}
    prefix = str(prefix)
    for comparison_index, comparison in enumerate(comparison_results):
        for index, localization in enumerate(comparison['localization']):
            if localization['start_token_' + prefix]['path'] != filename:
                continue

            start_line = localization['start_token_' + prefix]['line'] - 1
            start_col = localization['start_token_' + prefix]['column'] - 1
            end_line = localization['end_token_' + prefix]['line'] - 1
            end_col = localization['end_token_' + prefix]['column'] + 1
            data[(comparison_index, index)] = (start_line, start_col, end_line, end_col)

    return data
            
    
def __get_html_body__(comparison_results, files_1, files_2):
    html = ""
    html += '''
    <div class="row">
        <div class="left" id="similarity_list"><ol>_________similarity_list_________</ol></div>
        <div class="middle diff" id="files_1">_________1_files_1_________</div>
        <div class="right diff" id="files_2">_________2_files_2_________</div>
    </div>
    '''
    similarity_list_html = ""
    for comparison_index, comparison in enumerate(comparison_results):
        name_token_1 = comparison['code_unit_1']['first_token_name']
        name_token_2 = comparison['code_unit_2']['first_token_name']
        for index, localization in enumerate(comparison['localization']):
            start_1 = localization['start_token_1']['line'] 
            end_1 = localization['end_token_1']['line']  
            start_2 = localization['start_token_2']['line'] 
            end_2 = localization['end_token_2']['line'] 
            length = localization['length'] 


            label = f"{start_1:>3}:{end_1:>3} | {start_2:>3}:{end_2:>3} | {length}"
            
            similarity_list_html += f'''<pre><li class="s_{comparison_index}_{index}">{name_token_1}<br>{name_token_2}<br>{label}</li></pre>'''  
    html = html.replace("_________similarity_list_________", similarity_list_html)

    files_page = ""
    file_index = 0
    for path, code in files_1.items():
        path_label = f"""<div class="file_name">{path}</div>"""

        format_data = __get_preformat_info(comparison_results, 1, path)

        snippet = __to_html_snippet(format_data, 1, file_index, code)

        content = f"""<div class="raw_code"><pre>{snippet}</pre></div>"""
        files_page += path_label + content
        file_index += 1

    html = html.replace("_________1_files_1_________", files_page)
    
    files_page = ""
    file_index = 0
    for path, code in files_2.items():
        path_label = f"""<div class="file_name">{path}</div>"""

        format_data = __get_preformat_info(comparison_results, 2, path)

        snippet = __to_html_snippet(format_data, 2, file_index, code)

        content = f"""<div class="raw_code"><pre>{snippet}</pre></div>"""
        files_page += path_label + content
        file_index += 1

    html = html.replace("_________2_files_2_________", files_page)

    return html

def __get_script_part__():
    return """
    function addListeners(panel_list, left_panel, right_panel) {
      // Add event listeners to each list item
      panel_list.querySelectorAll('li').forEach((list_item) => {
        list_item.addEventListener('mouseenter', () => {
            // Get the id of the item
            const itemClass = list_item.getAttribute('class');
            // Highlight the corresponding items in the other panels
            panel_list.querySelectorAll("li." + itemClass).forEach((item) => {
                if (!item.classList.contains('highlighted')){
                    item.scrollIntoView({ behavior: 'auto', block: 'nearest', inline: 'start' })
                }

                item.classList.add('highlighted');
            });
            right_panel.querySelectorAll("span." + itemClass).forEach((item) => {
                if (!item.classList.contains('highlighted')){
                    item.scrollIntoView({ behavior: 'auto', block: 'nearest', inline: 'start' });
                }
                item.classList.add('highlighted');
            });
            left_panel.querySelectorAll("span." + itemClass).forEach((item) => {
                if (!item.classList.contains('highlighted')){
                    item.scrollIntoView({ behavior: 'auto', block: 'nearest', inline: 'start' });
                }
                item.classList.add('highlighted');
            });
        });

        list_item.addEventListener('mouseleave', () => {
            panel_list.querySelectorAll("li").forEach((item) => {
                item.classList.remove('highlighted');
            });
            left_panel.querySelectorAll('span').forEach((item) => {
                item.classList.remove('highlighted');
            });
        
            right_panel.querySelectorAll('span').forEach((item) => {
                item.classList.remove('highlighted');
            });
        });
      });
    }
    function addListenersPanels(panel_list, panel1, panel2) {
      // Add event listeners to each list item
      panel1.querySelectorAll('span').forEach((item) => {
        item.addEventListener('mouseenter', () => {
            // Get the id of the item
            const itemClass = item.getAttribute('class').slice(0, -9);
            // Highlight the corresponding items in the other panels
            panel_list.querySelectorAll("li." + itemClass).forEach((item) => {
                if (!item.classList.contains('highlighted')){
                    item.scrollIntoView({ behavior: 'auto', block: 'nearest', inline: 'start' });
                }
                item.classList.add('highlighted');
            });
            panel1.querySelectorAll("span." + itemClass).forEach((item) => {
                if (!item.classList.contains('highlighted')){
                    item.scrollIntoView({ behavior: 'auto', block: 'nearest', inline: 'start' });
                }
                item.classList.add('highlighted');
            });
            panel2.querySelectorAll("span." + itemClass).forEach((item) => {
                if (!item.classList.contains('highlighted')){
                    item.scrollIntoView({ behavior: 'auto', block: 'nearest', inline: 'start' });
                }
                item.classList.add('highlighted');
            });
        });

        item.addEventListener('mouseleave', () => {
            panel_list.querySelectorAll("li").forEach((item) => {
                item.classList.remove('highlighted');
            });
            panel1.querySelectorAll('span').forEach((item) => {
                item.classList.remove('highlighted');
            });
        
            panel2.querySelectorAll('span').forEach((item) => {
                item.classList.remove('highlighted');
            });
        });
      });
    }
    
    const list = document.getElementById('similarity_list');
    const left_panel = document.getElementById('files_1');
    const right_panel = document.getElementById('files_2');
    
    addListeners(list, left_panel, right_panel);
    addListenersPanels(list, left_panel, right_panel);
    addListenersPanels(list, right_panel, left_panel);
    """

def generate_html_diff_page(filename, output_file):
    with open(filename, 'r') as f:
        data = json.load(f)

    comparison_results = data['raw_comparison_results']

    files_1 = {}
    files_2 = {}
    for f in data['filenames_1']:
        files_1[f] =  __load_file(f)
    for f in data['filenames_2']:
        files_2[f] =  __load_file(f)

    html = ""
    html += f'''<html>{__get_html_head__()}'''
    html += f'''<body>{__get_html_body__(comparison_results, files_1, files_2)}</body>'''
    html += f'''<script>{__get_script_part__()}</script>'''
    html += '''</html>'''
    
    with open(output_file, 'w', encoding='utf8') as file:
        file.write(html)
