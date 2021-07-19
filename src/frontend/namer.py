"""
Alpha conversion pass. (Not using de brujin)
"""
from .ast import *
from .astnodes import *

##############################################################################

# replaces VarRefNode
IdxVarRefNode = NodeClassFactory('IdxVarRefNode', ('idx', 'sub'))
IdxLamNode = NodeClassFactory('IdxLamNode', ('ty', 'body'))
IdxLetRecArmNode = NodeClassFactory('IdxLetRecArmNode', ('argTy', 'val'))

class NamerVisitor(ASTTransformer):
    """Alpha conversion, capture variable identification"""
    def __init__(self):
        self.vars = []

    def visitVarRef(self, n:VarRefNode):
        name = n.name()
        for i, v in enumerate(self.vars):
            if isinstance(v, str) and v == name:
                return IdxVarRefNode(pos=n.pos, idx=i+1, sub=None)
            if isinstance(v, tuple) and name in v:
                return IdxVarRefNode(pos=n.pos, idx=i+1, sub=v.index(name)+1)
        raise MiniMLLocatedError(n, f'cannot find {n.name()}')

    def visitLam(self, n:LamNode):
        self.vars = [n.name()] + self.vars
        n = IdxLamNode(pos=n.pos, ty=n.ty(), body=self(n.body()))
        self.vars = self.vars[1:]
        return n

    def visitLetRec(self, n:LetRecNode):
        self.vars = [tuple(arm.name() for arm in n.arms())] + self.vars
        newArms = []
        for arm in n.arms():
            self.vars = [arm.arg()] + self.vars
            newArms += [IdxLetRecArmNode(pos=arm.pos, argTy=arm.argTy(), val=self(arm.val()))]
            self.vars = self.vars[1:]
        n.arms(newArms)
        n.body(self(n.body()))
        self.vars = self.vars[len(n.arms()):]
        return n

