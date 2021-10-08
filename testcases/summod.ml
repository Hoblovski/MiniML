let rec summod = \n -> \mo ->
    if n == 0 then 0
    else (n + summod (n-1) mo) % mo
in
    println (summod 500 7)
