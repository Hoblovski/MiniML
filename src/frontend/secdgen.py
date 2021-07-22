from ..common import *
from ..utils import *

from .ast import *

class SECDGenVisitor(ASTVisitor):
    """
    Generate SECD.
    """
    VisitorName = 'SECDGen'

    def newLabel(self, namespace):
        idx = self.labelIdx.get(namespace, 0)
        self.labelIdx[namespace] = idx + 1
        return f'{namespace}{idx}'

    def joinResults(self, n, chRes):
        return flatten(chRes)

    def __init__(self):
        self.instrs = {}
        self.labelIdx = {}

    def visitTop(self, n):
        self.instrs['main'] = self(n.expr) + ['halt']
        def f(instrs):
            return '\n    '.join(['']+instrs)
        return '\n\n\n'.join(f'{label}:{f(instrs)}'
                for label, instrs in self.instrs.items())

    def visitSeq(self, n):
        # each semicolon discards result of its lhs
        return joinlist(['pop 1'], self.visitChildren(n))

    def visitApp(self, n):
        return self(n.fn) + self(n.arg) + ['apply']

    def visitLit(self, n):
        return [f'const {n.val}']

    def visitNVarRef(self, n):
        return [f'access ${n.idx}']

    def visitNClosRef(self, n):
        return [f'access ${n.idx}', f'focus {n.sub}']

    def visitNLam(self, n):
        lamLabel = self.newLabel('lam')
        self.instrs[lamLabel] = self(n.body) + ['return']
        return [f'closure {lamLabel}']

    def visitNLetRecArm(self, n):
        closLabel = self.newLabel('clos')
        self.instrs[closLabel] = self(n.val) + ['return']
        return closLabel

    def visitLetRec(self, n):
        arms = [self(arm) for arm in n.arms]
        return ['closures ' + ' '.join(arms)] + self(n.body)

    def visitBuiltin(self, n):
        return [f'builtin {n.name}']

    def visitIte(self, n):
        cond, tr, fl = self(n.cond), self(n.tr), self(n.fl)
        l1, l2, l3 = self.newLabel('tr'), self.newLabel('fl'), self.newLabel('end')
        return cond + [f'brfl {l2}', f'{l1}:'] +\
            tr + [f'br {l3}', f'{l2}:'] + fl + [f'{l3}:']

    def visitBinOp(self, n):
        lhs, rhs = self(n.lhs), self(n.rhs)
        return lhs + rhs + [binOpToStr[n.op]]

    def visitUnaOp(self, n):
        sub = self(n.sub)
        return sub + [unaOpToStr[n.op]]

