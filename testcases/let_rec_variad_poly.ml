let rec f = \n -> \x -> if n == 0 then x else g (n-1) x
    and g = \n -> \x -> if n == 0 then x else f (n-1) x
in
f 2 0 ;
g 0 ()
