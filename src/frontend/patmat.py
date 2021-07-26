"""
Convert pattern matching into plain lambda.

Done before Namer and Typer.
-- Before namer: uses compiler generated names
   - why not after: this pass introduces temporary variables which is likely to
     break de brujin indices.
     Possibly to get around, but I do not want work with de brujin variables.
-- Before typer: may not have good type error info.


Translation scheme:

    Translating into pattern lambdas with a ptn2lam function.

        ptn2lam(ptn, rhs): lam

    Since lambdas does it automatically, we need not worry about name binding.
    @p -> r     is transformed into     \\args ... -> (OK|FAIL, r)

    A match expression is translated as
    ```
        match e
        | p1 -> r1
        | p2 -> r2
        | ...
        | pk -> rk
        end

        =>

        let e_i = e in // pushenv so we can reuse it

            // try first pattern
            let v1 = (ptn2lam (@p1 -> r1)) e_i in
            if nth 0 v1 == OK then nth 1 v1 else

            // try second pattern
            let v2 = (ptn2lam (@p2 -> r2)) e_i in
            if nth 0 v2 == OK then nth 1 v2 else
            ...

            // try last pattern
            let v_k = (ptn2lam (@p_k -> r_k)) e_i in
            if nth 0 v_k == OK then nth 1 v_k else

            // inexhaustive match
            undefined
    ```

    When p is ident pattern
    ```
        ptn2lam( @i -> r )
        =
        \\i -> (OK, r)
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
            let ptnlam = ptn2lam p1 (ptn2lam p2 (... (ptn2lam pk r))) in

            // the 1st pattern in the tuple
            let r0 = ptnlam (nth 0 x) in
            if nth 0 r0 == FAIL then (FAIL, _) else

            let r1 = (nth 1 r0) (nth 1 x) in
            if nth 0 r1 == FAIL then (FAIL, _) else

            ...

            let r_k-2 = (nth 1 r_k-3) (nth k-2 x) in
            if nth 0 r_k-2 == FAIL then (FAIL, _) else

            let r_k-1 = (nth 1 r_k-2) (nth k-1 x) in
            r_k-1
    ```
"""
from .ast import *
from .astnodes import *

_FAIL = 22
_OK = 11
_DUMMY = 0

class PatMatVisitor(ASTTransformer):
    """
    De brujin style alpha conversion
    """
    VisitorName = 'PatMat'

    def __init__(self):
        self.nameidx = {}

    def genName(self, namespace):
        idx = self.nameidx.get(namespace, 0)
        self.nameidx[namespace] = idx + 1
        return f'{namespace}_{idx}'

    def visitMatch(self, n):
        e_i = self.genName('e')
        # TODO: inexhaustive match? maybe transform the return value into a function that may panic?
        body = TupleNode(pos=n.pos, subs=[LitNode(val=_FAIL), LitNode(val=_DUMMY)])
        for arm in reversed(n.arms):
            v_i = self.genName('v')
            pl_i = self.genName('pl')
            ptnLamRes = LetNode(
                    name=pl_i,
                    val=self.mkPtnLam(arm.ptn, arm.expr),
                    ty=TyUnkNode(),
                    body=AppNode(pos=arm.pos,
                        fn=VarRefNode(name=pl_i),
                        arg=VarRefNode(pos=arm.pos, name=e_i)))
            v_i_nth = lambda n: NthNode(pos=arm.pos, idx=n, expr=VarRefNode(name=v_i))
            bodyIte = IteNode(pos=arm.pos,
                        cond=BinOpNode(pos=arm.pos,
                            lhs=v_i_nth(0),
                            op='==',
                            rhs=LitNode(pos=arm.pos, val=_OK)),
                        tr=v_i_nth(1),
                        fl=body)
            body = LetNode(pos=arm.pos, name=v_i, val=ptnLamRes, ty=TyUnkNode(), body=bodyIte)
        return LetNode(pos=n.pos, name=e_i, val=n.expr, ty=TyUnkNode(), body=body)

    def mkPtnLam(self, ptn, rhs):
        if isinstance(ptn, IdentPtnNode):
            return LamNode(pos=ptn.pos,
                    name=ptn.name, ty=TyUnkNode(),
                    body=TupleNode(pos=rhs.pos,
                        subs=[LitNode(pos=rhs.pos, val=_OK), rhs]))

        if isinstance(ptn, TuplePtnNode):
            ptnlam = self.mkPtnLam(ptn.subs[-1], rhs)
            for ptn1 in reversed(ptn.subs[:-1]):
                ptnlam = self.mkPtnLam(ptn1, ptnlam)
            # ptnlam is a big nested lambda
            # we need to unroll it
            # In the original SLPJ book they did not use a tuple to represent the result
            # and thus avoided the problem.

            x_i = self.genName('x')
            rs = [ self.genName(f'r{i}') for i in range(len(ptn.subs)) ]
            ptnlam_i = self.genName('ptnlam')

            # let r_n = f_nth(n), 1 <= n <= len(rs)-1
            f_nth = lambda n: AppNode(
                fn=NthNode(idx=1, expr=VarRefNode(name=rs[n-1])),
                arg=NthNode(idx=n, expr=VarRefNode(name=x_i)))
            f_0th = AppNode(
                fn=VarRefNode(name=ptnlam_i),
                arg=NthNode(idx=0, expr=VarRefNode(name=x_i)))

            body = VarRefNode(name=rs[-1])

            for idx in range(len(rs)-2, -1, -1):
                body = LetNode(
                        name=rs[idx+1],
                        val=f_nth(idx+1),
                        ty=TyUnkNode(),
                        body=body)
                body = IteNode(
                        cond=BinOpNode(
                            lhs=NthNode(
                                idx=0,
                                expr=VarRefNode(name=rs[idx])),
                            op='==',
                            rhs=LitNode(val=_FAIL)),
                        tr=TupleNode(subs=[
                            LitNode(val=_FAIL), LitNode(val=_DUMMY)]),
                        fl=body)

            body = LetNode(
                    name=rs[0],
                    val=f_0th,
                    ty=TyUnkNode(),
                    body=body)
            body = LetNode(
                    name=ptnlam_i,
                    val=ptnlam,
                    ty=TyUnkNode(),
                    body=body)

            return LamNode(pos=ptn.pos,
                    name=x_i,
                    ty=TyUnkNode(),
                    body=body)
