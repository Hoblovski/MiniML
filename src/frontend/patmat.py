"""
Convert pattern matching into plain lambda.
Used to be bad design of premature desugaring.
Should come after typer and namer.

- After namer:
    possible to clash invented names with existing ones, but avoided by carefully choosing namespaces.
- After typer:
    better type error info.
    the translation can be untyped (which is crucial as the scheme below is not typable).

Translation scheme:

    Translating into pattern lambdas with a ptn2lam function.

        ptn2lam(ptn, rhs): lam

    Since lambdas does it automatically, we need not worry about name binding.
    @p -> r     is transformed into     \\args ... -> (OK|FAIL, r)

    A match expression is translated as
    ```
        match expr
        | p1 -> r1
        | p2 -> r2
        | ...
        | pk -> rk
        end

        =>

        // compute expr ahead and pushenv so we can reuse it
        let e = expr in

            // try first pattern
            let lam1 = ptn2lam (@p1 -> r1) in
            let res1 = lam1 e in
            if nth 0 res1 == OK then nth 1 res1 else

            // try second pattern
            let lam2 = ptn2lam (@p2 -> r2) in
            let res2 = lam2 e in
            if nth 0 res2 == OK then nth 1 res2 else

            // try remaining patterns
            ...

            // try last (assume k-th) pattern
            let lam_k = ptn2lam (@pk -> rk) in
            let res_k = lam_k e in
            if nth 0 res_k == OK then nth 1 res_k else

            // inexhaustive match
            undefined // for now it's (_FAIL, _DUMMY), should be panic
    ```

    When p is ident pattern
    ```
        ptn2lam( @i -> r )
        =
        \\i -> (OK, r)      where i could occur freely in r
    ```

    When p is a constant pattern
    ```
        ptn2lam( @c -> r )
        =
        \\x -> if x == c then (OK, r) else (FAIL, _)
    ```

    When p is a tuple pattern, things gets complicated, as we got to do a lot
    of tuple unrolling.
    > The SLPJ book avoids this problem because it does not use a tuple to encode
    > match failure, rather it uses a bottom value.
    ```
        ptn2lam( @p1..pk -> r )
        =

        \\x ->
            let lam = ptn2lam p1 (ptn2lam p2 (... (ptn2lam pk r))) in

            // the 1st pattern in the tuple
            #let f0 = lam in
            let r0 = lam (nth 0 x) in
            if nth 0 r0 == FAIL then (FAIL, _) else

            #let f1 = (nth 1 r0) in
            let r1 = f1 (nth 1 x) in
            if nth 0 r1 == FAIL then (FAIL, _) else

            ...

            #let f_k-1 = (nth 1 r_k-2) in
            let r_k-1 = f_k-1 (nth k-1 x) in
            if nth 0 r_k-1 == FAIL then (FAIL, _) else

            (OK, nth 1 r_k-1)
    ```

    When p is a adt pattern, simply convert it to the tuple form
    ```
        ptn2lam( @ctor p1..pk -> r)
        =
        \\x ->
            if nth 0 x == V_ctor then
                ptn2lam (@p1..pk -> r) (nth 1 x)
            else
                (FAIL, _)
    ```

    And for the data type definitions, each constructor is transformed into a 'let'
        ```
        | ctor a1 a2

        ->

        let ctor = \\a1 -> \\a2 -> (V_ctor, (a1, a2)) in cont
        ```
"""
from .ast import *
from .astnodes import *
from ..utils import *
from ..common import *

# match expressions actually return (_OK, T) or (_FAIl, _DUMMY)
_OKVAL = 111
_ERRVAL = 222
_DUMMYVAL = 333

def ok(expr):
    return TupleNode(subs=[LitNode(val=_OKVAL), expr])

def err():
    return TupleNode(subs=[LitNode(val=_ERRVAL), LitNode(val=_DUMMYVAL)])

def is_ok(expr):
    return BinOpNode(lhs=NthNode(idx=0, expr=expr), op='==', rhs=LitNode(val=_OKVAL))

def is_err(expr):
    return BinOpNode(lhs=NthNode(idx=0, expr=expr), op='==', rhs=LitNode(val=_ERRVAL))

def unwrap(expr):
    return NthNode(idx=1, expr=expr)

def _v(name):
    return VarRefNode(name=name)


class PatMatVisitor(ASTTransformer):
    """
    Pattern matching desugaring.
    """
    VisitorName = 'PatMat'

    def __init__(self):
        self.nameidx = {}

    def genName(self, name, namespace='$'):
        suffix = self.nameidx.get(namespace, 0)
        self.nameidx[namespace] = suffix + 1
        return namespace + name + '@' + str(suffix)

    def visitTop(self, n):
        for dt in n.dataTypes:
            self(dt)
        ctorCont = rfold(joinCont, [dt.cont for dt in n.dataTypes], idfun)
        n.expr = ctorCont(self(n.expr))
        return n

    def visitDataType(self, n):
        for dt in n.ctors:
            self(dt)
        ctorCont = rfold(joinCont, [c.cont for c in n.ctors], idfun)
        n.cont = ctorCont
        return n

    def visitDataCtor(self, n):
        # use cps...
        def letk(cont):
            params = [self.genName('a') for _ in n.argTys]
            ctorRepr = TupleNode(subs=[
                LitNode(val=n.name[1]),
                TupleNode(subs=[_v(a) for a in params])])
            for a in reversed(params):
                ctorRepr = LamNode(name=a, ty=NullNode(), body=ctorRepr)
            cont = LetNode(
                    name=n.name[0],
                    ty=NullNode(),
                    val=ctorRepr,
                    body=cont)
            return cont
        n.cont = letk
        return n

    def visitMatch(self, n):
        self.visitChildren(n)
        e_name = self.genName('e')
        # TODO: inexhaustive match?
        # maybe transform the return value into a function that may panic?

        cont = err()
        for arm in reversed(n.arms):
            lam_name = self.genName('l')
            res_name = self.genName('v')

            cont = IteNode(
                    cond=is_ok(_v(res_name)),
                    tr=NthNode(idx=1, expr=_v(res_name)),
                    fl=cont)

            cont = LetNode(
                    name=res_name,
                    val=AppNode(fn=_v(lam_name), arg=_v(e_name)),
                    ty=NullNode(),
                    body=cont)

            cont = LetNode(
                    name=lam_name,
                    val=self.mkPtnLam(arm.ptn, arm.expr),
                    ty=NullNode(),
                    body=cont)

        cont = LetNode(name=e_name, val=n.expr, ty=NullNode(), body=cont)
        return cont

    def mkPtnLam(self, ptn, rhs):
        if isinstance(ptn, PtnBinderNode):
            return LamNode(
                    name=ptn.name,
                    ty=NullNode(),
                    body=ok(rhs))

        if isinstance(ptn, PtnLitNode):
            x_name = self.genName('x')

            cont = IteNode(
                    cond=BinOpNode(lhs=_v(x_name), op='==', rhs=ptn.expr),
                    tr=ok(rhs),
                    fl=err())
            cont = LamNode(
                    name=x_name,
                    ty=NullNode(),
                    body=cont)
            return cont

        if isinstance(ptn, PtnTupleNode):
            biglam = self.mkPtnLam(ptn.subs[-1], rhs)
            for ptn1 in reversed(ptn.subs[:-1]):
                biglam = self.mkPtnLam(ptn1, biglam)

            # we need to unroll it
            # In the original SLPJ book they did not use a tuple to represent the result
            # and thus avoided the problem.

            x_name = self.genName('x')
            biglam_name = self.genName('lam')
            k = len(ptn.subs)
            r_names = [ self.genName(f'r{i}') for i in range(k) ]

            # let r_n = f_nth(n), 1 <= n <= len(r_names)-1
            def f(i):
                if i == 0:
                    return _v(biglam_name)
                else:
                    return unwrap(_v(r_names[i-1]))

            cont = ok(NthNode(idx=1, expr=_v(r_names[k-1])))

            for i in range(k-1, -1, -1):
                cont = IteNode(
                        cond=is_err(_v(r_names[i])),
                        tr=err(),
                        fl=cont)

                cont = LetNode(
                        name=r_names[i],
                        ty=NullNode(),
                        val=AppNode(fn=f(i), arg=NthNode(idx=i, expr=_v(x_name))),
                        body=cont)

            cont = LetNode(
                    name=biglam_name,
                    ty=NullNode(),
                    val=biglam,
                    body=cont)

            cont = LamNode(
                    name=x_name,
                    ty=NullNode(),
                    body=cont)

            return cont

        if isinstance(ptn, PtnDataNode):
            x_name = self.genName('x')

            cont = self.mkPtnLam(PtnTupleNode(subs=ptn.subs), rhs)

            cont = IteNode(
                    cond=BinOpNode(
                        lhs=NthNode(idx=0, expr=_v(x_name)),
                        op='==',
                        rhs=LitNode(val=ptn.name[1])),
                    tr=AppNode(fn=cont, arg=NthNode(idx=1, expr=_v(x_name))),
                    fl=err())

            cont = LamNode(
                    name=x_name,
                    ty=NullNode(),
                    body=cont)

            return cont
