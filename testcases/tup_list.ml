-- discriminator: 0 for NIL, 1 for cons


let randst = 41231312
in
let mo = 65537
in
let plus = \x -> \y -> x+y
in
let maxint = 2147483647
in
let minint = 0- maxint
in
let min = \x -> \y -> if x < y then x else y
in


let rec lmake n = \f ->
    if n == 0 then (
        (0, 0, 0)
    ) else (
        let v = f n in
        let l1 = lmake (n-1) f in
        (1, v, l1)
    )
in
let rec lprint l =
    (match l
    | d, v, l -> if d == 0 then 0 else (println v ; lprint l ; 0)
    end)
in
let rec foldl f = \b -> \l ->
    (match l
    | d, v, l ->
        if d == 0 then
            b
        else
            foldl f (f b v) l
    end)
in
let lsum = foldl plus 0
in
let lmin = foldl min maxint
in
let lcons = \v -> \l -> (1, v, l)
in
let lnil = (0, 0, 0)
in
let lsingleton = \v -> lcons v lnil
in
let lfilter = \f -> foldl (\b -> \a -> if f a then lcons a b else b) lnil
in
let rec lapp l1 = \l2 ->
    (match l1
    | d, v, l ->
        if d == 0 then
            l2
        else
            lcons v (lapp l l2)
    end)
in


-- strange that it seems this qsort takes O(n^2) time?
let rec qsort l = (
    (match l
    | d, v, l ->
        if d == 0 then
            lnil
        else (
            let leq = qsort (lfilter (\x -> x<=v) l) in
            let lgt = qsort (lfilter (\x -> x>v) l) in
            lapp leq (lcons v lgt))
    end)
)
in
let rec sorted l =
    (match l
    | d, v1, l ->
        if d == 0 then (
            1
        ) else (
            match l
            | d, v2, xxx ->
                if d == 0 then (
                    1
                ) else (
                    if (v1 <= v2) then
                        sorted l
                    else
                        0
                )
            end
        )
    end)
in


let idfn = \x -> x in
let sqrfn = \x -> x*x in
let randfn = \x -> (x*20101 + 40111) % mo in
let l = lapp (lmake 2000 randfn) (lapp (lmake 5 sqrfn) (lmake 3 idfn)) in
println (sorted l) ;
println (sorted (qsort l))
