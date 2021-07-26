let a = (2, 3) in
let a = (8, a, 9) in
match a
| z, (x, y), w -> println x ; println y ; println z ; println w
| z, x, w -> println 233
end

