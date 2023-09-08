from typing import List, Tuple
from dataclasses import dataclass, field, asdict


class TokenKind:
    """Represents cursor kind."""

    cursor_type_counter: int = 0
    cursors_unique_list_of_short_names: List[str] = []
    token_kind_list: List["TokenKind"] = []

    def __init__(self, name: str, unique_short_name: str) -> None:
        self._name = name
        self._short_name = unique_short_name
        self._id = TokenKind.cursor_type_counter
        TokenKind.cursor_type_counter = 1 + TokenKind.cursor_type_counter

        self.__check_if_short_name_exists__(unique_short_name)
        TokenKind.cursors_unique_list_of_short_names.append(unique_short_name)
        TokenKind.token_kind_list.append(self)

    @property
    def name(self) -> str:
        """Cursor kind full name."""
        return self._name

    @property
    def short_name(self) -> str:
        """Cursor kind short name (3 unique, uppercase characters)."""
        return self._short_name

    @property
    def id(self) -> int:
        """Cursor unique id."""
        return self._id

    def __repr__(self) -> str:
        return f"[{self.name} {self.short_name}]"

    def __check_if_short_name_exists__(self, short_name) -> bool:
        if short_name in TokenKind.cursors_unique_list_of_short_names:
            raise RuntimeError("Cursor with that name already exist!")

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, TokenKind):
            return self.id == __o.id
        return False


class VariableTokenKind(TokenKind):
    """Represents variable type kind."""

    def __init__(self, name: str, unique_short_name: str) -> None:
        super().__init__(name, unique_short_name)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, VariableTokenKind):
            return self.id == __o.id
        return False


TokenKind.Invalid = TokenKind("Invalid type", "INV")
# variables
VariableTokenKind.NoType = VariableTokenKind("No type", "NOT")
VariableTokenKind.Void = VariableTokenKind("Void type", "VOI")
VariableTokenKind.Pointer = VariableTokenKind("Pointer type", "PTR")
VariableTokenKind.Bool = VariableTokenKind("Bool type", "BOO")
VariableTokenKind.Char = TokenKind("Char type", "CHA")
VariableTokenKind.Numeric = VariableTokenKind("Numeric type", "NUM")
VariableTokenKind.FloatingPoint = VariableTokenKind("Floating point presicion type", "FLP")
VariableTokenKind.Enum = VariableTokenKind("Enum type", "ENU")
VariableTokenKind.Array = VariableTokenKind("Array type", "ARR")
# literals
TokenKind.NumericLiteral = TokenKind("Numeric literal type", "NLL")
TokenKind.FloatingPointLiteral = TokenKind("Floating point literal type", "FLL")
TokenKind.StringLiteral = TokenKind("String literal type", "STL")
# structures and functions
TokenKind.ClassDecl = TokenKind("Class decl", "CLS")
TokenKind.MethodDecl = TokenKind("Method decl", "MET")
TokenKind.FieldDecl = TokenKind("Field decl", "FIE")
TokenKind.EnumDecl = TokenKind("Enum decl", "EUD")
TokenKind.FunctionDecl = TokenKind("Function type decl", "FUN")
TokenKind.ParameterDecl = TokenKind("Function parameter type decl", "FPA")
TokenKind.FunctionCall = TokenKind("Function call", "FCL")
TokenKind.VariableDecl = TokenKind("Variable", "VAR")
TokenKind.DeclRefExpr = TokenKind("DeclRefExpr", "DRE")

TokenKind.Try = TokenKind("Try statment", "TRY")
TokenKind.Throw = TokenKind("Throw statment", "TRH")
TokenKind.Catch = TokenKind("Catch statment", "CAT")

TokenKind.Allocation = TokenKind("Memory allocation statment", "ALL")
TokenKind.Deallocation = TokenKind("Memory deallocation statment", "DEL")
TokenKind.Break = TokenKind("Break statment", "BRE")
TokenKind.Continue = TokenKind("Continue", "CNT")
TokenKind.For = TokenKind("For loop", "FOR")
TokenKind.DoWhile = TokenKind("Do while loop", "DOW")
TokenKind.While = TokenKind("While loop", "WHI")
TokenKind.Switch = TokenKind("Switch statment", "SWI")
TokenKind.Default = TokenKind("Default statment in switch", "DEF")
TokenKind.Case = TokenKind("Case statment in switch", "CAS")
TokenKind.If = TokenKind("If statment", "IFS")
TokenKind.DeclStmt = TokenKind("Declaration statment", "DEC")
TokenKind.Return = TokenKind("Return statment", "RET")
#
# Compound assignment such as "+=" or "{}"
TokenKind.CompoundStmt = TokenKind("Compound statment", "COM")

# A builtin binary operation expression such as "x + y" or
# "x <= y".
TokenKind.BinaryOp = TokenKind("Binary operator", "BIO")
TokenKind.CompoundAssigmentOp = TokenKind("Compound assigment operator", "COO")
TokenKind.UnaryOp = TokenKind("Unary operator", "UNO")
TokenKind.ArraySubscript = TokenKind("Array subscript ([]) operator", "ARS")
TokenKind.TernaryOp = TokenKind("Ternary (conditional) operator", "TER")
TokenKind.CastExpr = TokenKind("Cast type", "CST")
TokenKind.Alias = TokenKind("Alias on type, typedef", "TPD")


@dataclass
class Location:
    path: str = ""
    line: int = -1
    column: int = -1


@dataclass
class Token:
    name: str = ""
    type_name: str = ""
    token_kind: TokenKind = None
    variable_token_kind: VariableTokenKind = None
    location: Location = None
    children: List["Token"] = field(default_factory=list)
    parent_token: "Token" = None

    def location_as_dict(self):
        return asdict(self.location)

    def walk_preorder(self):
        """Depth-first preorder walk over the cursor and its descendants.

        Yields cursors.
        """
        yield self
        for child in self.children:
            for descendant in child.walk_preorder():
                yield descendant
