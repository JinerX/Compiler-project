from dataclasses import dataclass
from typing import Union, Optional

Operand = Union[str, int]

@dataclass
class IRInstruction:
    """Base class for all IR instructions."""
    def __str__(self):
        return self.__class__.__name__


@dataclass
class Label(IRInstruction):
    """Mark a specific location in the code."""
    name: str

    def __str__(self):
        return f"{self.name}:"

@dataclass
class Jump(IRInstruction):
    """Unconditional jump."""
    target: str

    def __str__(self):
        return f"JUMP {self.target}"

@dataclass
class JumpCond(IRInstruction):
    """
    Conditional Jump based on comparison: left OP right.
    Ops: ==, !=, >, <, >=, <=
    """
    op: str
    left: Operand
    right: Operand
    target: str

    def __str__(self):
        return f"IF {self.left} {self.op} {self.right} GOTO {self.target}"


@dataclass
class Copy(IRInstruction):
    """dest := src (Variable to Variable or Constant to Variable)"""
    dest: str
    src: Operand

    def __str__(self):
        return f"{self.dest} := {self.src}"


@dataclass
class BinOp(IRInstruction):
    """dest := left OP right"""
    op: str
    dest: str
    left: Operand
    right: Operand

    def __str__(self):
        return f"{self.dest} := {self.left} {self.op} {self.right}"


@dataclass
class ArrayGet(IRInstruction):
    """dest := name[index]"""
    dest: str
    name: str
    index: Operand

    def __str__(self):
        return f"{self.dest} := {self.name}[{self.index}]"

@dataclass
class ArraySet(IRInstruction):
    """name[index] := src"""
    name: str
    index: Operand
    src: Operand

    def __str__(self):
        return f"{self.name}[{self.index}] := {self.src}"


@dataclass
class ProcStart(IRInstruction):
    name: str
    args: list[str]

    def __str__(self):
        return f"PROC {self.name}({', '.join(self.args)})"

@dataclass
class ProcEnd(IRInstruction):
    name: str

    def __str__(self):
        return f"ENDPROC {self.name}"

@dataclass
class Return(IRInstruction):
    proc_name: str 
    def __str__(self):
        return f"RETURN {self.proc_name}"

@dataclass
class Param(IRInstruction):
    """Push an argument before a CALL"""
    value: Operand

    def __str__(self):
        return f"PARAM {self.value}"

@dataclass
class Call(IRInstruction):
    proc_name: str
    
    def __str__(self):
        return f"CALL {self.proc_name}"


@dataclass
class Read(IRInstruction):
    dest: str

    def __str__(self):
        return f"READ {self.dest}"

@dataclass
class Write(IRInstruction):
    val: Operand

    def __str__(self):
        return f"WRITE {self.val}"