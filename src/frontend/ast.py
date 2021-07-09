"""
AST evolves and gets rewritten during compilation passe, defined thus in a
custom fashion.
"""

from ..utils import *
from ..generated.MiniMLParser import MiniMLParser
from ..generated.MiniMLVisitor import MiniMLVisitor


class ASTNode:
    """
    The generic AST Node.
    Implements: location, __str__.

    *Note: Subclass names must end with `Node`.
    """

    def __init__(self, ctx, *chs):
        self.chs = chs # a list of child nodes
        self._ctx = ctx

    def __str__(self):
        return IndentedPrintVisitor().visit(self)

    def nodeName(self):
        name = self.__class__.__name__
        assert name[-4:] == 'Node'
        return name[:-4]

    def pos(self):
        return (ctx.start.line,ctx.start.column)

    def setFields(self, ld):
        """Just quick start"""
        for name in ld.keys() - {'self', 'ctx'}:
            if name.startswith('_'):
                continue
            setattr(self, name, ld[name])


class ASTVisitor:
    """
    The generic AST visitor.
    """
    def visitChildren(self, node):
        res = []
        for ch in node.chs:
            res.append(self.visit(ch))
        return res

    # For nodes without children, their `res` is [] (unless overriden)
    def joinResults(self, res):
        return None

    # Default: visit all children, return their `joinResults`
    # Override: simply define `visitXXX`
    #
    # Note that `node` may not necessarily be of type XXNode.
    # For example it could be a string.
    def visit(self, node):
        if hasattr(self, f'visit{node.nodeName()}'):
            f = getattr(self, f'visit{node.nodeName()}')
            return f(node)
        else:
            res = self.visitChildren(node)
            return self.joinResults(res)

    # template:
    def visitXXX(self, node):
        print('Template function for visiting `XXXNode`')
        return None


# An example visitor
class IndentedPrintVisitor(ASTVisitor):
    INDENT = '|   ' # indentation block

    def __init__(self, level=0):
        self.level = level

    def visit(self, node):
        result = self.level * IndentedPrintVisitor.INDENT
        if isinstance(node, ASTNode):
            result += node.nodeName() + '\n'
            self.level += 1
            result += ''.join([self.visit(ch) for ch in node.chs])
            self.level -= 1
        else:
            result += str(node) + '\n'
        return result

##############################################################################
# AST Nodes

class TopNode(ASTNode):
    def __init__(self, ctx, expr):
        super().__init__(ctx, expr)
        self.setFields(locals())

class ExprNode(ASTNode):
    def __init__(self, ctx, *chs):
        super().__init__(ctx, *chs)

class LetNode(ExprNode):
    def __init__(self, ctx, name, val, body, ty=None):
        super().__init__(ctx, name, val, body, ty)
        self.setFields(locals())

class LamNode(ExprNode):
    def __init__(self, ctx, name, ty, body):
        super().__init__(ctx, name, ty, body)
        self.setFields(locals())

class SeqNode(ExprNode):
    def __init__(self, ctx, subs):
        super().__init__(ctx, *subs)
        self.setFields(locals())

class AppNode(ExprNode):
    def __init__(self, ctx, fn, arg):
        super().__init__(ctx, fn, arg)
        self.setFields(locals())

class LitNode(ExprNode):
    def __init__(self, ctx, val):
        super().__init__(ctx, val)
        self.setFields(locals())

class VarRefNode(ExprNode):
    def __init__(self, ctx, name):
        super().__init__(ctx, name)
        self.setFields(locals())

class BuiltinNode(ExprNode):
    LegalNames = {
            'println',
    }
    def __init__(self, ctx, name):
        assert name in BuiltinNode.LegalNames
        super().__init__(ctx, name)
        self.setFields(locals())

class BinOpNode(ExprNode):
    LegalOps = {
            '*', '/', '%',
            '+', '-',
            '>', '<', '>=', '<=', '==', '!=',
    }

    def __init__(self, ctx, lhs, op, rhs):
        assert op in BinOpNode.LegalOps
        super().__init__(ctx, lhs, op, rhs)
        self.setFields(locals())

class UnaOpNode(ExprNode):
    LegalOps = {
            '-',
    }

    def __init__(self, ctx, op, sub):
        assert op in UnaOpNode.LegalOps
        super().__init__(ctx, name, ty, body)
        self.setFields(locals())

class TyNode(ASTNode):
    def __init__(self, ctx, base, rhs=None):
        super().__init__(ctx, base, rhs)
        self.setFields(locals())

##############################################################################

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
        if ctx.ty() is not None:
            ty = ctx.ty().accept(self)
        else:
            ty = None
        return LetNode(ctx,
                name=text(ctx.Ident()), val=ctx.expr(0).accept(self),
                body=ctx.expr(1).accept(self), ty=ty)

    def visitLam1(self, ctx:MiniMLParser.Lam1Context):
        return LamNode(ctx,
                name=text(ctx.Ident()), ty=ctx.ty().accept(self),
                body=ctx.expr().accept(self))

    def visitSeq(self, ctx:MiniMLParser.SeqContext):
        return SeqNode(ctx,
                subs=[x.accept(self) for x in ctx.rel()])

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

