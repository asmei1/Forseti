import logging
import os
import codecs

from typing import List
from clang.cindex import Index
from ..code_parser import CodeParser
from ..program import Program
from ..tokenized_program import TokenizedProgram
from .clang_ast_converter import ClangASTConverter 
from .ccode_filter import CCodeFilter


class CCodeParser(CodeParser):
    def __init__(self, ccodeFilter:CCodeFilter) -> None:
        super().__init__()
        self.clang_ast_converter = ClangASTConverter(ccodeFilter)
    
    def remove_BOM_from_code(self, file_content):
        BOMLEN = len(codecs.BOM_UTF8)
        a = file_content[0][:BOMLEN]
        if file_content[0][:BOMLEN] == codecs.BOM_UTF8 or file_content[0][:BOMLEN] == "ï»¿":
            file_content[0] = file_content[0][BOMLEN:]
        return file_content
    
    def __parse_program_in_memory__(self, program: Program):
        translation_units = []
        filenames_with_src_codes = list(zip(program.filenames, ["".join(self.remove_BOM_from_code(file_content)) for file_content in program.raw_codes]))
        for filename in program.filenames:
            # Parse file.
            logging.debug('Processing %s ...', filename)

            # create index
            index = Index.create()
            
            # parse file
            # Here I also added NULL definition - because I skip all standard includes, it's recognized by libcland
            translation_units.append(index.parse(path=filename, unsaved_files=filenames_with_src_codes, args=['-D NULL=0']))
        return translation_units
    
    def __parse_program_from_file__(self, program: Program):
        translation_units = []
        for filename in program.filenames:
            # Parse file.
            logging.debug('Processing %s ...', filename)

            # create index
            index = Index.create()
            
            # parse file
            # Here I also added NULL definition - because I skip all standard includes, it's recognized by libcland
            translation_units.append(index.parse(path=filename, args=['-D NULL=0']))
        return translation_units
    
    def __filter_translation_units__(self, translation_units: List, program_filenames: List[str]):
        cursors = []
        for translation_unit in translation_units:
            for node in translation_unit.cursor.get_children():
                if node.location.file.name in program_filenames:
                    cursors.append(node)
        return cursors


    def parse(self, program: Program) -> TokenizedProgram:
        logging.debug('C program processing ...')

        tokenized_program = TokenizedProgram()
        tokenized_program.filenames = program.filenames
        tokenized_program.raw_codes = program.raw_codes
        if not program.author:
            basename = os.path.basename(os.path.dirname(program.filenames[0]))
            if len(program.filenames) > 1:
                tokenized_program.author = str(basename)
            else:
                filename = os.path.splitext(os.path.basename(program.filenames[0]))[0]
                tokenized_program.author = str(basename) + str(filename)

        else:
            tokenized_program.author = program.author
        
        logging.debug('Parsing ...')
        translation_units = []
        if len(program.raw_codes):
            translation_units = self.__parse_program_in_memory__(program)
        else:
            translation_units = self.__parse_program_from_file__(program)


        logging.debug('Filtering tokens ...')
        cursors = self.__filter_translation_units__(translation_units, program.filenames)

        logging.debug('Converting Clang tokens to Forseti format ...')
        tokenized_program.code_units = self.clang_ast_converter.convert(cursors)

        logging.debug('Program parsing done.')
        return tokenized_program