"""
AST evolves and gets rewritten during compilation passe, defined thus in a
custom fashion.
"""

from collections import namedtuple

from ..utils import *
from ..common import *
from ..generated.MiniMLParser import MiniMLParser
from ..generated.MiniMLVisitor import MiniMLVisitor


class ASTNode:
    """
    The generic AST Node.
    Implements: location, __str__.

    *NOTE: Subclass names must end with `Node`.
    """

    # *NOTE: entries in chs must not be aliased (i.e. fields are lambdas eval'ed lazily)!!!
    #        See `setAccessors`.
    def __init__(self, chs, ctx=None, pos=None):
        self.chs = list(chs) # for item assignment
        if pos is not None:
            self.pos = pos
        elif ctx is not None:
            self.pos = ctxPos(ctx)
        else:
            self.pos = (-1, -1)

    def __str__(self):
        return IndentedPrintVisitor().visit(self)

    def setChildren(self, *chs):
        self.chs = chs

    def nodeName(self):
        name = self.__class__.__name__
        assert name.endswith('Node')
        return name[:-4]

    def setAccessors(self, *names):
        """The name"""
        assert len(names) == len(self.chs)
        for index, name in enumerate(names):
            def f(new=None, index=index): # fuck you python index=index
                if new is None:
                    return self.chs[index]
                else:
                    self.chs[index] = new
            setattr(self, name, f)


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
    # res is a list
    #
    # Used by the default `visit` to join results from `visitChildren`.
    def joinResults(self, res):
        return None

    def visitorName(self):
        name = self.__class__.__name__
        assert name.endswith('Visitor')
        return name[:-7]

    # Default: visit all children, return their `joinResults`
    # Override: simply define `visitXXX`
    #
    # Note that `node` may not necessarily be of type XXNode.
    # For example it could be a string.
    #
    # The default impl could be slow...
    def visit(self, node):
        if not isinstance(node, ASTNode):
            return self.visitTerminalNode(node)

        if hasattr(self, f'visit{node.nodeName()}'):
            f = getattr(self, f'visit{node.nodeName()}')
            return f(node)
        elif hasattr(node, f'accept{self.visitorName()}'):
            f = getattr(node, f'accept{self.visitorName()}')
            return f(self)
        else:
            res = self.visitChildren(node)
            return self.joinResults(res)

    def visitTerminalNode(self, node):
        pass

    # template:
    def visitXXX(self, node):
        print('Template function for visiting `XXXNode`')
        return None

    def __call__(self, node):
        return self.visit(node)


class ASTTransformer(ASTVisitor):
    """
    Simple transformer.

    Return value of visitXXX is the new node (that replaces the old node).

    Node deletion NOT SUPPORTED.
    """
    def visitChildren(self, node):
        node.chs = [self.visit(ch) for ch in node.chs]

    def joinResults(self, res):
        raise MiniMLError('unreachable')

    def visit(self, node):
        """If visit method not overriden, return the old node -- unmodified."""
        if hasattr(self, f'visit{node.nodeName()}'):
            f = getattr(self, f'visit{node.nodeName()}')
            return f(node)
        else:
            self.visitChildren(node)
            return node


# An @Example visitor
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
    def __init__(self, ctx, expr:ExprNode):
        super().__init__((expr,), ctx=ctx)
        self.setAccessors('expr')

class ExprNode(ASTNode):
    def __init__(self, chs:[ASTNode], ctx):
        super().__init__(chs, ctx=ctx)

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

class TyNode(ASTNode):
    def __init__(self, ctx, base:TyNode, rhs:TyNode=None):
        # base can be TyNode or str
        super().__init__((base, rhs), ctx=ctx)
        self.setAccessors('base', 'rhs')

##############################################################################
# Construct AST

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

##############################################################################

# Yet another @Example visitor
class FormattedPrintVisitor(ASTVisitor):
    INDENT = '    '

    def __init__(self):
        self.level = 0 # indentation level

    def _i(self, s):
        return '\n'.join([FormattedPrintVisitor.INDENT + l for l in s.split('\n')])

    # @Example: hooking visit
    def visit(self, node):
        if isinstance(node, ASTNode):
            return super().visit(node)
        else:
            return str(node)

    def joinResults(self, res):
        if len(res) > 1:
            return res
        if len(res) == 1:
            return res[0]
        return ''

    def visitTop(self, n):
        res = '-- Program Begin --------------------------------\n'
        res += self(n.expr())
        res += '\n-- Program End --------------------------------'
        return res

    def visitVarRef(self, n):
        return f'{n.name()}'

    def visitLit(self, n):
        return f'{n.val()}'

    def visitBuiltin(self, n):
        return f'{n.name()}'

    def visitApp(self, n):
        fn, arg = self(n.fn()), self(n.arg())
        if max(len(fn), len(arg)) > 30:
            return f'({fn}\n {arg})'
        else:
            return f'({fn} {arg})'

    def visitLetRec(self, n):
        armsStr = '\nand\n'.join(
                self._i(f'{arm.name} ({arm.arg} : {self(arm.argTy)}) =\n{self._i(self(arm.val))}')
                for arm in n.arms())
        return f"""letrec
{armsStr}
in
{self._i(self(n.body()))}"""

        header += '   and '.join(
                f'{arm.name} ({arm.arg} : {self(arm.argTy)}) = {self(arm.val)}' for arm in n.arms())
        header += '\nin'
        header += self._i(self(n.body()))
        return header

    def visitBinOp(self, n):
        return f'({self(n.lhs())} {n.op()} {self(n.rhs())})'

    def visitUnaOp(self, n):
        return f'({n.op()} {self(n.sub())})'

    def visitTy(self, n):
        if n.rhs() is None:
            return f'{self(n.base())}'
        else:
            return f'({self(n.base())} -> {self(n.rhs())})'

    def visitIte(self, n):
        return f'''if {self(n.cond())} then
{self._i(self(n.tr()))}
else
{self._i(self(n.fl()))}'''

    def visitLam(self, n):
        bodyStr = self(n.body())
        res = f'\\{n.name()} : {self(n.ty())} ->'
        if len(bodyStr) < 40 and '\n' not in bodyStr:
            return f'({res} {bodyStr})'
        else:
            return f'({res}\n{self._i(bodyStr)})'

    def visitSeq(self, n):
        return ' ;\n'.join(self.visitChildren(n))

