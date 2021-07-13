"""
Namer converts the functional program to de brujin
"""
from .ast import *

##############################################################################

class NamedLamNode(LamNode):
    def __init__(self, pos, ty, body):
        ASTNode.__init__(self, (ty, body), pos=pos)
        self.setAccessors('ty', 'body')

    def acceptFormattedPrint(self, visitor):
        bodyStr = visitor(self.body())
        res = f'Lam<{visitor(self.ty())}>'
        if len(bodyStr) < 40:
            return f'({res} {bodyStr})'
        else:
            return f'({res}\n{visitor._i(bodyStr)})'

class NamedVarRefNode(VarRefNode):
    def __init__(self, pos, idx):
        ASTNode.__init__(self, (idx,), pos=pos)
        self.setAccessors('idx')

    def acceptFormattedPrint(self, visitor):
        return f'${self.idx()}'

##############################################################################

class Namer(ASTTransformer):
    """De brujin transformation"""
    def __init__(self):
        self.vars = [] # index from 1

    def addvar(self, v):
        self.vars.append(v)

    def delvar(self):
        self.vars.pop()

    def getvar(self, v):
        # get the de brujin index for v (rfind)
        for i in range(len(self.vars)-1, -1, -1):
            if self.vars[i] == v:
                return len(self.vars)-i
        return -1

    # @Example: hooking visit
    def visit(self, node):
        if isinstance(node, ASTNode):
            return super().visit(node)
        else:
            return node

    def visitVarRef(self, n):
        return NamedVarRefNode(n.pos, self.getvar(n.name()))

    def visitLam(self, n):
        self.addvar(n.name())
        res = NamedLamNode(n.pos, self(n.ty()), self(n.body()))
        self.delvar()
        return res

