from .ast import *

class SECDGenVisitor(ASTVisitor):
    def joinResults(self, r):
        return '\n'.join(r)

    def _i(self, lines):
        return '    ' + '\n    '.join(lines.split('\n'))

    def __init__(self):
        self.instrs = {}
        self.nclos = 0
        self.noth = 0
        # closure label -> instrs
        self.instrs = {}

    def visitTop(self, n):
        self.instrs['main'] = self(n.expr()) + 'halt\n'
        return '\n\n\n'.join([f'{label}:\n{self._i(instrs)}' for label, instrs in self.instrs.items()])

    def visitIdxLam(self, n):
        self.nclos += 1
        t = self.nclos
        self.instrs[f'p{t}'] = self(n.body()) + 'return\n'
        return f'closure p{t}\n'

    def visitSeq(self, n):
        return '\n'.join(self.visitChildren(n)) + '\n'

    def visitApp(self, n):
        # applyn?
        return self(n.fn()) + self(n.arg()) + 'apply\n'

    def visitLit(self, n):
        return f'const {n.val()}\n'

    def visitIdxVarRef(self, n):
        if n.sub() is None:
            return f'access ${n.idx()}\n'
        else:
            return f'access ${n.idx()}\n' +\
                f'focus {n.sub()}\n'

    def visitIdxLetRecArm(self, n):
        self.nclos += 1
        t = self.nclos
        self.instrs[f'p{t}'] = self(n.val()) + 'return\n'
        return f'p{t}'

    def visitLetRec(self, n):
        arms = [self(arm) for arm in n.arms()]
        return 'closures ' + ' '.join(arms) + '\n' + self(n.body())

    def visitBuiltin(self, n):
        return f'{n.name()}\n'

    def visitIte(self, n):
        t = self.noth
        self.noth += 3
        cond = self(n.cond())
        tr = self(n.tr())
        fl = self(n.fl())
        return f'{cond}' +\
                f'brfl fl{t+1}\n' +\
                f'tr{t}:\n' +\
                f'{tr}' +\
                f'br end{t+2}\n' +\
                f'fl{t+1}:\n' +\
                f'{fl}' +\
                f'end{t+2}:\n'

    def visitBinOp(self, n):
        lhs = self(n.lhs())
        rhs = self(n.rhs())
        op = {'%': 'mod', '-': 'sub', '+': 'add', '*': 'mul', '==': 'eq', '<=': 'le'}[n.op()]
        return lhs + rhs + f'{op}\n'

    def visitUnaOp(self, n):
        assert False

