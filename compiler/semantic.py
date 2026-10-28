from typing import Optional, List, Tuple, Dict, Set
from .symbols import SymbolTable, Symbol
from .errors import Diagnostics
from .ast import *
from lark import Tree as LarkTree
from lark import Token


class SemanticAnalyzer:
    def __init__(self, debug: bool = False):
        self.table = SymbolTable(debug=debug)
        self.diags = Diagnostics()
        self.call_graph: Dict[str, Set[str]] = {}
        self.debug = debug

    def analyze(self, program: Program):
        self._definition_pass(program)
        self._semantic_pass(program)
        self._detect_recursion()
        return self.diags

    def _definition_pass(self, program: Program):
        for proc in program.procedures:
            proc_sym = Symbol(
                name=proc.name,
                kind="proc",
                scope="main",
                proc_node=proc,
                params=[(p.mode, p.name) for p in proc.params]
            )
            try:
                self.table.declare_proc(proc_sym)
            except ValueError as e:
                self.diags.add(str(e))

        for d in program.main.declarations:
            if d.range:
                lo, hi = d.range
                if lo > hi:
                    self.diags.add(f"Array '{d.name}' declared with bad range [{lo}:{hi}] in main")
                    arr_range = (lo, hi)
                else:
                    arr_range = (lo, hi)
                s = Symbol(name=d.name, kind="array", scope="main", array_range=arr_range)
            else:
                s = Symbol(name=d.name, kind="var", scope="main")
            try:
                self.table.declare(s)
            except ValueError as e:
                self.diags.add(str(e))

    def _semantic_pass(self, program: Program):
        for proc in program.procedures:
            self._enter_proc(proc)
        self._enter_main(program.main)

    def _enter_proc(self, proc: Procedure):
            self.call_graph.setdefault(proc.name, set())
            self.table.push_scope(proc.name)

            assigned: Set[str] = set()

            for p in proc.params:
                raw_mode = p.mode
                mode = None
                if isinstance(raw_mode, str):
                    mode = raw_mode
                elif isinstance(raw_mode, Token):
                    mode = str(raw_mode.value)
                elif isinstance(raw_mode, LarkTree) and getattr(raw_mode, "children", None):
                    first = raw_mode.children[0]
                    if isinstance(first, Token):
                        mode = str(first.value)
                    else:
                        mode = str(first)
                else:
                    if raw_mode is not None:
                        try:
                            mode = str(raw_mode)
                        except Exception:
                            mode = None

                s = Symbol(name=p.name, kind="param", scope=proc.name, mode=mode)
                try:
                    self.table.declare(s)
                    if mode != "O":  
                        s.assigned = True
                        assigned.add(s.name)
                except ValueError as e:
                    self.diags.add(str(e))

            for d in proc.declarations:
                if d.range:
                    lo, hi = d.range
                    if lo > hi:
                        self.diags.add(f"Array '{d.name}' declared with bad range [{lo}:{hi}] in procedure {proc.name}")
                        arr_range = (lo, hi)
                    else:
                        arr_range = (lo, hi)
                    s = Symbol(name=d.name, kind="array", scope=proc.name, array_range=arr_range)
                else:
                    s = Symbol(name=d.name, kind="var", scope=proc.name)
                try:
                    self.table.declare(s)
                except ValueError as e:
                    self.diags.add(str(e))

            self._walk_commands(proc.commands, current_proc=proc.name, assigned=assigned, for_iter=None)

            self.table.pop_scope()

    def _enter_main(self, main: Main):
        self.table.push_scope("main")
        assigned: Set[str] = set()
        self._walk_commands(main.commands, current_proc="main", assigned=assigned, for_iter=None)
        self.table.pop_scope()

    def _walk_commands(self, commands: List[Command], current_proc: str, assigned: Set[str], for_iter: Optional[str]):
            for cmd in commands:
                if isinstance(cmd, Assign):
                    self._handle_assign(cmd, current_proc, assigned, for_iter)

                elif isinstance(cmd, IfThen):
                    self._walk_condition(cmd.cond, current_proc, assigned)
                    
                    branch_assigned = set(assigned)
                    self._walk_commands(cmd.then_cmds, current_proc, branch_assigned, for_iter)

                elif isinstance(cmd, IfElse):
                    self._walk_condition(cmd.cond, current_proc, assigned)

                    true_assigned = set(assigned)
                    false_assigned = set(assigned)

                    self._walk_commands(cmd.then_cmds, current_proc, true_assigned, for_iter)
                    self._walk_commands(cmd.else_cmds, current_proc, false_assigned, for_iter)

                    assigned.clear()
                    assigned.update(true_assigned.intersection(false_assigned))

                elif isinstance(cmd, WhileDo):
                    self._walk_condition(cmd.cond, current_proc, assigned)

                    body_assigned = set(assigned)
                    self._walk_commands(cmd.body, current_proc, body_assigned, for_iter)

                elif isinstance(cmd, RepeatUntil):
                    body_assigned = set(assigned)
                    self._walk_commands(cmd.body, current_proc, body_assigned, for_iter)
                    self._walk_condition(cmd.cond, current_proc, body_assigned)
                    
                    assigned.update(body_assigned)

                elif isinstance(cmd, ForLoop):
                    self._walk_value(cmd.frm, current_proc, assigned)
                    self._walk_value(cmd.to, current_proc, assigned)

                    self.table.push_scope(f"loop_{cmd.iter_name}")
                    
                    it_sym = Symbol(name=cmd.iter_name, kind="var", scope=current_proc) 
                    it_sym.assigned = True 
                    try:
                        self.table.declare(it_sym)
                    except ValueError:
                        self.diags.add(f"Redeclaration of iterator '{cmd.iter_name}'")

                    body_assigned = set(assigned)
                    body_assigned.add(cmd.iter_name)

                    self._walk_commands(cmd.body, current_proc, body_assigned, for_iter=cmd.iter_name)

                    self.table.pop_scope()
                    
                elif isinstance(cmd, ProcCall):
                    self._handle_proc_call(cmd, current_proc, assigned)

                elif isinstance(cmd, Read):
                    self._handle_read(cmd, current_proc, assigned, for_iter)

                elif isinstance(cmd, Write):
                    self._walk_value(cmd.value, current_proc, assigned)

                else:
                    pass

    def _walk_condition(self, cond: Condition, current_proc: str, assigned: Set[str]):
        self._walk_value(cond.left, current_proc, assigned)
        self._walk_value(cond.right, current_proc, assigned)

    def _handle_assign(self, cmd: Assign, current_proc: str, assigned: Set[str], for_iter: Optional[str]):
        target = cmd.target
        target_name = target.name

        if for_iter is not None and target_name == for_iter:
            self.diags.add(f"Cannot assign to FOR iterator '{for_iter}' inside its body")

        sym = self._resolve_name(target_name, current_proc)
        if sym is None:
            self.diags.add(f"Assignment to undeclared symbol '{target_name}' in scope '{current_proc}'")
        else:
            if sym.kind == "param" and sym.mode == "I":
                self.diags.add(f"Cannot assign to I-mode parameter '{target_name}' in procedure '{current_proc}'")
            sym.assigned = True
            assigned.add(target_name)

        self._walk_expression(cmd.expr, current_proc, assigned)

    def _handle_read(self, cmd: Read, current_proc: str, assigned: Set[str], for_iter: Optional[str]):
            target = cmd.target
            name = target.name
            
            if for_iter is not None and name == for_iter:
                self.diags.add(f"Cannot modify FOR iterator '{name}' via READ inside loop")

            sym = self._resolve_name(name, current_proc)
            if sym is None:
                self.diags.add(f"READ to undeclared symbol '{name}' in '{current_proc}'")
                return
                
            if target.index is not None and isinstance(target.index, str):
                idx_name = target.index
                self._check_initialized(idx_name, current_proc, assigned, context="array index")

            sym.assigned = True
            assigned.add(name)

    def _check_initialized(self, name: str, current_proc: str, assigned: Set[str], context: str):
        if name not in assigned:
            self.diags.add(f"Variable '{name}' used in {context} is not initialized in '{current_proc}'")
    
    def _handle_proc_call(self, cmd: ProcCall, current_proc: str, assigned: Set[str]):
            callee = cmd.name
            callee_sym = self.table.get_proc_symbol(callee)
            
            if callee_sym is None:
                self.diags.add(f"Call to undefined procedure '{callee}' in '{current_proc}'")
                return

            caller_idx = -1
            if current_proc != "main":
                caller_sym = self.table.get_proc_symbol(current_proc)
                caller_idx = caller_sym.proc_index if caller_sym else -1
            
            if current_proc != "main" and callee_sym.proc_index is not None:
                if callee_sym.proc_index >= caller_idx:
                    self.diags.add(f"Procedure '{callee}' called before its definition (relative to '{current_proc}')")

            formal_params = callee_sym.params or []
            if len(formal_params) != len(cmd.args):
                self.diags.add(f"Procedure '{callee}' expects {len(formal_params)} args but got {len(cmd.args)}")
                return

            caller_key = current_proc
            self.call_graph.setdefault(caller_key, set()).add(callee)

            for (formal_mode, formal_name), actual in zip(formal_params, cmd.args):
                actual_name = actual if isinstance(actual, str) else actual.name
                
                actual_sym = None
                if current_proc == "main":
                    actual_sym = self.table.lookup(actual_name, allow_globals_from_proc=True)
                else:
                    actual_sym = self.table.lookup_current(actual_name)

                if actual_sym is None:
                    self.diags.add(f"Variable '{actual_name}' passed to '{callee}' is not declared in '{current_proc}'")
                    continue

                if formal_mode == "T":
                    if actual_sym.kind != "array":
                        self.diags.add(f"Formal param '{formal_name}' expects an Array (T), but '{actual_name}' is a {actual_sym.kind}")
                    continue
                else:
                    if actual_sym.kind == "array":
                        self.diags.add(f"Formal param '{formal_name}' expects a variable, but '{actual_name}' is an Array")
                        continue

                if actual_sym.kind == "param":
                    caller_mode = actual_sym.mode
                    if caller_mode == "I" and formal_mode != "I":
                        self.diags.add(f"Cannot pass Read-Only parameter '{actual_name}' (I) to Read-Write/Output parameter '{formal_name}'")
                    
                    pass 

                reads_value = (formal_mode == "I" or formal_mode is None)
                
                if reads_value:
                    if actual_name not in assigned:
                        self.diags.add(f"Variable '{actual_name}' passed to input parameter '{formal_name}' of '{callee}' might be uninitialized")
                
                writes_value = (formal_mode == "O" or formal_mode is None)
                
                if writes_value:
                    assigned.add(actual_name)
                    actual_sym.assigned = True
    def _walk_expression(self, expr: Expression, current_proc: str, assigned: Set[str]):
        self._walk_value(expr.left, current_proc, assigned)
        if expr.op and expr.right:
            self._walk_value(expr.right, current_proc, assigned)

    def _walk_value(self, value: Value, current_proc: str, assigned: Set[str]):
        if value is None:
            return
        if value.number is not None:
            return
        if value.identifier is not None:
            name = value.identifier.name
            sym = self._resolve_name(name, current_proc)
            if sym is None:
                self.diags.add(f"Use of undeclared symbol '{name}' in '{current_proc}'")
                return
            if sym.kind == "param" and sym.mode == "O" and name not in assigned:
                self.diags.add(f"Use of O-parameter '{name}' before it's assigned in procedure '{current_proc}'")
            sym.used = True

    def _resolve_name(self, name: str, current_proc: str) -> Optional[Symbol]:
            is_main = (current_proc == "main")
            return self.table.lookup(name, allow_globals_from_proc=is_main)

    def _detect_recursion(self):
        visited = {}
        stack = []

        def dfs(node: str) -> bool:
            visited[node] = 1
            stack.append(node)
            for neigh in self.call_graph.get(node, ()):
                if visited.get(neigh, 0) == 0:
                    if dfs(neigh):
                        return True
                elif visited.get(neigh) == 1:
                    cycle = stack[stack.index(neigh):] + [neigh]
                    self.diags.add(f"Recursion detected in call chain: {' -> '.join(cycle)}")
                    return True
            stack.pop()
            visited[node] = 2
            return False

        for node in list(self.call_graph.keys()):
            if visited.get(node, 0) == 0:
                if dfs(node):
                    pass
