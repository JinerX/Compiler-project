from .symbols import SymbolTable, Symbol
from .ir import IRInstruction, Copy, BinOp, JumpCond, ArrayGet, ArraySet, Write, Read, Param, Call
from typing import Dict, List, Set, Union

class MemoryManager:
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.addresses: Dict[str, int] = {}
        self.next_free_address = 0
        
    def allocate(self, ir_instructions: List[IRInstruction]):
        self.addresses.clear()
        self.next_free_address = 0

        self._allocate_symbols()
        self._allocate_temporaries(ir_instructions)
        
        self.addresses["__math_temp"] = self.next_free_address
        self.next_free_address += 1

        math_regs = [
            "__math_reg1", "__math_reg2", "__math_res", "__math_ret",
            "__math_tmp", "__math_mult"
        ]
        for r in math_regs:
            self.addresses[r] = self.next_free_address
            self.next_free_address += 1

    def get_address(self, name: str) -> int:
        if name in self.addresses:
            return self.addresses[name]
        raise ValueError(f"MemoryManager: Symbol '{name}' has no allocated address.")

    def _allocate_symbols(self):
        all_scopes = []
        for i, name in enumerate(self.symbol_table.scope_names):
            all_scopes.append((name, self.symbol_table.scopes[i]))
        all_scopes.extend(self.symbol_table.archived_scopes)
        
        for scope_name, scope in all_scopes:
            sorted_symbols = sorted(scope.values(), key=lambda s: s.name)
            
            for sym in sorted_symbols:
                if sym.kind == "proc":
                    continue 
                
                if sym.scope == "main":
                    mangled_name = sym.name
                else:
                    mangled_name = f"{sym.scope}__{sym.name}"
                
                if mangled_name in self.addresses:
                    continue

                size = 1
                virtual_base_adjustment = 0
                
                if sym.kind == "array" and sym.array_range:
                    low, high = sym.array_range
                    size = high - low + 1
                    virtual_base_adjustment = low
                    
                    if self.next_free_address < low:
                        self.next_free_address = low
                
                real_addr = self.next_free_address
                
                stored_addr = real_addr - virtual_base_adjustment
                
                self.addresses[mangled_name] = stored_addr
                sym.memory_addr = stored_addr
                
                self.next_free_address += size

            if scope_name != "main" and not scope_name.startswith("loop_"):
                ret_var = f"{scope_name}__return_addr"
                if ret_var not in self.addresses:
                    self.addresses[ret_var] = self.next_free_address
                    self.next_free_address += 1
    
    def _allocate_temporaries(self, instructions: List[IRInstruction]):
        temps_found: Set[str] = set()
        def check(op):
            if isinstance(op, str) and op.startswith("__t"):
                temps_found.add(op)

        for instr in instructions:
            if isinstance(instr, Copy):
                check(instr.dest)
                check(instr.src)
            elif isinstance(instr, ArraySet):
                check(instr.name)
                check(instr.index)
                check(instr.src)
            elif isinstance(instr, BinOp):
                check(instr.dest)
                check(instr.left)
                check(instr.right)
            elif isinstance(instr, JumpCond):
                check(instr.left)
                check(instr.right)
            elif isinstance(instr, ArrayGet):
                check(instr.dest)
                check(instr.name)
                check(instr.index)
            elif isinstance(instr, Write):
                check(instr.val)
            elif isinstance(instr, Param):
                check(instr.value)
            elif isinstance(instr, Read):
                check(instr.dest)

        for t in sorted(list(temps_found)):
            if t not in self.addresses:
                self.addresses[t] = self.next_free_address
                self.next_free_address += 1

    def print_memory_map(self):
        print("\n=== Memory Map ===")
        print(f"{'Address':<10} | {'Variable Name'}")
        print("-" * 30)
        sorted_map = sorted(self.addresses.items(), key=lambda item: item[1])
        for name, addr in sorted_map:
            print(f"{addr:<10} | {name}")
        print("-" * 30)
        print(f"Total memory used: {self.next_free_address} cells")
        print("==================\n")