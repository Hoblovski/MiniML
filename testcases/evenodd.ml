let rec
    even (n : int) = if n == 0 then 1 else odd (n-1)
and odd (n: int)   = if n == 0 then 0 else even (n-1)
in
    print (even 4) ;
    print (even 5) ;
    print (odd 4) ;
    print (odd 5)
