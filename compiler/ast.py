from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

@dataclass
class Program:
    procedures: List["Procedure"]
    main: "Main"

@dataclass
class Procedure:
    name: str
    params: List["Param"]
    declarations: List["Decl"]
    commands: List["Command"]

@dataclass
class Main:
    declarations: List["Decl"]
    commands: List["Command"]

@dataclass
class Param:
    mode: Optional[str]
    name: str

@dataclass
class Decl:
    name: str
    range: Optional[Tuple[int, int]] = None

@dataclass
class Command: pass

@dataclass
class Assign(Command):
    target: "Identifier"
    expr: "Expression"

@dataclass
class IfThen(Command):
    cond: "Condition"
    then_cmds: List[Command]

@dataclass
class IfElse(Command):
    cond: "Condition"
    then_cmds: List[Command]
    else_cmds: List[Command]

@dataclass
class WhileDo(Command):
    cond: "Condition"
    body: List[Command]

@dataclass
class RepeatUntil(Command):
    body: List[Command]
    cond: "Condition"

@dataclass
class ForLoop(Command):
    iter_name: str
    frm: "Value"
    to: "Value"
    descending: bool
    body: List[Command]

@dataclass
class ProcCall(Command):
    name: str
    args: List[str]

@dataclass
class Read(Command):
    target: "Identifier"

@dataclass
class Write(Command):
    value: "Value"

@dataclass
class Identifier:
    name: str
    index: Optional[Union[str, int]] = None

@dataclass
class Value:
    number: Optional[int] = None
    identifier: Optional[Identifier] = None

@dataclass
class Expression:
    left: Value
    op: Optional[str] = None
    right: Optional[Value] = None

@dataclass
class Condition:
    left: Value
    op: str
    right: Value
