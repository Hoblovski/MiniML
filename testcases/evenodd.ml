let rec
    even = \n : int -> if n == 0 then 1 else odd (n-1)
and odd = \n: int   -> if n == 0 then 0 else even (n-1)
in
    println (even 4) ;
    println (even 5) ;
    println (odd 4) ;
    println (odd 5)
