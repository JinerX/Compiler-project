from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any


@dataclass
class Symbol:
    """
    Single symbol entry.
    - kind: "var" | "array" | "param" | "proc"
    - scope: name of scope (procedure name or "main")
    - mode: for params: None | "I" | "O" | "T"
    - array_range: for arrays (low, high) or None
    - params: for procs: ordered list of (mode,name) or None
    - declared_at: optional (line,col) if you later provide positions
    - assigned/used: simple booleans for flow checks
    """
    name: str
    kind: str
    scope: str
    mode: Optional[str] = None
    array_range: Optional[Tuple[int, int]] = None
    params: Optional[List[Tuple[Optional[str], str]]] = None
    declared_at: Optional[Tuple[int, int]] = None
    memory_addr: Optional[int] = None

    used: bool = False
    assigned: bool = False

    proc_node: Optional[Any] = None
    proc_index: Optional[int] = None


class SymbolTable:

    def __init__(self, debug: bool = False):
        self.scopes: List[Dict[str, Symbol]] = []
        self.scope_names: List[str] = []

        self.archived_scopes: List[Tuple[str, Dict[str, Symbol]]] = [] 

        self.debug = debug
        self.proc_order: List[str] = []
        self.push_scope("main")

    def push_scope(self, name: str):
        if self.debug:
            print(f"[SymbolTable] ENTER SCOPE '{name}'")
            self._print_contents()
        self.scopes.append({})
        self.scope_names.append(name)

    def pop_scope(self):
            if not self.scopes:
                return

            name = self.scope_names[-1]
            scope_content = self.scopes[-1]
            
            if self.debug:
                print(f"[SymbolTable] LEAVE SCOPE '{name}'")
                self._print_contents()
                
            if name != "main":
                self.archived_scopes.append((name, scope_content))

            self.scopes.pop()
            self.scope_names.pop()

    def current_scope_name(self) -> str:
        return self.scope_names[-1] if self.scope_names else "?"

    def current_scope(self) -> Dict[str, Symbol]:
        return self.scopes[-1]

    def declare(self, sym: Symbol):
        scope = self.current_scope()
        if sym.name in scope:
            raise ValueError(f"Duplicate declaration of '{sym.name}' in scope '{self.current_scope_name()}'")
        scope[sym.name] = sym
        return sym

    def declare_proc(self, sym: Symbol):
        scope = self.current_scope()
        if sym.name in scope:
            raise ValueError(f"Duplicate declaration of procedure '{sym.name}'")
        sym.proc_index = len(self.proc_order)
        self.proc_order.append(sym.name)
        scope[sym.name] = sym
        return sym

    def lookup_current(self, name: str) -> Optional[Symbol]:
        scope = self.current_scope()
        return scope.get(name)

    def lookup(self, name: str, allow_globals_from_proc: bool = False) -> Optional[Symbol]:
            for i in range(len(self.scopes) - 1, -1, -1):
                scope = self.scopes[i]
                if i == 0 and not allow_globals_from_proc:
                    return None
                
                if name in scope:
                    return scope[name]
            return None

    def get_proc_symbol(self, name: str) -> Optional[Symbol]:
        main_scope = self.scopes[0]
        s = main_scope.get(name)
        if s and s.kind == "proc":
            return s
        return None

    def all_symbols(self) -> List[Symbol]:
            all_syms = []
            for scope in self.scopes:
                all_syms.extend(scope.values())
            
            for _, scope in self.archived_scopes:
                all_syms.extend(scope.values())
                
            return all_syms

    def _print_contents(self):
        print("[SymbolTable] CURRENT CONTENTS:")
        for idx, sc in enumerate(self.scopes):
            name = self.scope_names[idx]
            print(f"  Scope '{name}':")
            for sym_name, sym in sc.items():
                kind = sym.kind
                mode = f", mode={sym.mode}" if sym.mode is not None else ""
                arr = f", range={sym.array_range}" if sym.array_range else ""
                print(f"    {sym_name}: kind={kind}{mode}{arr}")
        print("[/SymbolTable]\n")
