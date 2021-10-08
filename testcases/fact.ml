let rec fact = \n : int ->
    if n == 0 then
        1
    else
        n * fact (n-1)
in
    println (fact 0) ;
    println (fact 3) ;
    println (fact 6)

