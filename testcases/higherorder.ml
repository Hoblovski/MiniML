-- Factory method for factorials

let dot: (int -> int) -> (int -> int) -> (int -> int) =
    \f -> \g -> \x -> f (g x)
in

let dollar: (int -> int) -> int -> int =
    \f -> \x -> f x
in

let factgen: (int -> int) -> (int -> int) = \post ->
    let base = 1 in
    let zero = 0 in
    let step = 1 in
    let mul = \a: int -> \b: int -> a * b in
    let rec fact = \n : int ->
        if n == zero then
            base
        else
            mul n (fact (n-step))
    in
        dollar (dot post) fact
in

let fact = factgen (\x -> x)
in

let factp1 = factgen (\x -> x+1)
in

let builtinf = println in

builtinf (builtinf (dollar fact 0) ) ;
builtinf (dollar fact 7) ;
builtinf (dollar factp1 3) ;
builtinf (builtinf (dollar factp1 5))

