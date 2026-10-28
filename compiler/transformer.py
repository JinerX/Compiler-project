from lark import Lark, Transformer, Token
from .grammar import GRAMMAR
from .ast import *
from typing import List, Any, Optional

PARSER = Lark(GRAMMAR, start="start", parser="lalr", propagate_positions=True)


class ASTTransformer(Transformer):
    def NUM(self, tok: Token):
        return int(tok.value)

    def PIDENT(self, tok: Token):
        return str(tok.value)

    def TYPE(self, tok: Token):
        return str(tok.value)

    def declaration(self, items: List[Any]):
        if len(items) == 1:
            return Decl(name=items[0])
        name = items[0]
        low = int(items[1])
        high = int(items[2])
        return Decl(name=name, range=(low, high))

    def declarations(self, items: List[Decl]):
        return list(items)

    def args_decl_item(self, items):
        if len(items) == 1:
            return Param(mode=None, name=items[0])
        mode = items[0] if items[0] in ("I", "O", "T") else None
        return Param(mode=mode, name=items[1])

    def args_decl(self, items):
        return list(items)

    def args(self, items):
        return list(items)

    def proc_head(self, items):
        return (items[0], items[1])

    def proc_call(self, items):
        name = items[0]
        args = items[1] if items else []
        return ProcCall(name=name, args=args)

    def proc_call_stmt(self, items):
        return items[0]

    def ident(self, items):
        return Identifier(name=items[0])

    def arr_ident(self, items):
        return Identifier(name=items[0], index=items[1])

    def arr_const_index(self, items):
        return Identifier(name=items[0], index=int(items[1]))

    def number(self, items):
        return Value(number=int(items[0]))

    def value(self, items):
        v = items[0]
        if isinstance(v, Value):
            return v
        if isinstance(v, Identifier):
            return Value(identifier=v)
        return Value(number=int(v))

    def add(self, items): return Expression(left=items[0], op='+', right=items[1])
    def sub(self, items): return Expression(left=items[0], op='-', right=items[1])
    def mul(self, items): return Expression(left=items[0], op='*', right=items[1])
    def div(self, items): return Expression(left=items[0], op='/', right=items[1])
    def mod(self, items): return Expression(left=items[0], op='%', right=items[1])

    def expression(self, items):
        if len(items) == 1:
            return Expression(left=items[0])
        return items[0]

    def eq(self, items): return Condition(left=items[0], op='=', right=items[1])
    def ne(self, items): return Condition(left=items[0], op='!=', right=items[1])
    def gt(self, items): return Condition(left=items[0], op='>', right=items[1])
    def lt(self, items): return Condition(left=items[0], op='<', right=items[1])
    def ge(self, items): return Condition(left=items[0], op='>=', right=items[1])
    def le(self, items): return Condition(left=items[0], op='<=', right=items[1])

    def assign(self, items):
        return Assign(target=items[0], expr=items[1])

    def if_then(self, items):
        return IfThen(cond=items[0], then_cmds=items[1])

    def if_else(self, items):
        return IfElse(cond=items[0], then_cmds=items[1], else_cmds=items[2])

    def while_do(self, items):
        return WhileDo(cond=items[0], body=items[1])

    def repeat_until(self, items):
        return RepeatUntil(body=items[0], cond=items[1])

    def for_to(self, items):
        return ForLoop(iter_name=items[0], frm=items[1], to=items[2], descending=False, body=items[3])

    def for_downto(self, items):
        return ForLoop(iter_name=items[0], frm=items[1], to=items[2], descending=True, body=items[3])

    def read(self, items):
        return Read(target=items[0])

    def write(self, items):
        return Write(value=items[0])

    def commands(self, items):
        return list(items)

    def procedure(self, items):
        name, params = items[0]
        idx = 1
        declarations = []
        if idx < len(items) and isinstance(items[idx], list) and all(isinstance(x, Decl) for x in items[idx]):
            declarations = items[idx]
            idx += 1
        commands = items[idx]
        return Procedure(name=name, params=params, declarations=declarations, commands=commands)

    def main(self, items):
        if len(items) == 2:
            decls = items[0] if isinstance(items[0], list) else []
            cmds = items[1] if isinstance(items[1], list) else []
        else:
            decls = []
            cmds = items[0]
        return Main(declarations=decls, commands=cmds)

    def procedures(self, items):
        return list(items)

    def start(self, items):
        return Program(procedures=items[0], main=items[1])


def parse_program(text: str) -> Program:
    tree = PARSER.parse(text)
    ast = ASTTransformer().transform(tree)
    return ast
