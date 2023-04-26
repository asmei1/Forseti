import json
from bs4 import BeautifulSoup
import json


def __generate_html_diff(html, start_1, end_1, index_1, start_2, end_2, index_2, classId):
    soup = BeautifulSoup(html, 'html.parser')
    # highlight the difference between the start and end lines in both files
    if start_1 == end_1:
        line = soup.find(id=f'l{index_1}_{start_1}')
        line['class'] += [f'modified click_{classId}']
    else:
        for i in range(start_1, end_1+1):
            line = soup.find(id=f'l{index_1}_{i}')
            line['class'] += [f'modified click_{classId}']
            
    if start_2 == end_2:
        line = soup.find(id=f'r{index_2}_{start_2}')
        line['class'] += [f'modified click_{classId}']
    else:
        for i in range(start_2, end_2+1):
            line = soup.find(id=f'r{index_2}_{i}')
            line['class'] += [f'modified click_{classId}']

    return soup.prettify()


def __load_file(filename):
    with open(filename, 'r', encoding='latin-1') as file:
        return file.readlines()

def __to_html_snippet(iterator, code, prefix):
    remove_forbidden_tags = lambda x: x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    code = list(map(remove_forbidden_tags, code))
    html_fragment = "".join([f"<code class='' id='{prefix}{iterator}_{i+1}'>" + line + "</code>" for i, line in enumerate(code)])
    return html_fragment

def generate_html_diff_page(filename, output_file):
    with open(filename, 'r') as f:
        data = json.load(f)

    comparison_results = data['raw_comparison_results']

    files_1 = []
    files_2 = []
    for f in data['filenames_1']:
        files_1.append((f, __load_file(f)))
    for f in data['filenames_2']:
        files_2.append((f, __load_file(f)))
    html = ""
    html += '''
        <html>
        <head>

            <style>
                .diff { font-family: Courier; }
                .diff_header { background-color: #f8f8f8 }
                .empty_line { background-color: #cfc }
                .modified { background-color: #fcc }
                .selected_modified { background-color: red }
                .row {
                    display: flex;
                }

                .column {
                    flex: 50%;
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
        </head>
        <body>
        '''
        
    iterator = 0
    for f_1, f_2 in zip(files_1, files_2):
        file_path_1, file_1 = f_1
        file_path_2, file_2 = f_2
        html += f'''
                    <div class="sequence_{iterator}">
                        <div class="row">
                            <div class="column">{file_path_1}</div>
                            <div class="column">{file_path_2}</div>
                        </div>
                        <div class="row raw_code">
                            <div class="diff column" valign="top">
                                <pre>
                                    {__to_html_snippet(iterator, file_1, 'l')}
                                </pre>
                            </div>
                            <div class="diff column" valign="top">
                                <pre>
                                    {__to_html_snippet(iterator, file_2, 'r')}
                                </pre>
                            </div>
                        </div>
                    </div>
        '''
        iterator += 1
    for i in range(iterator, len(files_1)):
        file_path_1, file_1 = files_1[i]
        html += f'''
                    <div class="sequence_{iterator}">
                        <div class="row">
                            <div class="column">{file_path_1}</div>
                            <div class="column"></div>
                        </div>
                        <div class="row raw_code">
                            <div class="diff column" valign="top">
                                <pre>
                                    {__to_html_snippet(iterator, file_1, 'l')}
                                </pre>
                            </div>
                            <div class="diff column" valign="top">
                                <pre>
                                </pre>
                            </div>
                        </div>
                    </div>
        '''
        iterator += 1
    for i in range(iterator, len(files_2)):
        file_path_2, file_2 = files_2[i]
        html += f'''
                    <div class="sequence_{iterator}">
                        <div class="row">
                            <div class="column"></div>
                            <div class="column">{file_path_2}</div>
                        </div>
                        <div class="row raw_code">
                            <div class="diff column" valign="top">
                            </div>
                            <div class="diff column" valign="top">
                                <pre>
                                    {__to_html_snippet(iterator, file_2, 'r')}
                                </pre>
                            </div>
                        </div>
                    </div>
        '''
        iterator += 1



    html += '''
    </body>
    </html>
    '''
    i = 0
    for comparison in comparison_results:
        for localization in comparison['localization']:
            start_1 = localization['start_token_1']['line'] 
            end_1 = localization['end_token_1']['line']  
            path_1 = localization['start_token_1']['path']
            index_1 = [i for i, x in enumerate(files_1) if x[0] == path_1][0]

            start_2 = localization['start_token_2']['line'] 
            end_2 = localization['end_token_2']['line'] 
            path_2 = localization['start_token_2']['path'] 
            index_2 = [i for i, x in enumerate(files_2) if x[0] == path_2][0]
            html = __generate_html_diff(html, start_1, end_1, index_1, start_2, end_2, index_2, i)
            i += 1

    soup = BeautifulSoup(html, 'html.parser')
    script_tag = soup.new_tag('script')

    script_tag.string = '''
var cellElements = document.getElementsByTagName('code');

function colorSimilar(event) {
  var classNames = event.target.className.split(" ");
  for (var i = 0; i < cellElements.length; i++) {
    var names = cellElements[i].className.split(" ");
    if (!names.includes("modified")) {
        continue;
    }
    names.shift()
    if (names.filter(element => classNames.includes(element)).length) {
      cellElements[i].classList.add('selected_modified');    

    } else {
      cellElements[i].classList.remove('selected_modified');    
    }
  }
}

for (var i = 0; i < cellElements.length; i++) {
  cellElements[i].addEventListener('mouseover', colorSimilar)
}
    '''
    soup.html.append(script_tag)
    html = soup.prettify()
    with open(output_file, 'w', encoding='utf8') as file:
        file.write(html)
