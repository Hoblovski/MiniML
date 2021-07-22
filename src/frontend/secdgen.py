from ..common import *
from ..utils import *

from .ast import *
from .secdinstrs import *

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
        self.instrs['main'] = self(n.expr) + [HaltInstr()]
        return self

    def emit(self, fmt='secdi'):
        assert fmt in {'secdi', 'c'}
        if fmt == 'secdi':
            def f(instrs):
                instrs = [i.fmtSECD() for i in instrs]
                return '\n    '.join(['']+instrs)
            return '\n\n\n'.join(f'{label}:{f(instrs)}'
                    for label, instrs in self.instrs.items())
        elif fmt == 'c':
            HEADER = '#include <c_backend.h>\n\n'
            def f(instrs):
                instrs = [i.fmtC() for i in instrs]
                return '\n    '.join(['']+instrs)
            return HEADER + '\n\n\n'.join(f'void {label}(void){{{f(instrs)}\n}}'
                    for label, instrs in self.instrs.items())

    def visitSeq(self, n):
        # each semicolon discards result of its lhs
        return joinlist([PopInstr(1)], self.visitChildren(n))

    def visitApp(self, n):
        return self(n.fn) + self(n.arg) + [ApplyInstr()]

    def visitLit(self, n):
        return [ConstInstr(n.val)]

    def visitNVarRef(self, n):
        return [AccessInstr(n.idx)]

    def visitNClosRef(self, n):
        return [AccessInstr(n.idx), FocusInstr(n.sub)]

    def visitNLam(self, n):
        lamLabel = self.newLabel('lam')
        self.instrs[lamLabel] = self(n.body) + [ReturnInstr()]
        return [ClosureInstr(lamLabel)]

    def visitNLetRecArm(self, n):
        closLabel = self.newLabel('clos')
        self.instrs[closLabel] = self(n.val) + [ReturnInstr()]
        return closLabel

    def visitLetRec(self, n):
        arms = [self(arm) for arm in n.arms]
        return [ClosuresInstr(arms)] + self(n.body)

    def visitBuiltin(self, n):
        return [BuiltinInstr(n.name)]

    def visitIte(self, n):
        cond, tr, fl = self(n.cond), self(n.tr), self(n.fl)
        l1, l2, l3 = self.newLabel('tr'), self.newLabel('fl'), self.newLabel('end')
        return cond + [BranchInstr('brfl', l2), LabelInstr(l1)] +\
            tr + [BranchInstr('br', l3), LabelInstr(l2)] + fl + [LabelInstr(l3)]

    def visitBinOp(self, n):
        lhs, rhs = self(n.lhs), self(n.rhs)
        return lhs + rhs + [BinaryInstr(n.op)]

    def visitUnaOp(self, n):
        sub = self(n.sub)
        return sub + [UnaryInstr(n.op)]

