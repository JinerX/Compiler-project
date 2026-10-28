# Project
This is an implementation of a compiler which translates a custom language into a custom assembler-like language.

This is a part of my curriculum at Wroclaw University of Science and Technology.

example of `.imp` program:
```
PROCEDURE gcd(I a,I b,O c) IS
  x,y
IN
  x:=a;
  y:=b;
  WHILE y>0 DO
    IF x>=y THEN 
      x:=x-y;
    ELSE 
      x:=x+y;
      y:=x-y;
      x:=x-y;    
    ENDIF
  ENDWHILE
  c:=x;
END

PROGRAM IS
  a,b,c,d,x,y,z
IN
  READ a;
  READ b;
  READ c;
  READ d;
  gcd(a,b,x);
  gcd(c,d,y);
  gcd(x,y,z);
  WRITE z;
END
```

example of the corresponding `.mw` program:
```
JUMP 43	# skok do programu
STORE 0	# gcd
LOAD 1	# x:=a
RLOAD a
STORE 4
LOAD 2	# y:=b
RLOAD a
STORE 5
LOAD 5	# WHILE
JZERO 37	# skok za ENDWHILE
LOAD 4	# IF x>=y (y-x)
SWP b
LOAD 5
SUB b
JPOS 21	# skok ELSE
LOAD 5	# THEN x:=x-y
SWP b
LOAD 4
SUB b
STORE 4
JUMP 36	# skok za ENDIF
LOAD 5	# ELSE x:=x+y
SWP b
LOAD 4
ADD b
STORE 4
LOAD 5	# y:=x-y
SWP b
LOAD 4
SUB b
STORE 5
LOAD 5	# x:=x-y
SWP b
LOAD 4
SUB b
STORE 4
JUMP 8	# ENDWHILE
LOAD 3	# c:=x
SWP b
LOAD 4
RSTORE b
LOAD 0	# return
RTRN
READ	# READ a
STORE 6
READ	# READ b
STORE 7
READ	# READ c
STORE 8
READ	# READ d
STORE 9
RST a	# call gcd(a,b,x)
INC a
SHL a
INC a
SHL a
STORE 1
INC a
STORE 2
INC a
INC a
INC a
STORE 3
CALL 1
RST a	# call gcd(c,d,y)
INC a
SHL a
SHL a
SHL a
STORE 1
INC a
STORE 2
INC a
INC a
STORE 3
CALL 1
RST a	# call gcd(x,y,z)
INC a
SHL a
SHL a
INC a
SHL a
STORE 1
INC a
STORE 2
INC a
STORE 3
CALL 1
LOAD 12	# write z
WRITE
HALT
```

those particular examples have been sourced from my professor: Maciej Gębala 
https://cs.pwr.edu.pl/gebala/

To start the program:

Requires python programming language
```
python3 -m venv venv
source venv/bin/activate
pip3 install lark
```

Then it can be executed:
`python3 main.py <in_file.imp> <out_file.mr>`




