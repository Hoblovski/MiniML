"""
De brujin representation.
"""
from .ast import *
from .astnodes import *

##############################################################################

spec = """
NLam       : ty body
NVarRef    : idx.
NClosRef    : idx. sub.
NLetRecArm : argTy val
"""

globals().update(createNodes(spec))

class NamerVisitor(ASTTransformer):
    """
    De brujin style alpha conversion
    """
    VisitorName = 'Namer'

    def __init__(self):
        self.vars = []

    def push(self, var):
        self.vars = [var] + self.vars

    def pop(self):
        self.vars = self.vars[1:]

    def find(self, var):
        for i, v in enumerate(self.vars):
            if isinstance(v, str) and v == var:
                return (i, None)
            if isinstance(v, tuple) and var in v:
                return (i, v.index(var))
        return None, None

    def visitVarRef(self, n):
        idx, sub = self.find(n.name)
        if idx is None:
            raise MiniMLLocatedError(n, f'cannot find {n.name}')
        if sub is None:
            return NVarRefNode(pos=n.pos, idx=idx+1)
        else:
            return NClosRefNode(pos=n.pos, idx=idx+1, sub=sub+1)

    def visitLam(self, n):
        self.push(n.name)
        new = NLamNode(pos=n.pos, ty=n.ty, body=self(n.body))
        self.pop()
        return new

    def visitLetRec(self, n):
        self.push(tuple(arm.name for arm in n.arms))
        for i, arm in enumerate(n.arms):
            self.push(arm.arg)
            n.arms[i] = NLetRecArmNode(pos=arm.pos, argTy=arm.argTy, val=self(arm.val))
            self.pop()
        n.body = self(n.body)
        self.pop()
        return n
