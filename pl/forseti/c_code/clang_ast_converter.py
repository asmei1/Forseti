from typing import List, Tuple, Dict, Deque
from collections import deque
from clang.cindex import CursorKind as ClangCursorKind
from clang.cindex import TypeKind as ClangCursorType
from clang.cindex import Cursor as ClangCursor
from ..token import Token, TokenKind, VariableTokenKind
from ..code_unit import CodeUnit 
from .ccode_filter import CCodeFilter

def __add_children_to_stack__(parent_token: Token, cursor: ClangCursorKind, stack: Deque[Tuple[Token, ClangCursor]]):
    stack.extendleft([parent_token, child] for child in cursor.get_children())

class ClangASTConverter:
    def __init__(self, cursor_filter: CCodeFilter) -> None:
        self.conversion_cursor_map = self.__create_cursor_kind_conversion_dict()
        self.conversion_types_map = self.__create_type_kind_conversion_map__()
        self.cursor_filter = cursor_filter

    def __create_cursor_kind_conversion_dict(self) -> Dict[ClangCursorKind, TokenKind]:
        conversion_map: Dict[ClangCursorKind, TokenKind] = {}
        conversion_map[ClangCursorKind.STRUCT_DECL] = TokenKind.ClassDecl
        conversion_map[ClangCursorKind.ENUM_DECL] = TokenKind.EnumDecl
        conversion_map[ClangCursorKind.FIELD_DECL] = TokenKind.FieldDecl
        conversion_map[ClangCursorKind.VAR_DECL] = TokenKind.VariableDecl
        conversion_map[ClangCursorKind.FUNCTION_DECL] = TokenKind.FunctionDecl
        conversion_map[ClangCursorKind.PARM_DECL] = TokenKind.ParameterDecl

        conversion_map[ClangCursorKind.CALL_EXPR] = TokenKind.FunctionCall
        conversion_map[ClangCursorKind.INTEGER_LITERAL, ClangCursorKind.NULL_STMT] = TokenKind.NumericLiteral
        conversion_map[ClangCursorKind.CHARACTER_LITERAL] = TokenKind.CharacteLiteral
        conversion_map[ClangCursorKind.FLOATING_LITERAL] = TokenKind.FloatingPointLiteral
        conversion_map[ClangCursorKind.STRING_LITERAL] = TokenKind.StringLiteral

        conversion_map[ClangCursorKind.UNARY_OPERATOR] = TokenKind.UnaryOp
        conversion_map[ClangCursorKind.ARRAY_SUBSCRIPT_EXPR] = TokenKind.ArraySubscript
        conversion_map[ClangCursorKind.BINARY_OPERATOR] = TokenKind.BinaryOp
        conversion_map[ClangCursorKind.COMPOUND_ASSIGNMENT_OPERATOR] = TokenKind.CompoundAssigmentOp
        conversion_map[ClangCursorKind.CONDITIONAL_OPERATOR] = TokenKind.TernaryOp
        conversion_map[ClangCursorKind.CSTYLE_CAST_EXPR] = TokenKind.CastExpr

        conversion_map[ClangCursorKind.COMPOUND_STMT] = TokenKind.CompoundStmt
        conversion_map[ClangCursorKind.CASE_STMT] = TokenKind.Case
        conversion_map[ClangCursorKind.DEFAULT_STMT] = TokenKind.Default
        conversion_map[ClangCursorKind.IF_STMT] = TokenKind.If
        conversion_map[ClangCursorKind.SWITCH_STMT] = TokenKind.Switch
        conversion_map[ClangCursorKind.WHILE_STMT] = TokenKind.While
        conversion_map[ClangCursorKind.DO_STMT] = TokenKind.DoWhile
        conversion_map[ClangCursorKind.FOR_STMT] = TokenKind.For
        conversion_map[ClangCursorKind.CONTINUE_STMT] = TokenKind.Continue
        conversion_map[ClangCursorKind.BREAK_STMT] = TokenKind.Break
        conversion_map[ClangCursorKind.RETURN_STMT] = TokenKind.Return
        conversion_map[ClangCursorKind.DECL_STMT] = TokenKind.DeclStmt
        # conversion_map[ClangCursorKind.DECL_REF_EXPR] = TokenKind.DeclRefExpr
        conversion_map[ClangCursorKind.TYPEDEF_DECL] = TokenKind.Alias

        # Experimental C++ cursors handling
        conversion_map[ClangCursorKind.CLASS_DECL] = TokenKind.ClassDecl
        conversion_map[ClangCursorKind.CXX_TRY_STMT] = TokenKind.Try
        conversion_map[ClangCursorKind.CXX_METHOD] = TokenKind.MethodDecl
        conversion_map[ClangCursorKind.CXX_THROW_EXPR] = TokenKind.Throw
        conversion_map[ClangCursorKind.CXX_CATCH_STMT] = TokenKind.Catch
        conversion_map[ClangCursorKind.CXX_STATIC_CAST_EXPR] = TokenKind.CastExpr
        conversion_map[ClangCursorKind.CXX_DYNAMIC_CAST_EXPR] = TokenKind.CastExpr
        conversion_map[ClangCursorKind.CXX_REINTERPRET_CAST_EXPR] = TokenKind.CastExpr
        conversion_map[ClangCursorKind.CXX_CONST_CAST_EXPR] = TokenKind.CastExpr
        conversion_map[ClangCursorKind.CXX_NEW_EXPR] = TokenKind.Allocation
        conversion_map[ClangCursorKind.CXX_DELETE_EXPR] = TokenKind.Deallocation


        return conversion_map
    
    def __create_type_kind_conversion_map__(self) -> Dict[ClangCursorType, TokenKind]:
        conversion_map: Dict[ClangCursorType, TokenKind] = {}
        conversion_map[(ClangCursorType.VOID)] = VariableTokenKind.Void
        conversion_map[(ClangCursorType.BOOL)] = VariableTokenKind.Bool
        conversion_map[(ClangCursorType.CHAR_S, ClangCursorType.CHAR_U,
                    ClangCursorType.UCHAR, ClangCursorType.CHAR16,
                    ClangCursorType.CHAR32)] = VariableTokenKind.Bool
        conversion_map[(ClangCursorType.USHORT, ClangCursorType.UINT,
                    ClangCursorType.ULONG, ClangCursorType.ULONGLONG,
                    ClangCursorType.UINT128, ClangCursorType.SHORT,
                    ClangCursorType.INT, ClangCursorType.LONG,
                    ClangCursorType.LONGLONG,
                    ClangCursorType.INT128)] = VariableTokenKind.Numeric
        conversion_map[(ClangCursorType.FLOAT, ClangCursorType.DOUBLE,
                    ClangCursorType.LONGDOUBLE)] = VariableTokenKind.FloatingPoint
        conversion_map[(ClangCursorType.ENUM)] = VariableTokenKind.Enum
        conversion_map[(ClangCursorType.POINTER)] = VariableTokenKind.Pointer
        conversion_map[(ClangCursorType.CONSTANTARRAY,
                    ClangCursorType.VARIABLEARRAY,
                    ClangCursorType.DEPENDENTSIZEDARRAY)] = VariableTokenKind.Array
        return conversion_map

    def __get_numeric_literal__(self, clang_cursor: ClangCursor) -> str:
        tokens = [token for token in clang_cursor.get_tokens()]
        # It seems like clang interpret 'NULL' in some strange way, so this if statment is needed.
        # If NULL is detected, '0' will be returned.
        if len(tokens):
            return tokens[0].spelling
        else:
            return "0"
        
    def __get_binary_op_token__(self, clang_cursor: ClangCursor) -> str:
        # binary operator have always 2 children
        binary_op_children = [child for child in clang_cursor.get_children()]
        left_offset = len([token for token in binary_op_children[0].get_tokens()])
        return list(clang_cursor.get_tokens())[left_offset].spelling
    
    def __clang_cursor_kind_to_token_type_kind__(self, clang_cursor: ClangCursor) -> VariableTokenKind:
        clang_canonical_type = clang_cursor.type.get_canonical()
        
        for clang_type_kind, token_type_kind in self.conversion_types_map.items():
            if isinstance(clang_type_kind, tuple):
                if clang_canonical_type in clang_type_kind:
                    return token_type_kind
            else:
                if clang_canonical_type == clang_type_kind:
                    return token_type_kind

        return VariableTokenKind.NoType
        
    def __clang_cursor_kind_to_token_kind__(self, clang_cursor: ClangCursor) -> TokenKind:
        clang_cursor_kind = clang_cursor.kind
        for clang_kind, token_kind in self.conversion_cursor_map.items():
            if clang_cursor_kind == clang_kind:
                return token_kind

        return TokenKind.Invalid
        

    def __clang_cursor_to_token__(self, clang_cursor: ClangCursor, parent_token:Token) -> Token:
        token = Token()
        token.name = clang_cursor.displayname
        token.type_name = clang_cursor.type.get_canonical().spelling
        token.token_kind = self.__clang_cursor_kind_to_token_kind__(clang_cursor)
        token.variable_token_kind = self.__clang_cursor_kind_to_token_type_kind__(clang_cursor)
        token.parent_token = parent_token
        #TODO: Maybe its worth to store only basename?
        token.location = (clang_cursor.location.file.name,
                            clang_cursor.location.line,
                            clang_cursor.location.column)
        
        if token.token_kind == TokenKind.BinaryOp:
                token.name = self.__get_binary_op_token__(clang_cursor)
        
        if token.token_kind == TokenKind.VariableDecl:
            if token.variable_token_kind in [VariableTokenKind.Numeric, VariableTokenKind.FloatingPoint]:
                token.name = self.__get_numeric_literal__(clang_cursor)

        return token
    

        
    def __convert_root_cursors__(self, clang_cursors: List[ClangCursor]) -> Tuple[List['Token'], Deque[Tuple[Token, ClangCursor]]]:
        root_stack = deque()
        root_stack.extendleft([(None, cursor) for cursor in clang_cursors])
        root_ast_tokens:List['Token'] = []
        stack = deque()
        while root_stack:
            parent_token, current_cursor = root_stack.popleft()
            if self.cursor_filter.validate(current_cursor):
                token = self.__clang_cursor_to_token__(current_cursor, parent_token)
                root_ast_tokens.append(token)
                __add_children_to_stack__(token, current_cursor, stack)

        return root_ast_tokens, stack
        
    def __convert_children_cursors__(self, stack: Deque[Tuple[Token, ClangCursor]]) -> None:
        while stack:
            parent_token, current_cursor = stack.popleft()
            if self.cursor_filter.validate(current_cursor):
                token = self.__clang_cursor_to_token__(current_cursor, parent_token)    
                parent_token.children.append(token)
                __add_children_to_stack__(token, current_cursor, stack)
            else:
                __add_children_to_stack__(parent_token, current_cursor, stack)


    def convert(self, clang_cursors: List[ClangCursor]) -> List['CodeUnit']:
        root_ast_tokens, stack = self.__convert_root_cursors__(clang_cursors)
        self.__convert_children_cursors__(stack)

        return [CodeUnit(root_token) for root_token in root_ast_tokens]