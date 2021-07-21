from collections import namedtuple, OrderedDict

from ..utils import *
from ..common import *
from .ast import ASTNode, TermNode

def nodeClassFactory(className, nodeName, fieldNames,
        bunchedFields=None, termFields=None, Base=ASTNode):

    bunchedFields = bunchedFields or []
    termFields = termFields or []
    if not (set(bunchedFields) <= set(fieldNames)):
        raise MiniMLError(
                f'bunchedFields {bunchedFields} need be subset of fields {fieldNames}')
    if not (set(termFields) <= set(fieldNames)):
        raise MiniMLError(
                f'termFields {termFields} need be subset of fields {fieldNames}')

    def initf(self, pos=None, ctx=None, **kwargs):
        # Python >=3.6 preserves order of kwargs
        if set(kwargs.keys()) != set(fieldNames):
            raise MiniMLError(f'fields {fieldNames} expected, given {kwargs.keys()}')
        # Set children (for traversal)
        pos = pos or ctxPos(ctx)
        for termf in termFields:
            kwargs[termf] = TermNode(kwargs[termf], pos)
        Base.__init__(self, OrderedDict(kwargs), pos=pos)

    def mkGetset(name, term, bunch):
        if term:
            def getter(self):
                return self._c[name].v
            def setter(self, new):
                self._c[name].v = new
        else:
            def getter(self):
                return self._c[name]
            def setter(self, new):
                self._c[name] = new
        return (getter, setter)

    accessors = {
            f: property(*mkGetset(f, bunch=f in bunchedFields, term=f in termFields))
            for f in fieldNames }
    d = {'__init__': initf, 'NodeName': nodeName, 'bunchedFields': bunchedFields, **accessors}
    nodeClass = type(className, (Base,), d)
    return nodeClass


def createNodes(spec):
    spec = [x.split() for x in spec.strip().split('\n') if x != '']
    classes = {}
    for nodeName, _, *fieldNames in spec:
        bunchedFields = [ f[:-1] for f in fieldNames if f.endswith('+') ]
        termFields = [ f[:-1] for f in fieldNames if f.endswith('.') ]
        fieldNames = [f.replace('+', '').replace('.', '') for f in fieldNames]
        className = nodeName + 'Node'
        nodeClass = nodeClassFactory(className, nodeName, fieldNames,
                bunchedFields=bunchedFields, termFields=termFields)
        # black magic
        classes[className] = nodeClass
    return classes

spec = """
TyUnk     :
TyBase    : name.
TyLam     : lhs rhs
Top       : expr
Lam       : name.  ty  body
Seq       : subs+
App       : fn  arg
Lit       : val.
VarRef    : name.
LetRecArm : name.  arg.  argTy  val
LetRec    : arms+  body
Builtin   : name.
Ite       : cond  tr  fl
BinOp     : lhs  op.  rhs
UnaOp     : op.  sub
"""

globals().update(createNodes(spec))
