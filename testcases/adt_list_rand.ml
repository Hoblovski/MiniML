datatype List =
| Nil int
| Cons int List
end

let rec makel = \n -> \f ->
    if n == 0 then (
        Nil ()
    ) else (
        Cons (f n) (makel (n-1) f)
    )
in

let rec printl = \l ->
    match l
    | Nil _ -> ()
    | Cons v l2 -> println v ; printl l2
    end
in

let mo = 65537 in
let randf = \x -> (x*20101 + 40111) % mo in

let l = makel 3 randf in
printl l
