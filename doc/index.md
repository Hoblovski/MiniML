# Documentation
should in future become a blog series.

------------------------------------------------------------------------------
# SECD machine
.

my special treatment for recursive function groups.

------------------------------------------------------------------------------
# PatMat translation
Borrowed from SLPJ. see PatMat.py.

------------------------------------------------------------------------------
# Type checking
Hindley Milner

The type checker is cleverer than you!
* Me once written the wrong higher_order.ml and debugged for 2 hours. In the end I found my original annotations were wrong.
* While trying to type check tup_list.ml, the checker went to a infinite loop -- exactly desired behavior since there was no recursive type support then.

## Let Polymorphism
Two ways.
1. As in TAPL book, associate different type variables with each use.
  - This is essentially restricted universal types.
2. So called type schemes as in [cs3110](https://www.cs.cornell.edu/courses/cs3110/2020fa/textbook/interp/letpoly.html)
  - Oh I just realized in essence they are the same thing.

But polymorphic let-recs require careful thought on bound variables.


## Typeclasses
not implemented

------------------------------------------------------------------------------
# Playing with dynamic python
.

