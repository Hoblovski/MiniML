from collections import namedtuple

from ..utils import *
from ..common import *
from .ast import ASTNode

class ExprNode(ASTNode):
    def __init__(self, chs:[ASTNode], ctx):
        super().__init__(chs, ctx=ctx)

class TyNode(ASTNode):
    def __init__(self, ctx, base:'TyNode', rhs:'TyNode'=None):
        # base can be TyNode or str
        super().__init__((base, rhs), ctx=ctx)
        self.setAccessors('base', 'rhs')

class TopNode(ASTNode):
    def __init__(self, ctx, expr:ExprNode):
        super().__init__((expr,), ctx=ctx)
        self.setAccessors('expr')

class LamNode(ExprNode):
    def __init__(self, ctx, name:str, ty:TyNode, body:ExprNode):
        super().__init__((name, ty, body), ctx=ctx)
        self.setAccessors('name', 'ty', 'body')

class SeqNode(ExprNode):
    def __init__(self, ctx, subs:[ExprNode]):
        super().__init__(subs, ctx=ctx)

class AppNode(ExprNode):
    def __init__(self, ctx, fn:ExprNode, arg:ExprNode):
        super().__init__((fn, arg), ctx=ctx)
        self.setAccessors('fn', 'arg')

class LitNode(ExprNode):
    def __init__(self, ctx, val:int):
        super().__init__((val,), ctx=ctx)
        self.setAccessors('val')

class VarRefNode(ExprNode):
    def __init__(self, ctx, name:str):
        super().__init__((name,), ctx=ctx)
        self.setAccessors('name')

LetRecArm = namedtuple('LetRecArm', ('name', 'arg', 'argTy', 'val'))
class LetRecNode(ExprNode):
    def __init__(self, ctx, arms:[LetRecArm], body:ExprNode):
        super().__init__((arms, body), ctx=ctx)
        self.setAccessors('arms', 'body')

class BuiltinNode(ExprNode):
    def __init__(self, ctx, name:str):
        assert name in AllBuiltins
        super().__init__((name,), ctx=ctx)
        self.setAccessors('name')

class IteNode(ExprNode):
    def __init__(self, ctx, cond:ExprNode, tr:ExprNode, fl:ExprNode):
        super().__init__((cond, tr, fl), ctx=ctx)
        self.setAccessors('cond', 'tr', 'fl')

class BinOpNode(ExprNode):
    def __init__(self, ctx, lhs:ExprNode, op:str, rhs:ExprNode):
        assert op in LegalBinOps
        super().__init__((lhs, op, rhs), ctx=ctx)
        self.setAccessors('lhs', 'op', 'rhs')

class UnaOpNode(ExprNode):
    def __init__(self, ctx, op:str, sub:ExprNode):
        assert op in LegalUnaOps
        super().__init__((op, sub), ctx=ctx)
        self.setAccessors('op', 'sub')

