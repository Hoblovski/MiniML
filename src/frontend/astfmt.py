"""
This is possibly not well maintained.
"""

from .ast import ASTVisitor, ASTNode
from ..utils import *
from ..common import *


class FormattedPrintVisitor(ASTVisitor):
    VisitorName = 'FormattedPrint'
    INDENT = '    '

    def _i(self, s):
        return '\n'.join([self.INDENT + l for l in s.split('\n')])

    def _q(self, s):
        return s if ' ' not in s else f'({s})'

    def visitTermNode(self, n):
        return str(n.v)

    def joinResults(self, n, res):
        if isinstance(res, str):
            return res
        if len(res) == 1:
            return res[0]
        return '(' + ' '.join(res) + ')'

    def visitTop(self, n):
        header = '-- Program Begin --------------------------------\n'
        footer = '\n-- Program End --------------------------------\n'
        return header + self(n.expr) + footer

    def visitApp(self, n):
        fn, arg = self(n.fn), self(n.arg)
        if max(len(fn), len(arg)) > 30:
            return f'({fn}\n {arg})'
        else:
            return f'({fn} {arg})'

    def visitLet(self, n):
        valStr = self(n.val)
        if len(valStr) < 15:
            return f"""let {n.name} : {self(n.ty)} = {valStr} in
{self(n.body)}"""
        else:
            return f"""let {n.name} : {self(n.ty)} =
{self._i(valStr)}
in
{self(n.body)}"""

    def visitLetRec(self, n):
        armsStr = '\nand\n'.join(self._i(self(arm)) for arm in n.arms)
        return f"""letrec
{armsStr}
in
{self._i(self(n.body))}"""

    def visitTyUnk(self, n):
        return '<unk>'

    def visitTyLam(self, n):
        return f'({self(n.lhs)} -> {self(n.rhs)})'

    def visitIte(self, n):
        return f'''if {self(n.cond)} then
{self._i(self(n.tr))}
else
{self._i(self(n.fl))}'''

    def visitLam(self, n):
        bodyStr = self(n.body)
        res = f'\\{n.name} : {self(n.ty)} ->'
        if len(bodyStr) < 40 and '\n' not in bodyStr:
            return f'({res} {bodyStr})'
        else:
            return f'({res}\n{self._i(bodyStr)})'

    def visitSeq(self, n):
        return ' ;\n'.join(self.visitChildren(n))

    def visitLetRecArm(self, arm):
        return f'''{arm.name} ({arm.argName} : {self(arm.argTy)}) =
{self._i(self(arm.val))}'''

    def visitNVarRef(self, n):
        return f'${n.idx}'

    def visitNClosRef(self, n):
        return f'${n.idx}.{n.sub}'

    def visitNLetRecArm(self, arm):
        return f'LamArm {self(arm.argTy)} =\n{self._i(self(arm.val))}'

    def visitNLam(self, n):
        bodyStr = self(n.body)
        res = f'Lam {self(n.ty)} ->'
        if len(bodyStr) < 40 and '\n' not in bodyStr:
            return f'({res} {bodyStr})'
        else:
            return f'({res}\n{self._i(bodyStr)})'

    def visitMatch(self, n):
        armsStr = '\n'.join(self(arm) for arm in n.arms)
        return f"""match {self(n.expr)}
{armsStr}
end"""

    def visitMatchArm(self, n):
        return f"""| {self(n.ptn)} ->
{self._i(self(n.expr))}"""

    def visitIdentPtn(self, n):
        return f'{n.name}'

    def visitTuple(self, n):
        return '(' + ', '.join(f'({self(sub)})' for sub in n.subs) + ')'

    def visitTuplePtn(self, n):
        return ', '.join(f'({self(sub)})' for sub in n.subs)

    def visitNIdentPtn(self, n):
        return '@'

    def visitNTuplePtn(self, n):
        return ', '.join(f'{self._q(self(sub))}' for sub in n.subs)

    def visitNth(self, n):
        return f'(nth {n.idx} {self(n.expr)})'
