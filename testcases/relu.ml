let relu = \a ->
    let a = if a < 0 then 0 else a
    in a
in
    println (relu 5) ;
    println (relu (-5))
