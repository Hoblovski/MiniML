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
        'br', 'brfl'
}

AllBaseTypes = {
        'int', 'bool', 'unit'
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
