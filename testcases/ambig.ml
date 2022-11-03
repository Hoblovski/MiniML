-- ambiguous: the second x if interpreted as a type, then it's (\x : (int -> x) - 5) and fail.
-- this is not a trouble for cfg.
(\x : int -> x - 5) 5
