from copy import deepcopy
from antlr4 import *
from ast import literal_eval
from pprint import pprint

from .debug import *

class MiniMLError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

class MiniMLLocatedError(MiniMLError):
    def __init__(self, n, msg):
        self.msg = f'At {n.pos[0]}, {n.pos[1]}: {msg}'

    def __str__(self):
        return self.msg

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

def asinstance(obj, ty):
    if not isinstance(obj, ty):
        raise TypeError(f'cannot convert {obj} into {ty}')
    return obj

def text(x):
    if isinstance(x, str):
        return x
    try:
        return str(x.getText())
    except AttributeError:
        panic(f'invalid arg to text: {x}, type is {type(x)}')

def ctxPos(ctx):
    if ctx is None:
        return None
    return (ctx.start.line,ctx.start.column)

def flatten(l):
    res = []
    for i in l:
        if isinstance(i, list):
            res += flatten(i)
        else:
            res += [i]
    return res

def revertdict(d):
    return { v: k for k, v in d.items() }

def joinlist(sep, iterable):
    """
        joinlist(['s', '/'], [[3], [5, 6], [7, 8]]) =
        [3, 's', '/', 5, 6, 's', '/', 7, 8]
    """
    res = iterable[0]
    for it in iterable[1:]:
        res += sep
        res += it
    return res

class stacked_dict:
    def __init__(self):
        self._s = [{}]
        self._d = [{}]

    def __getitem__(self, key):
        return self._s[-1][key]

    def __setitem__(self, key, value):
        self._d[-1][key] = self._s[-1][key] = value

    def __contains__(self, key):
        return key in self._s[-1]

    def __len__(self):
        return len(self._s[-1])

    def push(self):
        self._s.append(deepcopy(self._s[-1]))
        self._d.append({})

    def pop(self):
        assert len(self._s) > 1
        self._s.pop()
        self._d.pop()

    def peek(self, last=0):
        return self._d[-1-last]

def noDuplicates(l):
    return len(set(l)) == len(l)

def unreachable():
    raise Exception('unreachable')

def unionsets(l):
    r = set()
    for s in l:
        assert isinstance(s, set)
        r.update(s)
    return r

def unzip(iterable):
    return zip(*iterable)

def joindict(iterable):
    res = deepcopy(iterable[0])
    for it in iterable[1:]:
        res.update(it)
    return res

def joinCont(cont1, cont2):
    def cont(k):
        return cont1(cont2(k))
    return cont

def idfun(x):
    return x

def rfold(f, l, a):
    it = reversed(l)
    for b in it:
        a = f(b, a)
    return a

