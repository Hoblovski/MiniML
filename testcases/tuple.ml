let a = (1, 2) in
    println ((nth 0 a)*10 + (nth 1 a)) ;
    (let b = (2, 3, 4, 5) in
        println (
            (nth 0 b)*1000+
            (nth 1 b)*100+
            (nth 2 b)*10+
            (nth 3 b)*1)
        ;

        (let c = (5, (2, 3), 6) in
            println (nth 0 c) ;
            println (nth 1 c) ;
            println (nth 2 c))
    )
