"""
Typer.

We use a Hindley-Milner style type system.

When python 3.10 comes out this'll be a lot easier with pattern matching.
"""
from ..utils import *
from ..common import *

from .ast import *
from .astnodes import *

class Type:
    def __repr__(self):
        return str(self)

    def subst(self, tvId, ty):
        raise MiniMLError('unimplemented subst')

    def substMap(self, tvMap):
        raise MiniMLError('unimplemented substMap')

    def freeTV(self):
        """
        a list of free type variables within this type.
        """
        raise MiniMLError('unimplemented freeTV')

    # PartialEq
    def __eq__(self, other):
        raise MiniMLError('unimplemented Type.__eq__')

    # Actually __ne__ but this name is more informative.
    def unableToUnify(self, other):
        raise MiniMLError('unimplemented Type.unableToUnify')

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

    def freeTV(self):
        return []

    def unableToUnify(self, other):
        return not (isinstance(other, TypeVar) or self == other)

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

    def freeTV(self):
        return self.lhs.freeTV() + self.rhs.freeTV()

    def unableToUnify(self, other):
        return not (isinstance(other, TypeVar) or self == other)

    def flatten(self):
        """
        Transform `t1 -> (t2 -> (t3 -> (... tk)))` to `[t1, t2, t3, ... tk]`
        """
        ret, t = [], self
        while isinstance(t, LamType):
            ret += [t.lhs]
            t = t.rhs
        ret += [t]
        return ret

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
        return self.arity() == other.arity() and all(x == y for x, y in zip(self.subs, other.subs))

    def __hash__(self):
        return hash(self.subs)

    def subst(self, tvId, ty):
        return TupleType(*[t.subst(tvId, ty) for t in self.subs])

    def substMap(self, tvMap):
        return TupleType(*[t.substMap(tvMap) for t in self.subs])

    def freeTV(self):
        return joinlist([], [t.freeTV() for t in self.subs])

    def unableToUnify(self, other):
        return not (isinstance(other, TypeVar) or self == other)


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

    def freeTV(self):
        return [self.id]

    def unableToUnify(self, other):
        return False

class TypeSchema(Type):
    """
    For HM type systems, type schemata only occur in typing contexts. They
    are instantiated at each use, and thus do not participate in the
    unification process. So all methods only used in unification are unimplemented.
    """
    def __init__(self, ty, tenv=None, quantTVIds=None, constrs=None):
        constrs = constrs or []
        self.ty = ty
        self.constrs = constrs
        assert tenv or quantTVIds is not None
        if quantTVIds is not None:
            self.quantTVIds = quantTVIds
        else:
            self.quantTVIds = list(set(ty.freeTV()) - set(tenv.freeTV()))

    def subst(self, tvId, ty):
        unimplemented()

    def substMap(self, tvMap):
        unimplemented()

    def freeTV(self):
        return list(set(self.ty.freeTV()) - set(self.quantTVIds))

    def __eq__(self, other):
        unimplemented()

    def unableToUnify(self, other):
        unimplemented()

    def instantiate(self):
        tvMap = { qTV: TypeVar.genFresh() for qTV in self.quantTVIds }
        ty = self.ty.substMap(tvMap)
        constrs = [c.substMap(tvMap) for c in self.constrs]
        return ty, constrs

    def __str__(self):
        t = ' '.join(self.quantTVIds)
        return f'A<{t}>. {self.ty}'

class DataType(Type):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f'dataType<{self.name}>'

    def __eq__(self, other):
        return isinstance(other, DataType) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def subst(self, tvId, ty):
        return self

    def substMap(self, tvMap):
        return self

    def freeTV(self):
        return []

    def unableToUnify(self, other):
        return not (isinstance(other, TypeVar) or self == other)

class TypeEnv:
    def __init__(self, tenv=None):
        tenv = tenv or {}
        self.tenv = tenv

    def update(self, varTyBindings):
        tenv = deepcopy(self.tenv)
        tenv.update(varTyBindings)
        return TypeEnv(tenv=tenv)

    def __getitem__(self, key):
        return self.tenv[key]

    def freeTV(self):
        return joinlist([], [ty.freeTV() for ty in self.tenv.values()])



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
        unimplemented()

    def subst(self, tvId, ty):
        unimplemented()

    def substMap(self, tvMap):
        unimplemented()

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

    def substMap(self, tvMap):
        return TypeConstrEq(self.lhs.substMap(tvMap), self.rhs.substMap(tvMap))

class TyperVisitor(ASTVisitor):
    """
    Type inference & checking. Attaches type info to AST nodes.

    Nodes are annotated with fields
        _tenv (\Gamma)  :: down, of type TypeEnv
        _constr         :: up.
                           type constraints are either
                            (T1, T2):   T1 = T2
                            TODO Richer constraints like `isNotLam T`
        type            :: up

    Visit functions returns nothing. Still visiting patterns return (ty, newBind: tenv)
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
        n._tenv = TypeEnv()
        newBind = joindict([self.goDown(n, dt) for dt in n.dataTypes])
        self.goDown(n, n.expr, newBind=newBind)

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

    def visitTyData(self, n):
        n.type = DataType(n.name)
        n._constr = []

    def visitDataType(self, n):
        newBind = {}
        for ctor in n.ctors:
            ctorTy = DataType(n.name)
            for ty in reversed(ctor.argTys):
                self.goDown(n, ty)
                ctorTy = LamType(ty.type, ctorTy)
            newBind[ctor.name[0]] = ctorTy
        return newBind

    def visitLet(self, n):
        self.goDown(n, n.ty)
        self.goDown(n, n.val)
        self.goDown(n, n.body, newBind={ n.name: TypeSchema(n.val.type, tenv=n._tenv, constrs=n.val._constr) })
        n.type = n.body.type
        n._constr += [TypeConstrEq(n.ty.type, n.val.type)]

    def visitLetRec(self, n):
        armDecls = {}
        armValTys = []
        # 1. declare all arms before going into their body, but do not go into vals yet
        for arm in n.arms:
            self.goDown(n, arm.fnTy)
            self.goDown(n, arm.argTy)
            armValTy = TypeVar.genFresh()
            armValTys += [armValTy]
            n._constr += [TypeConstrEq(arm.fnTy.type, LamType(arm.argTy.type, armValTy))]
            # TODO: poly let-rec
            armDecls[arm.fnName] = arm.fnTy.type
        tenv = n._tenv.update(armDecls)
        # 2. type the arm bodies
        for arm, armValTy in zip(n.arms, armValTys):
            self.goDown(n, arm.val, chTEnv=tenv.update({ arm.argName: arm.argTy.type }))
            n._constr += [TypeConstrEq(arm.val.type, armValTy)]
        # 3. type the let body
        self.goDown(n, n.body, chTEnv=tenv)
        n.type = n.body.type

    def visitLam(self, n):
        self.goDown(n, n.ty)
        self.goDown(n, n.body, newBind={ n.name : n.ty.type })
        n.type = LamType(n.ty.type, n.body.type)

    def visitSeq(self, n):
        self.visitChildren(n)
        n.type = n.subs[-1].type

    def visitIte(self, n):
        self.visitChildren(n)
        n.type = n.tr.type
        n._constr += [
                TypeConstrEq(n.cond.type, BaseType('bool')),
                TypeConstrEq(n.tr.type, n.fl.type)]

    def visitBinOp(self, n):
        self.visitChildren(n)

        if n.op in {'==', '!='}:
            # TODO: lam types are not compariable
            n.type = BaseType('bool')
            n._constr += [TypeConstrEq(n.lhs.type, n.rhs.type)]
            return

        lhsTy, rhsTy, resTy = TyperVisitor.BinOpRules[n.op]
        n.type = resTy
        n._constr += [
                TypeConstrEq(n.lhs.type, lhsTy),
                TypeConstrEq(n.rhs.type, rhsTy)]

    def visitUnaOp(self, n):
        self.visitChildren(n)
        subTy, resTy = TyperVisitor.UnaOpRules[n.op]
        n.type = resTy
        n._constr += [TypeConstrEq(n.sub.type, subTy)]

    def visitApp(self, n):
        self.visitChildren(n)
        resTy = TypeVar.genFresh()
        n.type = resTy
        n._constr += [TypeConstrEq(n.fn.type, LamType(n.arg.type, resTy))]

    def visitLit(self, n):
        if type(n.val) is int:
            n.type = BaseType('int')
            n._constr = []
        elif n.val == ():
            n.type = BaseType('unit')
            n._constr = []
        elif type(n.val) is bool: # fuck you python for bool <: int
            n.type = BaseType('bool')
            n._constr = []
        else:
            unreachable()

    def visitVarRef(self, n):
        ty, constr = n._tenv[n.name], []
        if isinstance(ty, TypeSchema):
            ty, constr = ty.instantiate()
        n.type = ty
        n._constr = constr

    def visitTuple(self, n):
        self.visitChildren(n)
        n.type = TupleType(*[sub.type for sub in n.subs])

    def visitBuiltin(self, n):
        if n.name == 'println': # println: \forall t. t -> unit
            argTV = TypeVar.genFresh()
            n.type = LamType(argTV, BaseType('unit'))
            n._constr = []
        elif n.name == 'print': # print: \forall t. t -> unit
            # TODO: put them foremost. now we have type schemata.
            argTV = TypeVar.genFresh()
            n.type = LamType(argTV, BaseType('unit'))
            n._constr = []
        elif n.name == 'panic': # print: \forall t. t
            n.type = TypeVar.genFresh()
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
        #
        #       Seems like Scala and Rust take the same approach.
        self.visitChildren(n)
        if not isinstance(n.expr.type, TupleType):
            raise MiniMLLocatedError(n,
                    'typeck limitation: argument to nth must be of concrete tuple type')
        if n.idx >= n.expr.type.arity():
            raise MiniMLLocatedError(n,
                    f'cannot take {n.idx}-th element of {n.expr.type.arity()}-ary tuple (nth indices start from 0)')
        n.type = n.expr.type.nth(n.idx)

    def visitMatch(self, n):
        self.goDown(n, n.expr)
        resTy = TypeVar.genFresh()
        n.type = resTy

        for arm in n.arms:
            ty, newBind = self.goDown(n, arm.ptn)
            self.goDown(n, arm.expr, newBind=newBind)
            n._constr += [
                    TypeConstrEq(arm.expr.type, resTy),
                    TypeConstrEq(ty, n.expr.type)]

    def visitPtnBinder(self, n):
        # NOTE: visiting patterns returns (ty, newBind)
        #   ty: what type does the pattern match against
        #   newBind: { name: ty }, binders introduced by the pattern into its body
        ty = TypeVar.genFresh()
        tenv = { n.name: ty }
        n.type = ty
        n._constr = []
        return ty, tenv

    def visitPtnTuple(self, n):
        tys, tenvs = list(unzip(self.goDown(n, s) for s in n.subs))
        tenv = joindict(tenvs)
        ty = TupleType(*tys)
        n.type = ty
        n._constr = []
        return ty, tenv

    def visitPtnLit(self, n):
        self.goDown(n, n.expr)
        ty = n.expr.type
        tenv = {}
        n.type = ty
        n._constr = []
        return ty, tenv

    def visitPtnData(self, n):
        tys, tenvs = list(unzip(self.goDown(n, s) for s in n.subs))
        tenv = joindict(tenvs)
        # the provided (ptn) argument tys and ctor param tys agree
        ctorTys = asinstance(n._tenv[n.name[0]], LamType).flatten()
        constrs = [TypeConstrEq(argTy, ctorParamTy)
                for argTy, ctorParamTy in zip(tys, ctorTys)]
        n.type = ctorTys[-1]
        n._constr = constrs
        return n.type, tenv

    def goDown(self, n, ch, newBind=None, chTEnv=None):
        # just pass down _tenv and collect constr
        if chTEnv is not None:
            ch._tenv = chTEnv
        elif newBind is not None:
            ch._tenv = n._tenv.update(newBind)
        else:
            ch._tenv = n._tenv
        ret = self(ch)
        constr, cDelta = getattr(n, '_constr', []), getattr(ch, '_constr', [])
        n._constr = constr + cDelta
        return ret

    def visitChildren(self, n):
        ret = []
        for f, ch in n._c.items():
            if f in n.bunchedFields:
                for chch in ch:
                    ret += [self.goDown(n, chch)]
            else:
                ret += [self.goDown(n, ch)]
        return ret



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
            if DEBUG['typer.PRINT_CONSTRS']:
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
                    if isinstance(c.lhs, TupleType) and isinstance(c.rhs, TupleType):
                        if c.lhs.arity() != c.rhs.arity():
                            raise MiniMLError(f'tuple arity dismatch: cannot unify {c.lhs} with {c.rhs}')
                        newCs = [TypeConstrEq(x, y) for x, y in zip(c.lhs.subs, c.rhs.subs)]
                        newConstrs += newCs
                        continue
                    if c.lhs.unableToUnify(c.rhs):
                        raise MiniMLError(f'cannot unify {c.lhs} with {c.rhs}')

                newConstrs += [c]
            constrs = newConstrs

            if DEBUG['typer.PRINT_CONSTRS']:
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
            if substTvId in substTy.freeTV():
                raise MiniMLError(f'unable to unify possibly recursive type: \'{substTvId} == {substTy}')

            if DEBUG['typer.PRINT_CONSTRS']:
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

        if DEBUG['typer.PRINT_TVMAP']:
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
