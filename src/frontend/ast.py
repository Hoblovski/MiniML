"""
AST evolves and gets rewritten during compilation passe, defined thus in a
custom fashion.
"""

from ..utils import *
from ..common import *
from collections import OrderedDict

class ASTNode:
    """
    The raw generic AST Node.
    Implements: location, __str__.
    Subclasses need to implement field accessors (better never access _c directly)

    @param `bunchedFields`: subset of `chs` (can also be a list)
        Children that contain a list of ASTNodes.
        Visitors visit the list's entries, instead of treating it as a terminal node.

    INVARIANT:
        type(x) is list | ASTNode       forall x in self._c
            and type(x) is list, its entries are ASTNode

    NOTE:
        subclasses must have:
            self.__class__.NodeName defined
            self.__class__.bunchedFields  defined
    """

    def __init__(self, chs:OrderedDict, pos=(-1, -1)):
        self._c = chs
        self.pos = pos

    def __str__(self):
        return LISPStylePrintVisitor()(self)

    # Override me
    @property
    def NodeName(self):
        raise MiniMLError(f'Undefined NodeName for {type(self)}')

    # Override me
    @property
    def bunchedFields(self):
        raise MiniMLError(f'Undefined bunchedFields for {type(self)}')


class TermNode(ASTNode):
    """
    Wrapper around terminal nodes, so that all nodes in an AST are of type `ASTNode`.
    """
    NodeName = 'Terminal'

    def __init__(self, value, pos=(-1, -1)):
        ASTNode.__init__(self, OrderedDict(), pos)
        self._v = value

    def getv(self):
        return self._v

    def setv(self, new):
        self._v = new

    def __str__(self):
        return str(self.v)

    v = property(getv, setv)


class ASTVisitor:
    """
    NOTE:
        subclasses must have:
            self.__class__.VisitorName defined
    """
    # Override me.
    def joinResults(self, n, chRes):
        return chRes

    # Override me.
    def visitTermNode(self, n):
        pass

    # Override me
    @property
    def VisitorName(self):
        raise MiniMLError(f'Undefined VisitorName for {type(self)}')

    def visit(self, n):
        """
        Default:
          self.joinResults( n, self.visitChildren(n) )

        Override:
          derivedVisitor.visit{NodeName}
          node.accept{VisitorName}
          node.accept
        """
        if isinstance(n, TermNode):
            return self.visitTermNode(n)
        if hasattr(self, f'visit{n.NodeName}'):
            f = getattr(self, f'visit{n.NodeName}')
            return f(n)
        if hasattr(n, f'accept{self.VisitorName}'):
            f = getattr(n, f'accept{self.VisitorName}')
            return f(self)
        if hasattr(n, f'accept'):
            f = getattr(n, f'accept')
            return f(self)
        res = self.visitChildren(n)
        return self.joinResults(n, res)

    def visitChildren(self, n):
        res = []
        for f, ch in n._c.items():
            if f in n.bunchedFields:
                res += [self(chch) for chch in ch]
            else:
                res += [self(ch)]
        return res

    def __call__(self, n):
        return self.visit(n)


class ASTTransformer(ASTVisitor):
    """
    Visit functions returns the new node for substitution.
    Node deletion not supported (do the deletion in parent node).
    """
    def visitChildren(self, n):
        for f, ch in n._c.items():
            if f in n.bunchedFields:
                n._c[f] = [self(chch) for chch in ch]
            else:
                n._c[f] = self(ch)

    def visit(self, n):
        """
        Default:
          child = self.visit(child)   forall n.child
          return n

        Override:
          derivedVisitor.visit{NodeName}
          node.accept{VisitorName}
          node.accept

        Note:
          Never visit a TermNode alone.
          Do rewrite `visit` for its parent!
        """
        if isinstance(n, TermNode):
            return n
        if hasattr(self, f'visit{n.NodeName}'):
            f = getattr(self, f'visit{n.NodeName}')
            return f(n)
        if hasattr(n, f'accept{self.VisitorName}'):
            f = getattr(n, f'accept{self.VisitorName}')
            return f(self)
        if hasattr(n, f'accept'):
            f = getattr(n, f'accept')
            return f(self)
        self.visitChildren(n)
        return n


class IndentedPrintVisitor(ASTVisitor):
    VisitorName = 'IndentedPrint'
    INDENT = '|   '

    def visitTermNode(self, n):
        return [str(n.v)]

    def joinResults(self, n, chLines):
        return [n.NodeName] + [self.INDENT + x for x in flatten(chLines)]

    def visitTop(self, n):
        return '\n'.join(self(n.expr))


class LISPStylePrintVisitor(ASTVisitor):
    VisitorName = 'LISPStylePrint'

    def visitTermNode(self, n):
        return str(n.v)

    def joinResults(self, n, chLines):
        return '(' + ' '.join([n.NodeName] + chLines) + ')'
