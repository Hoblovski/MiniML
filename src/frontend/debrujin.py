"""
Should be done after Namer's alpha conversion pass.

De brujin indices are unstable so only do this pass just before emitting to SECD.
"""
from .ast import *
from .astnodes import *

# New ASTNodes
# idx, sub >= 1.
#   Note that this should correspond to secdi convention.
globals().update(createNodes("""
NLam       : body
NVarRef    : idx.
NClosRef   : idx. sub.
NLetRecArm : val
NLet       : val body

NIdentPtn        :
NTuplePtn        : subs+
"""))

class DeBrujinVisitor(ASTTransformer):
    """
    Convert to de brujin representation.

    Sets all binder names to None, and all VarRef names to integer.
    """
    VisitorName = 'DeBrujin'

    def __init__(self):
        self.vars = []

    def pushVar(self, var):
        self.vars = [var] + self.vars

    def popVar(self, n=1):
        self.vars = self.vars[n:]

    def visitVarRef(self, n):
        for i, v in enumerate(self.vars):
            if isinstance(v, str) and v == n.name:
                return NVarRefNode(pos=n.pos, idx=i+1)
            if isinstance(v, tuple) and n.name in v:
                return NClosRefNode(pos=n.pos, idx=i+1, sub=v.index(n.name)+1)
        raise MiniMLLocatedError(n, f'cannot find {n.name}')

    def visitLam(self, n):
        self.pushVar(n.name)
        del n.name
        new = NLamNode(pos=n.pos, body=self(n.body))
        self.popVar()
        return new

    def visitLetRec(self, n):
        self.pushVar(tuple(arm.fnName for arm in n.arms))
        for i, arm in enumerate(n.arms):
            self.pushVar(arm.argName)
            n.arms[i] = NLetRecArmNode(pos=arm.pos, val=self(arm.val))
            self.popVar()
        n.body = self(n.body)
        self.popVar()
        return n

    def visitLet(self, n):
        val = self(n.val)
        self.pushVar(n.name)
        new = NLetNode(pos=n.pos, val=val, body=self(n.body))
        self.popVar()
        return new
