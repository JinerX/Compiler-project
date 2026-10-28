GRAMMAR = r"""
%import common.WS
%ignore WS
COMMENT: /#.*/ 
%ignore COMMENT

PIDENT: /[_a-z]+/
NUM: /\d+/

start: procedures main
procedures: procedure*
procedure: "PROCEDURE" proc_head "IS" declarations? "IN" commands "END"
main: "PROGRAM" "IS" declarations? "IN" commands "END"

commands: command+
command: identifier ":=" expression ";" -> assign
       | "IF" condition "THEN" commands "ELSE" commands "ENDIF" -> if_else
       | "IF" condition "THEN" commands "ENDIF" -> if_then
       | "WHILE" condition "DO" commands "ENDWHILE" -> while_do
       | "REPEAT" commands "UNTIL" condition ";" -> repeat_until
       | "FOR" PIDENT "FROM" value "TO" value "DO" commands "ENDFOR" -> for_to
       | "FOR" PIDENT "FROM" value "DOWNTO" value "DO" commands "ENDFOR" -> for_downto
       | proc_call ";" -> proc_call_stmt
       | "READ" identifier ";" -> read
       | "WRITE" value ";" -> write

proc_head: PIDENT "(" args_decl ")"
proc_call: PIDENT "(" args ")"

declarations: declaration ("," declaration)*
declaration: PIDENT | PIDENT "[" NUM ":" NUM "]"

args_decl: args_decl_item ("," args_decl_item)*
TYPE: "T" | "I" | "O"

args_decl_item: TYPE? PIDENT



args: PIDENT ("," PIDENT)*

expression: value | value "+" value -> add | value "-" value -> sub
          | value "*" value -> mul | value "/" value -> div | value "%" value -> mod

condition: value "=" value -> eq | value "!=" value -> ne
         | value ">" value -> gt | value "<" value -> lt
         | value ">=" value -> ge | value "<=" value -> le

value: NUM -> number | identifier

identifier: PIDENT "[" PIDENT "]" -> arr_ident
          | PIDENT "[" NUM "]" -> arr_const_index
          | PIDENT -> ident
"""
