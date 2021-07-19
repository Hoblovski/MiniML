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

    @param bunched: Varargs node.
        Always has fields of type `list` (not tuple etc!).
        When flattened that field contains a list of ASTNodes.
        Visitors shall treat them differently.
    """

    def __init__(self, chs, pos=None, bunched=False):
        self._c = list(chs) # Never alias these entries elsewhere.
        self.pos = pos or (-1, -1)
        self.bunched = bunched

    def __str__(self):
        return IndentedPrintVisitor().visit(self)

    def nodeName(self):
        name = self.__class__.__name__
        assert name.endswith('Node')
        return name[:-4]


class ASTVisitor:
    """
    The generic AST visitor.
    """
    def visitChildren(self, node):
        res = []
        for ch in node._c:
            if node.bunched and isinstance(ch, list):
                res += [self(chch) for chch in ch]
            else:
                res += [self(ch)]
        return res

    # Override me.
    def joinResults(self, res):
        pass

    # Override me.
    def visitTerminalNode(self, node):
        pass

    def visitorName(self):
        name = self.__class__.__name__
        assert name.endswith('Visitor')
        return name[:-7]

    # Default: `self.joinResults(self.visitorName(node))`
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

        if hasattr(node, f'accept{self.visitorName()}'):
            f = getattr(node, f'accept{self.visitorName()}')
            return f(self)

        if hasattr(node, f'accept'):
            f = getattr(node, f'accept')
            return f(self)

        res = self.visitChildren(node)
        return self.joinResults(res)

    def __call__(self, node):
        return self.visit(node)


class IndentedPrintVisitor(ASTVisitor):
    INDENT = '|   ' # indentation block

    def __init__(self, level=0):
        self.level = level

    def visit(self, node):
        result = self.level * IndentedPrintVisitor.INDENT
        if isinstance(node, ASTNode):
            result += node.nodeName() + '\n'
            self.level += 1
            for ch in node._c:
                if node.bunched and isinstance(ch, list):
                    result += ''.join(self(chch) for chch in ch)
                else:
                    result += self(ch)
            self.level -= 1
        else:
            result += str(node) + '\n'
        return result
