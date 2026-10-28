from typing import List, Dict, Union
from .ir import *
from .memory import MemoryManager
from .symbols import SymbolTable
from .math_lib import MUL_ASM, DIV_ASM, REG1, REG2, RES, TMP, MULT

class CodeGenerator:
    def __init__(self, memory_manager: MemoryManager, symbol_table: SymbolTable):
        self.mem = memory_manager
        self.sym = symbol_table
        self.code: List[str] = []
        self.labels: Dict[str, int] = {} 
        self.param_queue: List[str] = []
        
        self.param_addrs: set[int] = set()
        for s in self.sym.all_symbols():
            if s.kind == "param":
                if s.scope == "main":
                    mname = s.name
                else:
                    mname = f"{s.scope}__{s.name}"
                try:
                    addr = self.mem.get_address(mname)
                    self.param_addrs.add(addr)
                except ValueError:
                    pass 

    def generate(self, instructions: List[IRInstruction]) -> str:
            self.code = []
            self.labels = {}

            for instr in instructions:
                self._emit_comment(f"# {instr}")
                
                if isinstance(instr, Label):
                    self._handle_label(instr)
                elif isinstance(instr, Read):
                    self._handle_read(instr)
                elif isinstance(instr, Write):
                    self._handle_write(instr)
                elif isinstance(instr, Copy):
                    self._handle_copy(instr)
                elif isinstance(instr, Jump):
                    self._handle_jump(instr)
                elif isinstance(instr, ProcStart):
                    self.labels[instr.name] = len(self.code)
                    ret_var = f"{instr.name}__return_addr"
                    try:
                        addr = self.mem.get_address(ret_var)
                        self._emit(f"STORE {addr}")
                    except ValueError:
                        pass
                elif isinstance(instr, (ProcEnd, Return)):
                    if instr.__class__ == Return:
                        self._handle_return(instr)
                elif isinstance(instr, BinOp):
                    self._handle_bin_op(instr)
                elif isinstance(instr, JumpCond):
                    self._handle_jump_cond(instr)
                elif isinstance(instr, ArraySet):
                    self._handle_array_set(instr)
                elif isinstance(instr, ArrayGet):
                    self._handle_array_get(instr)
                elif isinstance(instr, Param):
                    self._handle_param(instr)
                elif isinstance(instr, Call):
                    self._handle_call(instr)
                else:
                    self._emit_comment(f"# TODO: Implement {type(instr).__name__}")

            self._emit("HALT")
            
            # --- Append Math Lib ---
            addr_map = {
                REG1: self.mem.get_address(REG1),
                REG2: self.mem.get_address(REG2),
                RES:  self.mem.get_address(RES),
                "__math_ret": self.mem.get_address("__math_ret"),
                TMP:  self.mem.get_address(TMP),
                MULT: self.mem.get_address(MULT)
            }

            final_asm = MUL_ASM + "\n" + DIV_ASM
            
            for reg_name, addr in addr_map.items():
                final_asm = final_asm.replace(reg_name, str(addr))
                
            math_lines = final_asm.strip().split('\n')
            
            for i, line in enumerate(math_lines):
                clean_line = line.strip()
                if not clean_line: continue
                if clean_line.startswith('#'): continue
                    
                if clean_line.endswith(':'):
                    label_name = clean_line[:-1]
                    self.labels[label_name] = len(self.code)
                else:
                    self.code.append(line)

            resolved_code = []
            for line in self.code:
                parts = line.split()
                new_parts = []
                for part in parts:
                    if part.startswith("@"):
                        label_name = part[1:]
                        if label_name in self.labels:
                            new_parts.append(str(self.labels[label_name]))
                        else:
                            raise ValueError(f"Undefined label: {label_name}")
                    else:
                        new_parts.append(part)
                resolved_code.append(" ".join(new_parts))

            return "\n".join(resolved_code)

    def _handle_label(self, instr: Label):
        self.labels[instr.name] = len(self.code)

    def _handle_read(self, instr: Read):
        self._emit("READ")
        addr = self.mem.get_address(instr.dest)
        if addr in self.param_addrs:
            self._emit("SWP c")
            self._emit(f"LOAD {addr}")
            self._emit("SWP b")
            self._emit("SWP c")
            self._emit("RSTORE b")
        else:
            self._emit(f"STORE {addr}")

    def _handle_write(self, instr: Write):
        self._load_to_acc(instr.val)
        self._emit("WRITE")

    def _handle_copy(self, instr: Copy):
        self._load_to_acc(instr.src)
        addr = self.mem.get_address(instr.dest)
        if addr in self.param_addrs:
            self._emit("SWP c")
            self._emit(f"LOAD {addr}")
            self._emit("SWP b")
            self._emit("SWP c")
            self._emit("RSTORE b")
        else:
            self._emit(f"STORE {addr}")

    def _handle_jump(self, instr: Jump):
        self._emit(f"JUMP @{instr.target}")

    def _handle_param(self, instr: Param):
        if isinstance(instr.value, str):
            self.param_queue.append(instr.value)
        else:
            raise ValueError("Constants cannot be passed by reference")

    def _handle_call(self, instr: Call):
        proc_sym = self.sym.get_proc_symbol(instr.proc_name)
        if not proc_sym: raise ValueError(f"Unknown proc {instr.proc_name}")
        
        formal_params = [f"{instr.proc_name}__{pname}" for _, pname in proc_sym.params]
        if len(self.param_queue) != len(formal_params): raise ValueError("Arg mismatch")

        for arg_name, param_name in zip(self.param_queue, formal_params):
            dest_addr = self.mem.get_address(param_name)
            src_addr = self.mem.get_address(arg_name)
            
            if src_addr in self.param_addrs:
                 self._emit(f"LOAD {src_addr}")
            else:
                 self._gen_const(src_addr)
            
            self._emit(f"STORE {dest_addr}")

        self.param_queue = []
        
        ret_var = f"{instr.proc_name}__return_addr"
        self._emit(f"CALL @{instr.proc_name}")

    def _emit(self, asm: str):
        self.code.append(asm)

    def _emit_comment(self, txt: str):
        pass

    def _load_to_acc(self, operand: Union[str, int]):
        if isinstance(operand, int):
            self._gen_const(operand)
        elif isinstance(operand, str):
            addr = self.mem.get_address(operand)
            if addr in self.param_addrs:
                self._emit(f"LOAD {addr}")
                self._emit("SWP b")
                self._emit("RLOAD b")
            else:
                self._emit(f"LOAD {addr}")
    
    def _gen_const(self, value: int):
        self._emit("RST a")
        if value == 0: return
        bin_str = bin(value)[2:] 
        for i, bit in enumerate(bin_str):
            if i > 0: self._emit("SHL a")
            if bit == '1': self._emit("INC a")

    def _handle_bin_op(self, instr: BinOp):
        self._load_to_acc(instr.left)
        
        if instr.op == "+":
            if isinstance(instr.right, int) and instr.right == 1:
                self._emit("INC a")
            else:
                self._emit("SWP c")
                self._load_to_acc(instr.right)
                self._emit("ADD c")
                
        elif instr.op == "-":
            if isinstance(instr.right, int) and instr.right == 1:
                self._emit("DEC a")
            else:
                self._emit("SWP c")
                self._load_to_acc(instr.right)
                self._emit("SWP c")
                self._emit("SUB c")

        elif instr.op == "*":
            self._load_to_acc(instr.left)
            self._emit(f"STORE {self.mem.get_address(REG1)}")
            self._load_to_acc(instr.right)
            self._emit(f"STORE {self.mem.get_address(REG2)}")
            self._emit("CALL @__lib_mul")
            self._emit(f"LOAD {self.mem.get_address(RES)}")
        elif instr.op in ("/", "%"):
            self._load_to_acc(instr.left)
            self._emit(f"STORE {self.mem.get_address(REG1)}")
            self._load_to_acc(instr.right)
            self._emit(f"STORE {self.mem.get_address(REG2)}")
            self._emit("CALL @__lib_div")
            if instr.op == "/":
                self._emit(f"LOAD {self.mem.get_address(RES)}")
            else:
                self._emit(f"LOAD {self.mem.get_address(REG1)}")
        
        dest_addr = self.mem.get_address(instr.dest)
        if dest_addr in self.param_addrs:
            self._emit("SWP c")
            self._emit(f"LOAD {dest_addr}")
            self._emit("SWP b")
            self._emit("SWP c")
            self._emit("RSTORE b")
        else:
            self._emit(f"STORE {dest_addr}")

    def _handle_jump_cond(self, instr: JumpCond):
        if instr.op == ">":
            self._load_to_acc(instr.left)
            self._emit("SWP c")
            self._load_to_acc(instr.right)
            self._emit("SWP c")
            self._emit("SUB c")
            self._emit(f"JPOS @{instr.target}")
        elif instr.op == "<":
            self._load_to_acc(instr.right)
            self._emit("SWP c")
            self._load_to_acc(instr.left)
            self._emit("SWP c")
            self._emit("SUB c")
            self._emit(f"JPOS @{instr.target}")
        elif instr.op == ">=":
            self._load_to_acc(instr.right)
            self._emit("SWP c")
            self._load_to_acc(instr.left)
            self._emit("SWP c")
            self._emit("SUB c")
            self._emit(f"JZERO @{instr.target}")
        elif instr.op == "<=":
            self._load_to_acc(instr.left)
            self._emit("SWP c")
            self._load_to_acc(instr.right)
            self._emit("SWP c")
            self._emit("SUB c")
            self._emit(f"JZERO @{instr.target}")
        elif instr.op == "=":
            self._load_to_acc(instr.left)
            self._emit("SWP c")
            self._load_to_acc(instr.right)
            self._emit("SWP c")
            self._emit("SUB c")
            self._emit("SWP d")
            
            self._load_to_acc(instr.right)
            self._emit("SWP c")
            self._load_to_acc(instr.left)
            self._emit("SWP c")
            self._emit("SUB c")
            self._emit("ADD d")
            self._emit(f"JZERO @{instr.target}")
        elif instr.op == "!=":
            self._load_to_acc(instr.left)
            self._emit("SWP c")
            self._load_to_acc(instr.right)
            self._emit("SWP c")
            self._emit("SUB c")
            self._emit("SWP d")
            
            self._load_to_acc(instr.right)
            self._emit("SWP c")
            self._load_to_acc(instr.left)
            self._emit("SWP c")
            self._emit("SUB c")
            self._emit("ADD d")
            self._emit(f"JPOS @{instr.target}")

    def _load_effective_address(self, name: str, index_operand: Union[str, int]):
        self._load_to_acc(index_operand)
        self._emit("SWP b")
        base_addr_loc = self.mem.get_address(name)
        if base_addr_loc in self.param_addrs:
            self._emit(f"LOAD {base_addr_loc}")
        else:
            self._gen_const(base_addr_loc)
        self._emit("ADD b")
        self._emit("SWP b")

    def _handle_array_set(self, instr: ArraySet):
        self._load_effective_address(instr.name, instr.index)
        self._load_to_acc(instr.src)
        self._emit("RSTORE b")

    def _handle_array_get(self, instr: ArrayGet):
        self._load_effective_address(instr.name, instr.index)
        self._emit("RLOAD b")
        dest_addr = self.mem.get_address(instr.dest)
        self._emit(f"STORE {dest_addr}")

    def _handle_proc_start(self, instr: ProcStart):
        self.labels[instr.name] = len(self.code)
        
        ret_var = f"{instr.name}__return_addr"
        try:
            addr = self.mem.get_address(ret_var)
            self._emit(f"STORE {addr}")
        except ValueError:
            pass

    def _handle_return(self, instr: Return):
        ret_var = f"{instr.proc_name}__return_addr"
        try:
            addr = self.mem.get_address(ret_var)
            self._emit(f"LOAD {addr}")
        except ValueError:
            pass
        
        self._emit("RTRN")