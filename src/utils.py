from copy import deepcopy
from antlr4 import *
from ast import literal_eval

DebugAllowSugarLetExpr = False

class MiniMLError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

def getSymbolicNames(Lexer:type):
    intAttrs = set([a for a in dir(Lexer) if type(getattr(Lexer, a)) is int])
    ignoreAttrs = { "DEFAULT_MODE", "DEFAULT_TOKEN_CHANNEL", "HIDDEN",
            "MAX_CHAR_VALUE", "MIN_CHAR_VALUE", "MORE", "SKIP" }
    symNames = intAttrs - ignoreAttrs
    return {getattr(Lexer, a): a for a in symNames}

def dumpLexerTokens(lexer):
    symNames = getSymbolicNames(type(lexer))
    print(f"{'Token':<10} {'Text':<20}")
    print(f"{'-'*9:<10} {'-'*19:<20}")
    for token in lexer.getAllTokens():
        symName = symNames[token.type]
        print(f"{symName:<10} {token.text:<40}")

def panic(msg):
    print('================================')
    print('==== PANIC =====================')
    print(msg)
    raise MiniMLError('compiler panicked')

def text(x):
    if isinstance(x, str):
        return x
    try:
        return str(x.getText())
    except AttributeError:
        panic(f'invalid arg to text: {x}, type is {type(x)}')

def ctxPos(ctx):
    return (ctx.start.line,ctx.start.column)

