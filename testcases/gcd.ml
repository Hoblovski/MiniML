let rec gcd = \a -> \b ->
    if a == 0 then
        b
    else
        gcd (b % a) a
in
    println (gcd 8 12) ;
    println (gcd 6 (gcd 8 12))
