from collections import namedtuple

from ..utils import *
from ..common import *
from .ast import ASTNode

def NodeClassFactory(nodeName, fieldNames, Base=ASTNode, bunched=False, **kwargs):
    def __init__(self, ctx, **kwargs):
        # Python >=3.6 preserves order of kwargs
        if set(kwargs.keys()) != set(fieldNames):
            raise MiniMLError(f'fields {fieldNames} expected, given {kwargs.keys()}')
        # Set children (for traversal)
        Base.__init__(self, kwargs.values(), pos=ctxPos(ctx), bunched=bunched)
        # Set Accessors
        for idx, (field, value) in enumerate(kwargs.items()):
            def f(new=None, _idx=idx): # loop lambda caveat
                if new is None:
                    return self._c[_idx]
                else:
                    self._c[_idx] = new
            setattr(self, field, f)
    initDict = {"__init__": __init__}
    nodeClass = type(nodeName, (Base,) , {**initDict, **kwargs})
    return nodeClass


TyNode = NodeClassFactory('TyNode', ('base', 'rhs'))
TopNode = NodeClassFactory('TopNode', ('expr',))
LamNode = NodeClassFactory('LamNode', ('name', 'ty', 'body'))
SeqNode = NodeClassFactory('SeqNode', ('subs',), bunched=True)
AppNode = NodeClassFactory('AppNode', ('fn', 'arg'))
LitNode = NodeClassFactory('LitNode', ('val',))
VarRefNode = NodeClassFactory('VarRefNode', ('name',))

LetRecArm = namedtuple('LetRecArm', ('name', 'arg', 'argTy', 'val'))
LetRecNode = NodeClassFactory('LetRecNode', ('arms', 'body'))
BuiltinNode = NodeClassFactory('BuiltinNode', ('name',))

IteNode = NodeClassFactory('IteNode', ('cond', 'tr', 'fl'))
BinOpNode = NodeClassFactory('BinOpNode', ('lhs', 'op', 'rhs'))
UnaOpNode = NodeClassFactory('UnaOpNode', ('op', 'sub'))
