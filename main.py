from compiler.transformer import parse_program
from compiler.semantic import SemanticAnalyzer
from compiler.ir_generator import IRGenerator
from compiler.memory import MemoryManager
from compiler.codegen import CodeGenerator
import sys

if len(sys.argv) != 3:
    print("invalid arguments")
    sys.exit(1)

file_path = sys.argv[1]
out_path = sys.argv[2]

with open(file_path, "r", encoding="utf-8") as f:
    code = f.read() 


print("--- Pipeline ---")
prog = parse_program(code)
analyzer = SemanticAnalyzer()
analyzer.analyze(prog)
generator = IRGenerator()
instructions = generator.generate(prog)
memory_mgr = MemoryManager(analyzer.table)
memory_mgr.allocate(instructions)
codegen = CodeGenerator(memory_mgr, analyzer.table)
vm_code = codegen.generate(instructions)

memory_mgr.print_memory_map()

# print("[VM CODE]")
# print(vm_code)

with open(out_path, "w") as f:
    f.write(vm_code)