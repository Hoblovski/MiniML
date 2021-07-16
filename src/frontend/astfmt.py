from .ast import ASTVisitor, ASTNode

from ..utils import *
from ..common import *

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


