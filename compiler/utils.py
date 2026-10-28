from .ast import *

def pretty_print(node, indent: int = 0):
    pad = "  " * indent
    if node is None:
        print(pad + "None")
        return
    t = type(node)
    if isinstance(node, Program):
        print(pad + "Program:")
        print(pad + "  Procedures:")
        for p in node.procedures:
            pretty_print(p, indent+2)
        print(pad + "  Main:")
        print(pad + "    Declarations:")
        for d in node.main.declarations:
            pretty_print(d, indent+3)
        print(pad + "    Commands:")
        for c in node.main.commands:
            pretty_print(c, indent+3)

    elif isinstance(node, Procedure):
        print(pad + f"Procedure {node.name} params={[(p.mode,p.name) for p in node.params]}")
        print(pad + "  Declarations:")
        for d in node.declarations:
            pretty_print(d, indent+2)
        print(pad + "  Commands:")
        for c in node.commands:
            pretty_print(c, indent+2)
    elif isinstance(node, Main):
        print(pad + "Main:")
        print(pad + "  Declarations:")
        for d in node.declarations:
            pretty_print(d, indent+2)
        print(pad + "  Commands:")
        for c in node.commands:
            pretty_print(c, indent+2)
    elif isinstance(node, Decl):
        if node.range:
            print(pad + f"Decl: {node.name} [{node.range[0]}:{node.range[1]}]")
        else:
            print(pad + f"Decl: {node.name}")
    elif isinstance(node, Assign):
        print(pad + "Assign:")
        print(pad + "  Target:")
        pretty_print(node.target, indent+2)
        print(pad + "  Expr:")
        pretty_print(node.expr, indent+2)
    elif isinstance(node, IfThen):
        print(pad + f"IfThen cond:")
        pretty_print(node.cond, indent+1)
        print(pad + "Then:")
        for c in node.then_cmds:
            pretty_print(c, indent+2)
    elif isinstance(node, IfElse):
        print(pad + f"IfElse cond:")
        pretty_print(node.cond, indent+1)
        print(pad + "Then:")
        for c in node.then_cmds:
            pretty_print(c, indent+2)
        print(pad + "Else:")
        for c in node.else_cmds:
            pretty_print(c, indent+2)
    elif isinstance(node, WhileDo):
        print(pad + "WhileDo:")
        pretty_print(node.cond, indent+1)
        for c in node.body:
            pretty_print(c, indent+2)
    elif isinstance(node, RepeatUntil):
        print(pad + "RepeatUntil:")
        for c in node.body:
            pretty_print(c, indent+2)
        print(pad + "Until:")
        pretty_print(node.cond, indent+1)
    elif isinstance(node, ForLoop):
        dir_s = "DOWNTO" if node.descending else "TO"
        print(pad + f"For {node.iter_name} FROM")
        pretty_print(node.frm, indent+1)
        print(pad + f" {dir_s}")
        pretty_print(node.to, indent+1)
        print(pad + "Body:")
        for c in node.body:
            pretty_print(c, indent+2)
    elif isinstance(node, ProcCall):
        print(pad + f"ProcCall {node.name} args={node.args}")
    elif isinstance(node, Read):
        print(pad + "Read:")
        pretty_print(node.target, indent+1)
    elif isinstance(node, Write):
        print(pad + "Write:")
        pretty_print(node.value, indent+1)
    elif isinstance(node, Identifier):
        if node.index is None:
            print(pad + f"Identifier: {node.name}")
        else:
            print(pad + f"Identifier: {node.name}[{node.index}]")
    elif isinstance(node, Value):
        if node.number is not None:
            print(pad + f"Number: {node.number}")
        else:
            print(pad + "Value Ident:")
            pretty_print(node.identifier, indent+1)
    elif isinstance(node, Expression):
        if node.op is None:
            print(pad + "Expr (single):")
            pretty_print(node.left, indent+1)
        else:
            print(pad + f"Expr: op {node.op}")
            print(pad + "  Left:")
            pretty_print(node.left, indent+2)
            print(pad + "  Right:")
            pretty_print(node.right, indent+2)
    elif isinstance(node, Condition):
        print(pad + f"Condition ({node.op})")
        print(pad + "  Left:")
        pretty_print(node.left, indent+2)
        print(pad + "  Right:")
        pretty_print(node.right, indent+2)
    else:
        print(pad + f"(Unhandled AST node type: {t})")
        print(node)