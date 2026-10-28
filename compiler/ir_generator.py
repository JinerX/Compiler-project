from typing import List, Optional
from .ast import *
from .ir import *

from .ast import Read as ASTRead, Write as ASTWrite
from .ir import Read as IRRead, Write as IRWrite


class IRGenerator:
    def __init__(self):
        self.instructions: List[IRInstruction] = []
        self.temp_counter = 0
        self.label_counter = 0
        self.current_scope = "main"

    def generate(self, program: Program) -> List[IRInstruction]:
            self.instructions = []

            self.emit(Jump("main"))
            
            for proc in program.procedures:
                self._visit_procedure(proc)
            
            self.emit(Label("main"))
            self._visit_main(program.main)
            
            return self.instructions


    def emit(self, instr: IRInstruction):
        self.instructions.append(instr)

    def new_temp(self) -> str:
        """Create a unique temporary variable name."""
        name = f"__t{self.temp_counter}"
        self.temp_counter += 1
        return name

    def new_label(self, suffix: str = "") -> str:
        """Create a unique label."""
        name = f"L{self.label_counter}_{suffix}" if suffix else f"L{self.label_counter}"
        self.label_counter += 1
        return name

    def resolve_name(self, name: str) -> str:
        if self.current_scope == "main":
            return name
        else:
            return f"{self.current_scope}__{name}"


    def _visit_procedure(self, proc: Procedure):
        self.current_scope = proc.name
        param_names = [f"{proc.name}__{p.name}" for p in proc.params]
        
        self.emit(ProcStart(proc.name, param_names))
        self._visit_commands(proc.commands)
        
        self.emit(Return(proc.name))
        self.emit(ProcEnd(proc.name))
        self.current_scope = "main"

    def _visit_main(self, main: Main):
        self.current_scope = "main"
        self._visit_commands(main.commands)

    def _visit_commands(self, commands: List[Command]):
        for cmd in commands:
            if isinstance(cmd, Assign):
                self._visit_assign(cmd)
            elif isinstance(cmd, IfThen):
                self._visit_if_then(cmd)
            elif isinstance(cmd, IfElse):
                self._visit_if_else(cmd)
            elif isinstance(cmd, WhileDo):
                self._visit_while(cmd)
            elif isinstance(cmd, RepeatUntil):
                self._visit_repeat(cmd)
            elif isinstance(cmd, ForLoop):
                self._visit_for(cmd)
            elif isinstance(cmd, ProcCall):
                self._visit_proc_call(cmd)
            elif isinstance(cmd, ASTRead):
                self._visit_read(cmd)
            elif isinstance(cmd, ASTWrite):
                self._visit_write(cmd)

    def _visit_assign(self, cmd: Assign):
        rhs_val = self._visit_expression(cmd.expr)
        
        target = cmd.target
        target_name = self.resolve_name(target.name)
        
        if target.index is not None:
            if isinstance(target.index, int):
                idx_op = target.index
            else:
                idx_op = self.resolve_name(target.index)
            
            self.emit(ArraySet(target_name, idx_op, rhs_val))
        else:
            self.emit(Copy(target_name, rhs_val))

    def _visit_expression(self, expr: Expression) -> Operand:
        if expr.op is None:
            return self._visit_value(expr.left)
        
        left_op = self._visit_value(expr.left)
        right_op = self._visit_value(expr.right)
        
        result_temp = self.new_temp()
        
        self.emit(BinOp(expr.op, result_temp, left_op, right_op))
        
        return result_temp

    def _visit_value(self, val: Value) -> Operand:
        if val.number is not None:
            return val.number
        
        ident = val.identifier
        name = self.resolve_name(ident.name)
        
        if ident.index is not None:
            result_temp = self.new_temp()
            
            if isinstance(ident.index, int):
                idx_op = ident.index
            else:
                idx_op = self.resolve_name(ident.index)
                
            self.emit(ArrayGet(result_temp, name, idx_op))
            return result_temp
        
        return name

    def _visit_if_then(self, cmd: IfThen):
        label_true = self.new_label("then")
        label_end = self.new_label("endif")
        
        self._visit_condition(cmd.cond, label_true, label_end)
        
        self.emit(Label(label_true))
        self._visit_commands(cmd.then_cmds)
        self.emit(Label(label_end))

    def _visit_if_else(self, cmd: IfElse):
        label_true = self.new_label("true")
        label_false = self.new_label("false")
        label_end = self.new_label("endif")
        
        self._visit_condition(cmd.cond, label_true, label_false)
        
        self.emit(Label(label_true))
        self._visit_commands(cmd.then_cmds)
        self.emit(Jump(label_end))
        
        self.emit(Label(label_false))
        self._visit_commands(cmd.else_cmds)
        
        self.emit(Label(label_end))

    def _visit_while(self, cmd: WhileDo):
        label_start = self.new_label("while_start")
        label_body = self.new_label("while_body")
        label_end = self.new_label("while_end")
        
        self.emit(Label(label_start))
        
        self._visit_condition(cmd.cond, label_body, label_end)
        
        self.emit(Label(label_body))
        self._visit_commands(cmd.body)
        self.emit(Jump(label_start))
        
        self.emit(Label(label_end))

    def _visit_repeat(self, cmd: RepeatUntil):
        label_start = self.new_label("repeat_start")
        label_end = self.new_label("repeat_end")
        
        self.emit(Label(label_start))
        self._visit_commands(cmd.body)
        
        self._visit_condition(cmd.cond, label_end, label_start)
        
        self.emit(Label(label_end))

    def _visit_for(self, cmd: ForLoop):
            label_start = self.new_label("for_start")
            label_end = self.new_label("for_end")
            
            iter_name = self.resolve_name(cmd.iter_name)
            start_val = self._visit_value(cmd.frm)
            self.emit(Copy(iter_name, start_val))
            
            limit_val = self._visit_value(cmd.to)
            limit_temp = self.new_temp()
            self.emit(Copy(limit_temp, limit_val))
            
            if cmd.descending:
                # DOWNTO Logic
                
                self.emit(JumpCond("<", iter_name, limit_temp, label_end))
                
                self.emit(Label(label_start))
                
                self._visit_commands(cmd.body)
                
                self.emit(JumpCond("=", iter_name, limit_temp, label_end))
                
                self.emit(BinOp("-", iter_name, iter_name, 1))
                self.emit(Jump(label_start))
                
            else:
                # TO Logic
                self.emit(Label(label_start))
                self.emit(JumpCond(">", iter_name, limit_temp, label_end))
                
                self._visit_commands(cmd.body)
                
                self.emit(BinOp("+", iter_name, iter_name, 1))
                self.emit(Jump(label_start))

            self.emit(Label(label_end))

    def _visit_condition(self, cond: Condition, label_true: str, label_false: str):
        """
        Generates code to jump to label_true if valid, else jump to label_false.
        """
        left = self._visit_value(cond.left)
        right = self._visit_value(cond.right)
        
        self.emit(JumpCond(cond.op, left, right, label_true))
        self.emit(Jump(label_false))

    def _visit_proc_call(self, cmd: ProcCall):
        for arg in cmd.args:
            resolved_arg = self.resolve_name(arg)
            self.emit(Param(resolved_arg))
            
        self.emit(Call(cmd.name))

    def _visit_read(self, cmd: ASTRead):
        target = cmd.target
        target_name = self.resolve_name(target.name)
        
        if target.index is not None:
            temp = self.new_temp()
            self.emit(IRRead(temp))
            
            if isinstance(target.index, int):
                idx = target.index
            else:
                idx = self.resolve_name(target.index)
            
            self.emit(ArraySet(target_name, idx, temp))
        else:
            self.emit(IRRead(target_name))

    def _visit_write(self, cmd: ASTWrite):
        val = self._visit_value(cmd.value)
        self.emit(IRWrite(val))