from .ast import ASTVisitor, ASTNode
from ..utils import *
from ..common import *

# Yet another @Example visitor
class FormattedPrintVisitor(ASTVisitor):
    VisitorName = 'FormattedPrint'
    INDENT = '    '

    def _i(self, s):
        return '\n'.join([self.INDENT + l for l in s.split('\n')])

    def visitTermNode(self, n):
        return str(n.value)

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
        res = f'\\{self(n.name)} : {self(n.ty)} ->'
        if len(bodyStr) < 40 and '\n' not in bodyStr:
            return f'({res} {bodyStr})'
        else:
            return f'({res}\n{self._i(bodyStr)})'

    def visitSeq(self, n):
        return ' ;\n'.join(self.visitChildren(n))

    def visitLetRecArm(self, arm):
        return f'''{self(arm.name)} ({self(arm.arg)} : {self(arm.argTy)}) =
{self._i(self(arm.val))}'''

    def visitIdxVarRef(self, n):
        idx, sub = n.idx, n.sub
        if sub is None:
            return f'${idx}'
        else:
            return f'${idx}.{sub}'

    def visitIdxLetRecArm(self, arm):
        return f'LamArm {self(arm.argTy)} =\n{self._i(self(arm.val))}'

    def visitIdxLam(self, n):
        bodyStr = self(n.body)
        res = f'Lam {self(n.ty)} ->'
        if len(bodyStr) < 40 and '\n' not in bodyStr:
            return f'({res} {bodyStr})'
        else:
            return f'({res}\n{self._i(bodyStr)})'

