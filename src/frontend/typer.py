"""
Typer.

Even if we don't have universal types at user level, for type inference we should have them because of constraint based type checking.
For now it's naive constraint-based type inference, but later it should be some hindley-milner.

When python 3.10 comes out this'll be a lot easier with pattern matching.
"""
from ..utils import *
from ..common import *

from .ast import *
from .astnodes import *


class Type:
    def __repr__(self):
        return str(self)

    def substTV(self, tvId, actualTy):
        raise MiniMLError('unimplemented substTV')

    def substTVMap(self, tvMap):
        raise MiniMLError('unimplemented substTVMap')

    def freeTyVars(self):
        raise MiniMLError('unimplemented freeTyVars')

    pass

class BaseType(Type):
    def __init__(self, name):
        #assert name in AllBaseTypes
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, BaseType) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def substTV(self, tvId, actualTy):
        return self

    def substTVMap(self, tvMap):
        return self

    def freeTyVars(self):
        return []

class LamType(Type):
    def __init__(self, lhs, rhs):
        assert isinstance(lhs, Type) and isinstance(rhs, Type)
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return f'({self.lhs}) -> ({self.rhs})'

    def __eq__(self, other):
        return isinstance(other, LamType) and self.lhs == other.lhs and self.rhs == other.rhs

    def __hash__(self):
        return hash((self.lhs, self.rhs))

    def substTV(self, tvId, actualTy):
        lhs_ = self.lhs.substTV(tvId, actualTy)
        rhs_ = self.rhs.substTV(tvId, actualTy)
        return LamType(lhs_, rhs_)

    def substTVMap(self, tvMap):
        lhs_ = self.lhs.substTVMap(tvMap)
        rhs_ = self.rhs.substTVMap(tvMap)
        return LamType(lhs_, rhs_)

    def freeTyVars(self):
        return self.lhs.freeTyVars() + self.rhs.freeTyVars()

class TypeVar(Type):
    """
    genTypeVarName ensures that generated type variables are always unique.

    TODO: associate TypeVar with ASTNode for better error
    """
    _S = []

    def genTypeVarName():
        for i in range(len(TypeVar._S)-1, -1, -1):
            if TypeVar._S[i] != 'z':
                TypeVar._S[i] = chr(ord(TypeVar._S[i]) + 1)
                for j in range(i+1, len(TypeVar._S)):
                    TypeVar._S[j] = 'a'
                break
        else:
            TypeVar._S = ['a'] * (len(TypeVar._S) + 1)
        return ''.join(TypeVar._S)

    def genFresh():
        return TypeVar()

    def __init__(self):
        self.id = TypeVar.genTypeVarName()

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, TypeVar) and self.id == other.id

    def __str__(self):
        return f"'{self.id}"

    def substTV(self, tvId, actualTy):
        if tvId == self.id:
            return actualTy
        else:
            return self

    def substTVMap(self, tvMap):
        return tvMap.get(self.id, self)

    # TODO: free tv?

class MiniMLTypeMismatchError(MiniMLLocatedError):
    def __init__(self, n, expected, actual, msg=None):
        msg = msg or ' '
        super().__init__(n, f'bad {msg} type. expected {expected}, given {actual}')

class MiniMLTypeUnifyError(MiniMLLocatedError):
    def __init__(self, lhs, rhs):
        super().__init__(n, f'cannot unify {lhs} with {rhs}')

class TyperVisitor(ASTVisitor):
    """
    Type inference & checking. Attaches type info to AST nodes.

    Nodes are annotated with fields
        _tenv (\Gamma)  :: down
        _constr         :: up.
                           type constraints are either
                            (T1, T2):   T1 = T2
                            TODO isNotLam T
        type            :: up
    """
    VisitorName = 'Typer'

    UnaOpRules = {
    #  op : sub, resTy
        '-': (BaseType('int'), BaseType('int'))
    }

    BinOpRules = {
    #  op : lhsTy, rhsTy, resTy
        '+': (BaseType('int'), BaseType('int'), BaseType('int')),
        '-': (BaseType('int'), BaseType('int'), BaseType('int')),
        '*': (BaseType('int'), BaseType('int'), BaseType('int')),
        '/': (BaseType('int'), BaseType('int'), BaseType('int')),
        '%': (BaseType('int'), BaseType('int'), BaseType('int')),

        '>': (BaseType('int'), BaseType('int'), BaseType('bool')),
        '<': (BaseType('int'), BaseType('int'), BaseType('bool')),
        '>=': (BaseType('int'), BaseType('int'), BaseType('bool')),
        '<=': (BaseType('int'), BaseType('int'), BaseType('bool')),
    }

    def visitTop(self, n):
        n._tenv = {}
        self.visitChildren(n)
        n._constr = n.expr._constr

    def visitTyUnk(self, n):
        n.type = TypeVar.genFresh()
        n._constr = set()

    def visitTyBase(self, n):
        n.type = BaseType(n.name)
        n._constr = set()

    def visitTyLam(self, n):
        self.visitChildren(n)
        n.type = LamType(n.lhs.type, n.rhs.type)
        n._constr = set()

    def visitLet(self, n):
        self(n.ty)
        n.val._tenv = n._tenv
        self(n.val)
        n.body._tenv = deepcopy(n._tenv)
        n.body._tenv[n.name] = n.val.type
        self(n.body)
        c1 = (n.ty.type, n.val.type)
        n.type = n.body.type
        n._constr = n.val._constr | n.body._constr | {c1}

    def visitLetRec(self, n):
        assert False
#LetRec                  : arms+  body
#    LetRecArm           : name.  argName.  argTy  val

    def visitLam(self, n):
        self(n.ty)
        n.body._tenv = deepcopy(n._tenv)
        n.body._tenv[n.name] = n.ty.type
        self(n.body)
        n.type = LamType(n.ty.type, n.body.type)
        n._constr = n.body._constr

    def visitSeq(self, n):
        self.visitChildren(n)
        n.type = n.subs[-1].type
        n._constr = unionsets([ch._constr for ch in n.subs])

    def visitIte(self, n):
        self.visitChildren(n)
        n.type = n.tr.type
        c1 = (n.cond.type, BaseType('bool'))
        c2 = (n.tr.type, n.fl.type)
        n._constr = n.cond._constr | n.tr._constr | n.fl._constr | {c1, c2}

    def visitBinOp(self, n):
        self.visitChildren(n)

        if n.op in {'==', '!='}:
            n.type = BaseType('bool')
            # TODO: lam types are not compariable
            c = (n.lhs.type, n.rhs.type)
            n._constr = n.lhs._constr | n.rhs._constr | {c}
            return

        lhsTy, rhsTy, resTy = TyperVisitor.BinOpRules[n.op]
        n.type = resTy
        cl = (n.lhs.type, lhsTy)
        cr = (n.rhs.type, rhsTy)
        n._constr = n.lhs._constr | n.rhs._constr | {cl, cr}

    def visitUnaOp(self, n):
        self.visitChildren(n)
        subTy, resTy = TyperVisitor.UnaOpRules[n.op]
        n.type = resTy
        c = (n.sub.type, subTy)
        n._constr = n.sub._constr | {c}

    def visitApp(self, n):
        self.visitChildren(n)
        resTV = TypeVar.genFresh()
        n.type = resTV
        c = (n.fn.type, LamType(n.arg.type, resTV))
        n._constr = n.fn._constr | n.arg._constr | {c}

    def visitLit(self, n):
        if isinstance(n.val, int):
            n.type = BaseType('int')
            n._constr = set()
        elif n.val == ():
            n.type = BaseType('unit')
            n._constr = set()
        else:
            unreachable()

    def visitVarRef(self, n):
        n.type = n._tenv[n.name]
        n._constr = set()

    def visitTuple(self, n):
        self.visitChildren(n)
        assert False

    def visitBuiltin(self, n):
        if n.name == 'println':
            argTV = TypeVar.genFresh()
            n.type = LamType(argTV, BaseType('unit'))
            n._constr = set()
        else:
            unreachable()

    def visitNth(self, n):
        assert False

    def visitChildren(self, n):
        # pass down _Gamma
        res = []
        for f, ch in n._c.items():
            if f in n.bunchedFields:
                for chch in ch:
                    chch._tenv = n._tenv
                    res += [self(chch)]
            else:
                ch._tenv = n._tenv
                res += [self(ch)]
        return res



class UnifyVisitor(ASTVisitor):
    """
    Does unification and tagging types.

    Nodes are annotated with fields
        _tenv:          deleted
        _constr         deleted
        type
    """
    VisitorName = 'Unify'

    def unify(_constrs):
        tvMap = {}

        constrs = _constrs
        while constrs != []:
            newConstrs = []

            # 1. break lambdas
            for lhs, rhs in constrs:
                if lhs == rhs:
                    continue
                if isinstance(lhs, LamType) and isinstance(rhs, LamType):
                    newConstrs += [(lhs.lhs, rhs.lhs), (lhs.rhs, rhs.rhs)]
                    continue
                newConstrs += [(lhs, rhs)]
            constrs = [(lhs, rhs) for lhs, rhs in newConstrs if lhs != rhs]
            if constrs == []:
                break

            # 2. find a nontrivial variable substitution (OPT: multiple at once)
            tyKey, tyVal = None, None
            for lhs, rhs in constrs:
                if isinstance(lhs, TypeVar):
                    tyKey, tyVal = lhs.id, rhs
                    break
                if isinstance(rhs, TypeVar):
                    tyKey, tyVal = rhs.id, lhs
                    break
            else:
                raise MiniMLError('unification failed: no trivial varsubst')
            tvMap[tyKey] = tyVal

            # 3. apply the substitution
            constrs = [(lhs.substTV(tyKey, tyVal), rhs.substTV(tyKey, tyVal))
                    for lhs, rhs in constrs]
            constrs = [(lhs, rhs) for lhs, rhs in constrs if lhs != rhs]

        return tvMap

    def doTag(self, n):
        if hasattr(n, 'type'):
            n.type = n.type.substTVMap(self.tvMap)
            #del n._tenv, n._constr
        self.visitChildren(n)

    def visitTop(self, n):
        self.tvMap = UnifyVisitor.unify(n._constr)
        self.doTag(n)

    def visitTyUnk(self, n):
        self.doTag(n)

    def visitTyBase(self, n):
        self.doTag(n)

    def visitTyLam(self, n):
        self.doTag(n)

    def visitLet(self, n):
        self.doTag(n)

    def visitLetRec(self, n):
        self.doTag(n)

    def visitLam(self, n):
        self.doTag(n)

    def visitSeq(self, n):
        self.doTag(n)

    def visitIte(self, n):
        self.doTag(n)

    def visitBinOp(self, n):
        self.doTag(n)

    def visitUnaOp(self, n):
        self.doTag(n)

    def visitApp(self, n):
        self.doTag(n)

    def visitLit(self, n):
        self.doTag(n)

    def visitVarRef(self, n):
        self.doTag(n)

    def visitTuple(self, n):
        self.doTag(n)

    def visitBuiltin(self, n):
        self.doTag(n)

    def visitNth(self, n):
        self.doTag(n)
        assert False



class TypedIndentedPrintVisitor(ASTVisitor):
    VisitorName = 'TypedIndentedPrint'
    INDENT = '|   '

    def visitTermNode(self, n):
        ty = getattr(n, 'type', None)
        if ty is not None:
            return [str(n.v), str(ty)]
        else:
            return [str(n.v)]

    def joinResults(self, n, chLines):
        ty = getattr(n, 'type', None)
        if ty is not None:
            return [n.NodeName, str(ty)] + [self.INDENT + x for x in flatten(chLines)]
        else:
            return [n.NodeName] + [self.INDENT + x for x in flatten(chLines)]

    def visitTop(self, n):
        res = self.visitChildren(n)
        res = self.joinResults(n, res)
        return '\n'.join(res)
