"""
AST evolves and gets rewritten during compilation passe, defined thus in a
custom fashion.
"""

from ..utils import *
from ..common import *

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
