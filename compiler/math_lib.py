
REG1 = "__math_reg1"
REG2 = "__math_reg2"
RES  = "__math_res"
RET  = "__math_ret"
TMP  = "__math_tmp"
MULT = "__math_mult"

MUL_ASM = """
__lib_mul:
    STORE {ret}
    RST a
    STORE {res}

__mul_loop:
    LOAD {reg2}
    JZERO @__mul_end

    # Check if reg2 is Odd
    # We need to calculate: reg2 - ((reg2 / 2) * 2)
    # 1. Store reg2 in c
    LOAD {reg2}
    SWP c
    
    # 2. Calculate (reg2 / 2) * 2 in a
    LOAD {reg2}
    SHR a
    SHL a
    
    # 3. Calculate diff: c (reg2) - a (floored)
    SWP c       # a = reg2, c = floored
    SUB c       # a = reg2 - floored (0 or 1)
    
    JZERO @__mul_even

    # If Odd: res = res + reg1
    LOAD {res}
    SWP b
    LOAD {reg1}
    ADD b
    STORE {res}

__mul_even:
    # reg1 = reg1 * 2 (Doubling)
    LOAD {reg1}
    SHL a
    STORE {reg1}

    # reg2 = reg2 / 2 (Halving)
    LOAD {reg2}
    SHR a
    STORE {reg2}

    JUMP @__mul_loop

__mul_end:
    LOAD {ret}
    RTRN
""".format(reg1=REG1, reg2=REG2, res=RES, ret=RET)

# Assembly for Division (a / b) and Modulo (a % b)
DIV_ASM = """
__lib_div:
    STORE {ret}
    RST a
    STORE {res}
    
    # Check Div by 0
    LOAD {reg2}
    JZERO @__div_end

    # Check if divisor > dividend
    LOAD {reg2}
    SWP b
    LOAD {reg1}
    SWP b
    SUB b
    JPOS @__div_end

    # Init: tmp = reg2, mult = 1
    LOAD {reg2}
    STORE {tmp}
    RST a
    INC a
    STORE {mult}

__div_scale_up:
    LOAD {tmp}
    SWP b
    LOAD {reg1}
    SWP b
    SUB b
    JPOS @__div_scale_down
    
    LOAD {tmp}
    SHL a
    STORE {tmp}
    
    LOAD {mult}
    SHL a
    STORE {mult}
    
    JUMP @__div_scale_up

__div_scale_down:
    LOAD {tmp}
    SHR a
    STORE {tmp}
    
    LOAD {mult}
    SHR a
    STORE {mult}

__div_loop:
    LOAD {mult}
    JZERO @__div_end

    # if reg1 >= tmp
    LOAD {tmp}
    SWP b
    LOAD {reg1}
    SWP b
    SUB b
    JPOS @__div_skip

    # reg1 -= tmp
    LOAD {tmp}
    SWP b
    LOAD {reg1}
    SUB b
    STORE {reg1}

    # res += mult
    LOAD {res}
    SWP b
    LOAD {mult}
    ADD b
    STORE {res}

__div_skip:
    LOAD {tmp}
    SHR a
    STORE {tmp}
    
    LOAD {mult}
    SHR a
    STORE {mult}
    
    JUMP @__div_loop

__div_end:
    LOAD {ret}
    RTRN
""".format(reg1=REG1, reg2=REG2, res=RES, ret=RET, tmp=TMP, mult=MULT)