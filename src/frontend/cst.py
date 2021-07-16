from ..utils import *
from ..common import *
from ..generated.MiniMLParser import MiniMLParser
from ..generated.MiniMLVisitor import MiniMLVisitor
from .astnodes import *

def _accept(ctx, visitor):
    if ctx is None:
        return None
    return ctx.accept(visitor)

class ConstructASTVisitor(MiniMLVisitor):
    """
    Note this class visits the *CST*.
    """

    def __init__(self):
        pass

    def visitTop(self, ctx:MiniMLParser.TopContext):
        return TopNode(ctx,
                expr=ctx.expr().accept(self))

    def visitLet1(self, ctx:MiniMLParser.Let1Context):
        return LetRecNode(ctx,
                arms=ctx.letRecArms().accept(self),
                body=ctx.expr().accept(self))

    def visitLetRecArms(self, ctx:MiniMLParser.LetRecArmsContext):
        return [arm.accept(self) for arm in ctx.letRecArm()]

    def visitLetRecArm(self, ctx:MiniMLParser.LetRecArmContext):
        return LetRecArm(
                name=text(ctx.Ident(0)), arg=text(ctx.Ident(1)),
                argTy=_accept(ctx.ty(), self), val=ctx.expr().accept(self))

    def visitLet2(self, ctx:MiniMLParser.Let2Context):
        # Desugar: let X: T = E0 in E1  =>   (\\X:T -> E1)(E0)
        return AppNode(ctx,
                fn=LamNode(ctx,
                    name=text(ctx.Ident()), ty=_accept(ctx.ty(), self),
                    body=ctx.expr(1).accept(self)),
                arg=ctx.expr(0).accept(self))

    def visitLam1(self, ctx:MiniMLParser.Lam1Context):
        return LamNode(ctx,
                name=text(ctx.Ident()), ty=_accept(ctx.ty(), self),
                body=ctx.expr().accept(self))

    def visitSeq(self, ctx:MiniMLParser.SeqContext):
        subs=[x.accept(self) for x in ctx.ite()]
        if len(subs) == 1:
            return subs[0]
        else:
            return SeqNode(ctx, subs=subs)

    def visitIte1(self, ctx:MiniMLParser.Rel1Context):
        return IteNode(ctx,
                cond=ctx.rel(0).accept(self), tr=ctx.rel(1).accept(self),
                fl=ctx.ite().accept(self))

    def visitRel1(self, ctx:MiniMLParser.Rel1Context):
        return BinOpNode(ctx,
                lhs=ctx.rel().accept(self), op=text(ctx.RelOp()),
                rhs=ctx.add().accept(self))

    def visitAdd1(self, ctx:MiniMLParser.Add1Context):
        return BinOpNode(ctx,
                lhs=ctx.add().accept(self), op=text(ctx.AddOp()),
                rhs=ctx.mul().accept(self))

    def visitMul1(self, ctx:MiniMLParser.Mul1Context):
        return BinOpNode(ctx,
                lhs=ctx.mul().accept(self), op=text(ctx.MulOp()),
                rhs=ctx.una().accept(self))

    def visitUna1(self, ctx:MiniMLParser.Una1Context):
        return UnaOpNode(ctx,
                op=text(ctx.UnaOp()), sub=ctx.una().accept(self))

    def visitApp1(self, ctx:MiniMLParser.App1Context):
        return AppNode(ctx,
                fn=ctx.app().accept(self), arg=ctx.atom().accept(self))

    def visitAtomUnit(self, ctx:MiniMLParser.AtomUnitContext):
        return LitNode(ctx,
                val=())

    def visitAtomInt(self, ctx:MiniMLParser.AtomIntContext):
        return LitNode(ctx,
                val=int(text(ctx)))

    def visitAtomIdent(self, ctx:MiniMLParser.AtomIdentContext):
        return VarRefNode(ctx,
                name=text(ctx))

    def visitAtomParen(self, ctx:MiniMLParser.AtomParenContext):
        return ctx.expr().accept(self)

    def visitTyParen(self, ctx:MiniMLParser.TyParenContext):
        return ctx.ty().accept(self)

    def visitAtomPrint(self, ctx:MiniMLParser.AtomPrintContext):
        return BuiltinNode(ctx,
                name='println')

    def visitTyInt(self, ctx:MiniMLParser.TyIntContext):
        return TyNode(ctx,
                base='int')

    def visitTyArrow(self, ctx:MiniMLParser.TyArrowContext):
        return TyNode(ctx,
                base=ctx.ty(0).accept(self), rhs=ctx.ty(1).accept(self))

    def visitTyUnit(self, ctx:MiniMLParser.TyUnitContext):
        return TyNode(ctx,
                base='unit')

