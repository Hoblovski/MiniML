let rec magic = \f -> \b -> magic f (f b 0)
in

let f = magic (\x -> \y -> x+y) 0 in

let g = magic (\x -> \y -> ()) () in

0

