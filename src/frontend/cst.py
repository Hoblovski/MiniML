from ..utils import *
from ..common import *
from ..generated.MiniMLParser import MiniMLParser
from ..generated.MiniMLVisitor import MiniMLVisitor
from .astnodes import *

def _acceptMaybeTy(ctx, visitor):
    if ctx.ty() is None:
        return TyUnkNode(ctx=ctx)
    return ctx.ty().accept(visitor)

# desugared let. deprecated.
def _Let(pos, name, val, ty, body):
    return AppNode(ctx=ctx,
            fn=LamNode(ctx=ctx,
                name=text(ctx.Ident()), ty=_acceptMaybeTy(ctx, self),
                body=ctx.expr(1).accept(self)),
            arg=ctx.expr(0).accept(self))

class ConstructASTVisitor(MiniMLVisitor):
    """
    Note this class visits the *CST*.
    """

    def __init__(self):
        pass

    def visitTop(self, ctx:MiniMLParser.TopContext):
        return TopNode(ctx=ctx,
                expr=ctx.expr().accept(self))

    def visitLet1(self, ctx:MiniMLParser.Let1Context):
        return LetRecNode(ctx=ctx,
                arms=[arm.accept(self) for arm in ctx.letRecArm()],
                body=ctx.expr().accept(self))

    def visitLetRecArm(self, ctx:MiniMLParser.LetRecArmContext):
        return LetRecArmNode(ctx=ctx,
                name=text(ctx.Ident(0)), argName=text(ctx.Ident(1)),
                argTy=_acceptMaybeTy(ctx, self), val=ctx.expr().accept(self))

    def visitLet2(self, ctx:MiniMLParser.Let2Context):
        # Desugar: let X: T = E0 in E1  =>   (\\X:T -> E1)(E0)
        return LetNode(ctx=ctx,
                name=text(ctx.Ident()), ty=_acceptMaybeTy(ctx, self),
                val=ctx.expr(0).accept(self), body=ctx.expr(1).accept(self))

    def visitMat1(self, ctx:MiniMLParser.Mat1Context):
        return MatchNode(ctx=ctx,
                expr=ctx.expr(0).accept(self),
                arms=[MatchArmNode(ctx=ctx,
                        ptn=ptn.accept(self),
                        expr=expr.accept(self))
                    for ptn, expr in zip(ctx.ptn(), ctx.expr()[1:])])

    def visitPtnParen(self, ctx:MiniMLParser.PtnParenContext):
        return ctx.ptn().accept(self)

    def visitPtnBinder(self, ctx:MiniMLParser.PtnBinderContext):
        return IdentPtnNode(ctx=ctx,
                name=text(ctx))

    def visitPtnTuple(self, ctx:MiniMLParser.PtnTupleContext):
        return TuplePtnNode(ctx=ctx,
                subs=[ptn.accept(self) for ptn in ctx.ptn0()])

    def visitLam1(self, ctx:MiniMLParser.Lam1Context):
        return LamNode(ctx=ctx,
                name=text(ctx.Ident()), ty=_acceptMaybeTy(ctx, self),
                body=ctx.expr().accept(self))

    def visitSeq(self, ctx:MiniMLParser.SeqContext):
        subs=[x.accept(self) for x in ctx.ite()]
        if len(subs) == 1: # do not create unnecessary SeqNodes
            return subs[0]
        else:
            return SeqNode(ctx=ctx, subs=subs)

    def visitIte1(self, ctx:MiniMLParser.Rel1Context):
        return IteNode(ctx=ctx,
                cond=ctx.rel(0).accept(self), tr=ctx.rel(1).accept(self),
                fl=ctx.ite().accept(self))

    def visitRel1(self, ctx:MiniMLParser.Rel1Context):
        return BinOpNode(ctx=ctx,
                lhs=ctx.rel().accept(self), op=text(ctx.relOp()),
                rhs=ctx.add().accept(self))

    def visitAdd1(self, ctx:MiniMLParser.Add1Context):
        return BinOpNode(ctx=ctx,
                lhs=ctx.add().accept(self), op=text(ctx.addOp()),
                rhs=ctx.mul().accept(self))

    def visitMul1(self, ctx:MiniMLParser.Mul1Context):
        return BinOpNode(ctx=ctx,
                lhs=ctx.mul().accept(self), op=text(ctx.mulOp()),
                rhs=ctx.una().accept(self))

    def visitUna1(self, ctx:MiniMLParser.Una1Context):
        return UnaOpNode(ctx=ctx,
                op=text(ctx.unaOp()), sub=ctx.una().accept(self))

    def visitApp1(self, ctx:MiniMLParser.App1Context):
        return AppNode(ctx=ctx,
                fn=ctx.app().accept(self), arg=ctx.atom().accept(self))

    def visitAtomUnit(self, ctx:MiniMLParser.AtomUnitContext):
        return LitNode(ctx=ctx,
                val=())

    def visitAtomTuple(self, ctx:MiniMLParser.AtomTupleContext):
        return TupleNode(ctx=ctx,
                subs=[expr.accept(self) for expr in ctx.expr()])

    def visitLitInt(self, ctx:MiniMLParser.LitIntContext):
        return LitNode(ctx=ctx,
                val=int(text(ctx)))

    def visitAtomIdent(self, ctx:MiniMLParser.AtomIdentContext):
        return VarRefNode(ctx=ctx,
                name=text(ctx))

    def visitAtomParen(self, ctx:MiniMLParser.AtomParenContext):
        return ctx.expr().accept(self)

    def visitTyParen(self, ctx:MiniMLParser.TyParenContext):
        return ctx.ty().accept(self)

    def visitAtomPrint(self, ctx:MiniMLParser.AtomPrintContext):
        return BuiltinNode(ctx=ctx,
                name='println')

    def visitAtomNth(self, ctx:MiniMLParser.AtomNthContext):
        return NthNode(ctx=ctx,
                idx=int(text(ctx.Integer())),
                expr=ctx.atom().accept(self))

    def visitTyInt(self, ctx:MiniMLParser.TyIntContext):
        return TyBaseNode(ctx=ctx,
                name='int')

    def visitTyArrow(self, ctx:MiniMLParser.TyArrowContext):
        return TyLamNode(ctx=ctx,
                lhs=ctx.ty(0).accept(self), rhs=ctx.ty(1).accept(self))

    def visitTyUnit(self, ctx:MiniMLParser.TyUnitContext):
        return TyBaseNode(ctx=ctx,
                name='unit')

