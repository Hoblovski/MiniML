let add: int -> int -> int =
    \x: int -> \y: int -> x + y in
let f = add 3 in
println (f 4) ;
println (add 5 6)
