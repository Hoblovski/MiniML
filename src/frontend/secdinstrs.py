from ..common import *
from ..utils import *

class SECDInstr:
    """
    NOTE:
        subclasses must have:
            self.__class__.InstrName defined
    """
    pass

def instrClassFactory(className, instrName, fieldNames, vararg=False, Base=SECDInstr):
    if vararg and len(fieldNames) != 1:
        raise MiniMLError(
                f'vararg instrs can only have one field, but got {fieldNames}')

    def initf(self, *args):
        if not vararg and len(args) != len(fieldNames):
            raise MiniMLError(f'Expected {len(fieldNames)} args, given {len(args)}')
        self._args = args

    # used for secdi
    def fmtSECDf(self):
        a = self._args[0] if vararg else self._args
        argStr = ' '.join(str(x) for x in a)
        return f'{self.InstrName:<10}{argStr}'

    # used for C backend
    def fmtCf(self):
        a = self._args[0] if vararg else self._args
        argStr = ', '.join(str(x) for x in a)
        return f'I{self.InstrName}({argStr});'

    # do not provide setters yet
    def mkGet(name, idx):
        def getter(self):
            return self._args[idx]
        return getter

    accessors = {
            f: property(mkGet(f, idx))
            for idx, f in enumerate(fieldNames) }

    d = {'__init__': initf, 'InstrName': instrName, 'fmtSECD': fmtSECDf, 'fmtC': fmtCf,
            **accessors}
    instrClass = type(className, (Base,), d)
    return instrClass


def createInstrs(spec):
    spec = [x.split() for x in spec.strip().split('\n') if x != '']
    classes = {}
    for instrName, _, *fieldNames in spec:
        vararg = any('+' in f for f in fieldNames)
        fieldNames = [f.replace('+', '') for f in fieldNames]
        className = instrName.capitalize() + 'Instr'
        instrClass = instrClassFactory(className, instrName, fieldNames,
                vararg=vararg)
        classes[className] = instrClass
    return classes

spec = """
halt     :
pop      : n
apply    :
const    : val
access   : n
focus    : n
return   :
closure  : lbl
closures : lbl+
builtin  : name
binary   : op
unary    : op
branch   : op lbl
label    : name
"""
globals().update(createInstrs(spec))

BinaryInstr.fmtSECD = lambda self: binOpToStr[self.op]
UnaryInstr.fmtSECD = lambda self: unaOpToStr[self.op]
LabelInstr.fmtSECD = lambda self: f'\n  {self.name}:'
BranchInstr.fmtSECD = lambda self: f'{self.op} {self.lbl}'
ConstInstr.fmtC = lambda self: f'Iconstint({self.val});' # FIXME


def branchFmtC(self):
    if self.op == 'br':
        return f'Ibr({self.lbl});'
    elif self.op == 'brfl':
        return f'Ibr1(0 ==, {self.lbl});'
BranchInstr.fmtC = branchFmtC
