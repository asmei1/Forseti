import codecs
from typing import List, Tuple
from pl.forseti.program import Program
def read_programs_sets(file_paths_sets: List[List[str]]) -> List[Program]:
    programs_sets = []
    for paths in file_paths_sets:
        names = []
        files_content = []
        for path in paths:
            file = open(path, mode='r', encoding='latin-1')
            
            names.append(path)
            files_content.append(file.readlines())
            file.close()
        if names and files_content:
            programs_sets.append(Program(names, files_content))
    return programs_sets
