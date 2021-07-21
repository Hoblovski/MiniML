from .utils import *

LegalUnaOps = {
        '-',
}

LegalBinOps = {
        '*', '/', '%',
        '+', '-',
        '>', '<', '>=', '<=', '==', '!=',
}

AllBuiltins = {
        'println',
}

LegalBrOps = {
        "br",
        "beqz", "bnez", "beq", "bne",
        "ble", "blt", "bge", "bgt"
}

relOpToStr = {
    '==': 'eq', '!=': 'ne', '>': 'gt',
    '<': 'lt', '>=': 'ge', '<=': 'le'
}

relStrToOp = revertdict(relOpToStr)

binOpToStr = {
    '+': 'add', '-': 'sub', '*': 'mul', '/': 'div', '%': 'mod',
    **relOpToStr
}

binStrToOp = revertdict(binOpToStr)

unaOpToStr = {
    '-': 'neg'
}

unaStrToOp = revertdict(unaOpToStr)
