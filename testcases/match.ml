let a = (1, (2, 3)) in
match a
| x, (2, z) -> println 222 ; println (x + z)
| x, (y, z) -> println (x + y + z)
end
