datatype List =
| Nil int
| Cons int List
end

-- l: List 'a, f: 'b -> 'a -> 'b
let rec foldl = \f -> \b -> \l ->
    match l
    | Nil _ -> b
    | Cons a l1 -> foldl f (f b a) l1
    end
in

-- l: List 'a, f: 'a -> 'b -> 'b
let rec foldr = \f -> \l -> \b ->
    match l
    | Nil _ -> b
    | Cons a l1 -> f a (foldr f l1 b)
    end
in

let foldl1 = \f -> \l ->
    match l
    | Cons a l1 -> foldl f a l1
    | _ -> panic ()
    end
in

let rec foldr1 = \f -> \l ->
    match l
    | Cons a (Nil _) -> a
    | Cons a l1 -> f a (foldr1 f l1)
    | _ -> panic ()
    end
in

let printl_rev = \l -> (foldr (\x -> \y -> print x) l () ; println ())
in

let printl = \l -> (foldl (\x -> \y -> print y) () l ; println ())
in

let rec printl_match = \l ->
    match l
    | Nil _ -> println ()       -- terminating 0
    | Cons v l2 -> print v ; printl_match l2
    end
in

let filterl = \f -> \l ->
    let g = \a -> \b -> if f a then Cons a b else b
    in
        foldr g l (Nil 0)
in

let appl = \l1 -> \l2 ->
    let g = \a -> \b -> Cons a b
    in
        foldr g l1 l2
in

let lenl = \l ->
    let g = \a -> \b -> b + 1
    in
        foldr g l 0
in

let rec qsortl = \l ->
    match l
    | Nil _ -> Nil 0
    | Cons v l1 ->
        let l2 = qsortl (filterl (\x -> x<=v) l1) in
        let l3 = qsortl (filterl (\x -> x>v) l1) in
            appl l2 (Cons v l3)
    end
in

let mo = 10007 in
let randf = \x -> (x*6619 + 3003) % mo in
let seed = 1293 in

let rec makel = \n ->
    if n == 1 then
        Cons seed (Nil 0)
    else (
        let l = makel (n-1) in
        match l
        | Cons v _ -> Cons (randf v) l
        | _ -> panic ()
        end
    )
in

let l = makel 10 in
printl l ;
printl (qsortl l)
