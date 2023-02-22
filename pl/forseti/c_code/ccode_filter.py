from dataclasses import asdict, dataclass

from clang.cindex import CursorKind as ClangCursorKind
from clang.cindex import Cursor as ClangCursor
from ..token import TokenKind

@dataclass
class CCodeFilterConfig:

    filter_struct_declaration: bool = True
    """Defines, if structure declaration should be filtered."""

    filter_function_declaration: bool = True
    """Defines, if structure declaration should be filtered."""

    filter_alias: bool = True
    """Defines, if alias (typedef) should be filtered."""

    filter_mixed_declarations: bool = True
    """Defines, if cursors for mixing declarations with statments or expressions(DECL_STMT)
    should be filtered. In most cases they should be, due to noise which are introduced in 
    sequence."""

    filter_brackets: bool = True
    """Defines, if brackets from compund statments - {statment; stamtent;}
    should be filtered. In most cases yes, due to noise reduction."""

    filter_parent_expression: bool = True
    """Defines, if parent expression should be filtered. Parent expression for example 
    is int var = (x + y)."""



class CCodeFilter:
    """"""

    def __is_struct_declaration(self, cursor: ClangCursor) -> bool:
        if cursor.kind is ClangCursorKind.STRUCT_DECL:
            return not cursor.is_definition()
        return False

    def __is_function_declaration(self, cursor: ClangCursor) -> bool:
        if cursor.kind is ClangCursorKind.FUNCTION_DECL:
            return not cursor.is_definition()
        return False

    def __is_alias(self, cursor: ClangCursor) -> bool:
        return cursor.kind is ClangCursorKind.TYPEDEF_DECL

    def __is_mixed_declarations(self, cursor: ClangCursor) -> bool:
        return cursor.kind is ClangCursorKind.DECL_STMT

    def __is_brackets(self, cursor: ClangCursor) -> bool:
        return cursor.kind is ClangCursorKind.COMPOUND_STMT

    def __is_parent_expression(self, cursor: ClangCursor) -> bool:
        return cursor.kind is ClangCursorKind.PAREN_EXPR

    def __is_unexposed_expression(self, cursor: ClangCursor) -> bool:
        return cursor.kind is ClangCursorKind.UNEXPOSED_EXPR

    def __is_type_reference(self, cursor: ClangCursor) -> bool:
        return cursor.kind is ClangCursorKind.TYPE_REF

    def __is_initialization_list(self, cursor: ClangCursor) -> bool:
        return cursor.kind is ClangCursorKind.INIT_LIST_EXPR

    def __init__(self, config=CCodeFilterConfig()) -> None:
        # self.__config = config
        self.__rules = []

        always_filter_rules = [
            self.__is_unexposed_expression, self.__is_type_reference,
            self.__is_initialization_list
        ]

        self.__rules += always_filter_rules

        associated_rules = {}
        associated_rules['filter_alias'] = self.__is_alias
        associated_rules[
            'filter_mixed_declarations'] = self.__is_mixed_declarations
        associated_rules[
            'filter_function_declaration'] = self.__is_function_declaration
        associated_rules[
            'filter_struct_declaration'] = self.__is_struct_declaration
        associated_rules['filter_brackets'] = self.__is_brackets
        associated_rules[
            'filter_parent_expression'] = self.__is_parent_expression

        config_fields = asdict(config)
        for field_name, rule in associated_rules.items():
            if config_fields[field_name]:
                self.__rules.append(rule)

    def validate(self, cursor: ClangCursorKind) -> bool:
        """Decide, if particall clang cursor should be part of CodeUnit, 
        based on config passed in CProgramFilter constructor."""
        # if not cursor or cursor.kind is TokenKind.Invalid:
        if not cursor:
            return False

        # temporary solution
        if cursor.kind is ClangCursorKind.NULL_STMT:
            return False

        for rule in self.__rules:
            if rule(cursor):
                return False

        return True