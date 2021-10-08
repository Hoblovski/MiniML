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

_DEBUG_PRINT_CONSTRS = False
_DEBUG_PRINT_TVMAP = False

class Type:
    def __repr__(self):
        return str(self)

    def subst(self, tvId, ty):
        raise MiniMLError('unimplemented subst')

    def substMap(self, tvMap):
        raise MiniMLError('unimplemented substMap')

    # Do we need this?
    def freeTyVars(self):
        raise MiniMLError('unimplemented freeTyVars')

    pass

class BaseType(Type):
    def __init__(self, name):
        assert name in AllBaseTypes
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, BaseType) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def subst(self, tvId, ty):
        return self

    def substMap(self, tvMap):
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

    def subst(self, tvId, ty):
        lhs_ = self.lhs.subst(tvId, ty)
        rhs_ = self.rhs.subst(tvId, ty)
        return LamType(lhs_, rhs_)

    def substMap(self, tvMap):
        lhs_ = self.lhs.substMap(tvMap)
        rhs_ = self.rhs.substMap(tvMap)
        return LamType(lhs_, rhs_)

    def freeTyVars(self):
        return self.lhs.freeTyVars() + self.rhs.freeTyVars()

class TupleType(Type):
    def __init__(self, *subs):
        assert all(isinstance(t, Type) for t in subs)
        self.subs = subs

    def arity(self):
        return len(self.subs)

    def nth(self, n):
        return self.subs[n]

    def __str__(self):
        return '(' + ', '.join([str(x) for x in self.subs]) + ')'

    def __eq__(self, other):
        if not isinstance(other, TupleType):
            return False
        return all(x == y for x, y in zip(self.subs, other.subs))

    def __hash__(self):
        return hash(self.subs)

    def subst(self, tvId, ty):
        return TupleType(*[t.subst(tvId, ty) for t in self.subs])

    def substMap(self, tvMap):
        return TupleType(*[t.substMap(tvMap) for t in self.subs])

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

    def subst(self, tvId, ty):
        if tvId == self.id:
            return ty
        else:
            return self

    def substMap(self, tvMap):
        return tvMap.get(self.id, self)

class MiniMLTypeMismatchError(MiniMLLocatedError):
    def __init__(self, n, expected, actual, msg=None):
        msg = msg or ' '
        super().__init__(n, f'bad {msg} type. expected {expected}, given {actual}')

class MiniMLTypeUnifyError(MiniMLLocatedError):
    def __init__(self, lhs, rhs):
        super().__init__(n, f'cannot unify {lhs} with {rhs}')


class TypeConstr:
    # TODO: introduce location information?
    def isValid(self):
        """
        Is this Constr always True? i.e. Useless tautology?
        """
        raise MiniMLError('unimplemented isValid')

class TypeConstrEq(TypeConstr):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return f'{str(self.lhs):<40}=={str(self.rhs):<40}'

    def __repr__(self):
        return str(self)

    def isValid(self):
        return self.lhs == self.rhs

    def subst(self, tvId, ty):
        return TypeConstrEq(self.lhs.subst(tvId, ty), self.rhs.subst(tvId, ty))

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
        n._constr = []

    def visitTyBase(self, n):
        n.type = BaseType(n.name)
        n._constr = []

    def visitTyLam(self, n):
        self.visitChildren(n)
        n.type = LamType(n.lhs.type, n.rhs.type)
        n._constr = []

    def visitLet(self, n):
        # TODO: let-polymorphism
        n.ty._tenv = n._tenv
        self(n.ty)
        n.val._tenv = n._tenv
        self(n.val)
        n.body._tenv = deepcopy(n._tenv)
        n.body._tenv[n.name] = n.val.type
        self(n.body)
        c1 = TypeConstrEq(n.ty.type, n.val.type)
        n.type = n.body.type
        n._constr = n.val._constr + n.body._constr + [c1]

    def visitLetRec(self, n):
        constrs = []
        tenv = deepcopy(n._tenv)
        armResTys = []
        # 1. declare all arms before going into their body
        for arm in n.arms:
            self(arm.fnTy)
            self(arm.argTy)
            armResTy = TypeVar.genFresh()
            c = TypeConstrEq(arm.fnTy.type, LamType(arm.argTy.type, armResTy))
            constrs = constrs + [c]
            tenv[arm.fnName] = arm.fnTy.type
            armResTys += [armResTy]
        # 2. type the arm bodies
        for armResTy, arm in zip(armResTys, n.arms):
            arm.val._tenv = deepcopy(tenv)
            arm.val._tenv[arm.argName] = arm.argTy.type
            self(arm.val)
            c = TypeConstrEq(arm.val.type, armResTy)
            constrs = constrs + arm.val._constr + [c]
        # 3. type the let body
        n.body._tenv = tenv
        self(n.body)
        n._constr = n.body._constr + constrs
        n.type = n.body.type

    def visitLam(self, n):
        n.ty._tenv = n._tenv
        self(n.ty)
        n.body._tenv = deepcopy(n._tenv)
        n.body._tenv[n.name] = n.ty.type
        self(n.body)
        n.type = LamType(n.ty.type, n.body.type)
        n._constr = n.body._constr

    def visitSeq(self, n):
        self.visitChildren(n)
        n.type = n.subs[-1].type
        n._constr = joinlist([], [ch._constr for ch in n.subs])

    def visitIte(self, n):
        self.visitChildren(n)
        n.type = n.tr.type
        c1 = TypeConstrEq(n.cond.type, BaseType('bool'))
        c2 = TypeConstrEq(n.tr.type, n.fl.type)
        n._constr = n.cond._constr + n.tr._constr + n.fl._constr + [c1, c2]

    def visitBinOp(self, n):
        self.visitChildren(n)

        if n.op in {'==', '!='}:
            n.type = BaseType('bool')
            # TODO: lam types are not compariable
            c = TypeConstrEq(n.lhs.type, n.rhs.type)
            n._constr = n.lhs._constr + n.rhs._constr + [c]
            return

        lhsTy, rhsTy, resTy = TyperVisitor.BinOpRules[n.op]
        n.type = resTy
        cl = TypeConstrEq(n.lhs.type, lhsTy)
        cr = TypeConstrEq(n.rhs.type, rhsTy)
        n._constr = n.lhs._constr + n.rhs._constr + [cl, cr]

    def visitUnaOp(self, n):
        self.visitChildren(n)
        subTy, resTy = TyperVisitor.UnaOpRules[n.op]
        n.type = resTy
        c = TypeConstrEq(n.sub.type, subTy)
        n._constr = n.sub._constr + [c]

    def visitApp(self, n):
        self.visitChildren(n)
        resTV = TypeVar.genFresh()
        n.type = resTV
        c = TypeConstrEq(n.fn.type, LamType(n.arg.type, resTV))
        n._constr = n.fn._constr + n.arg._constr + [c]

    def visitLit(self, n):
        if isinstance(n.val, int):
            n.type = BaseType('int')
            n._constr = []
        elif n.val == ():
            n.type = BaseType('unit')
            n._constr = []
        else:
            unreachable()

    def visitVarRef(self, n):
        n.type = n._tenv[n.name]
        n._constr = []

    def visitTuple(self, n):
        self.visitChildren(n)
        n.type = TupleType(*[sub.type for sub in n.subs])
        n._constr = joinlist([], [sub._constr for sub in n.subs])

    def visitBuiltin(self, n):
        if n.name == 'println':
            argTV = TypeVar.genFresh()
            n.type = LamType(argTV, BaseType('unit'))
            n._constr = []
        else:
            unreachable()

    def visitNth(self, n):
        # TODO: we're forbidding things like
        #           let f = \x -> nth 1 x
        #       by requiring n to be already defined type
        #
        #       Theoretically it's possible but let's leave it to dependent typing.
        #       Because essentially  nth  is (variably) dependently typed.
        self.visitChildren(n)
        if not isinstance(n.expr.type, TupleType):
            raise MiniMLLocatedError(n, 'typeck limitation: argument to nth must be of concrete type #TODO')
        if n.idx >= n.expr.type.arity():
            raise MiniMLLocatedError(n, f'cannot take {n.idx}-th element of {n.expr.type.arity()}-ary tuple (nth indices start from 0)')
        n._constr = n.expr._constr
        n.type = n.expr.type.nth(n.idx)

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



class UnifyTagVisitor(ASTVisitor):
    """
    Does unification and tagging types.

    Nodes are annotated with fields
        _tenv           deleted
        _constr         deleted
        type            the inferred type
    """
    VisitorName = 'UnifyTag'

    def unify(_constrs):
        tvMap = {}

        constrs = _constrs
        while constrs != []:
            if _DEBUG_PRINT_CONSTRS:
                print('='*70)
                print('Constrs:')
                pprint(constrs)
                print(':Constrs')
            newConstrs = []

            # 1. break lambdas, tuples etc.
            constrs = [c for c in constrs if not c.isValid()] # filter out all tautologies
            if constrs == []:
                break
            for c in constrs:
                if isinstance(c, TypeConstrEq):
                    if isinstance(c.lhs, LamType) and isinstance(c.rhs, LamType):
                        c1 = TypeConstrEq(c.lhs.lhs, c.rhs.lhs)
                        c2 = TypeConstrEq(c.lhs.rhs, c.rhs.rhs)
                        newConstrs += [c1, c2]
                        continue
                newConstrs += [c]
            constrs = newConstrs

            if _DEBUG_PRINT_CONSTRS:
                print('-'*70)
                print('Constrs:')
                pprint(constrs)
                print(':Constrs')

            # 2. find a resolved type variable (OPT: multiple at once)
            constrs = [c for c in constrs if not c.isValid()] # filter out all tautologies
            if constrs == []:
                break
            substTvId, substTy = None, None
            for c in constrs:
                if isinstance(c, TypeConstrEq):
                    if isinstance(c.lhs, TypeVar):
                        substTvId, substTy = c.lhs.id, c.rhs
                        break
                    if isinstance(c.rhs, TypeVar):
                        substTvId, substTy = c.rhs.id, c.lhs
                        break
            else:
                raise MiniMLError('unification failed: no trivial varsubst')
            tvMap[substTvId] = substTy
            if _DEBUG_PRINT_CONSTRS:
                print('='*70)
                print(f'{str(substTvId):<30} => {str(substTy):<30}')
            # todo check: panic if    free(substTy).contains(substTvId)

            # 3. apply the substitution
            #    note the substitution need be applied to tvMap as well
            #    as tvMap is a specific trivial form of constraint
            constrs = [c.subst(substTvId, substTy) for c in constrs]
            for tvId, ty in tvMap.items():
                tvMap[tvId] = ty.subst(substTvId, substTy)
            constrs = [c for c in constrs if not c.isValid()] # filter out all tautologies
            if constrs == []:
                break

        if _DEBUG_PRINT_TVMAP:
            print(tvMap)

        return tvMap

    def __init__(self, constrs):
        self.tvMap = UnifyTagVisitor.unify(constrs)

    def visit(self, n):
        if hasattr(n, 'type'):
            n.type = n.type.substMap(self.tvMap)
        ASTVisitor.visit(self, n)


class TypedIndentedPrintVisitor(ASTVisitor):
    VisitorName = 'TypedIndentedPrint'
    INDENT = '|   '

    def visitTermNode(self, n):
        ty = getattr(n, 'type', None)
        if ty is not None:
            return ['* typer: ' + str(n.v), str(ty)]
        else:
            return [str(n.v)]

    def joinResults(self, n, chLines):
        ty = getattr(n, 'type', None)
        if ty is not None:
            return [n.NodeName, '* typer: ' + str(ty)] + [self.INDENT + x for x in flatten(chLines)]
        else:
            return [n.NodeName] + [self.INDENT + x for x in flatten(chLines)]

    def visitTop(self, n):
        res = self.visitChildren(n)
        res = self.joinResults(n, res)
        return '\n'.join(res)
