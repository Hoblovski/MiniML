# MiniML
ML-like functional language compiler written in Python for fun.

You may be interested in my [rewrite of miniml in Rust](https://github.com/Hoblovski/miniml-rs).

# Features
* Function as first-class citizen, higher order functions
* Compile (or transpile) to native. Uses C as backend.
* Associated IR interpreter, [RSECD](https://github.com/Hoblovski/RSECD-interp)
* Polymorphic type checking.
* Pattern matching (as powerful as in ML).
* [TODO] garbage collection
* [TODO] polymorphic types
* [TODO] optimizations
  - [Tail recursive SECD](https://www.cs.utexas.edu/users/boyer/ftp/nqthm/trsecd/trsecd.html)
  - CPS
  - Even G machine maybe?

# Usage
Requires:
* python >= 3.6
* pip of the same python version
  - And do `pip3 install -r src/requirements.txt`
* jdk >= 11
* [antlr](antlr.org)
  - Set `ANTLR_JAR` environment variable to the location of ANTLR jar
  - Set `CLASSPATH` to include that path
* gcc-multilib
  - If you want to compile to native on a 64-bit computer. (Generated native code is 32 bit).

> ANTLR is great. ANTLR+Scala and ANTLR+py is even greater.

Then
```
# Run parser generator
make grammar-py

# Usage
./miniml -h

# Run with interpreter.
./miniml -s secd testcases/higherorder.ml path/to/output.secd
cd path/to/RSECD-interp                                         # see [RSECD] below
./secdi path/to/output.secd

# Compile to native. Should be orders of magnitudes (>100x) faster than intrepreting.
export PATH=$PATH:$PWD
./minimlc testcases/higherorder.ml
./a.out                                                         # same results as interpreting
```

If you see `ModuleNotFoundError: No module named 'src.generated'`, run `make grammar-py` and then rerun your command.

# Architecture
* MiniML
* lexing parsing desugaring stuff with ANTLR
* naming: just alpha conversion pass, make all names distinct.
  - So we can use a flat dict for book-keeping.
  - maybe we should not mutate the ast... that can make bug report harder?
* typing
  - supports polymorphism e.g. `'a -> 'a` and polymorphic-let
  - hindley-milner style type checking
* patmat (once done wrong in the past)
* debrujin: convert to the nameless de brujin form for SECD emission
* [RSECD](https://github.com/Hoblovski/RSECD-interp): stack based functional IR
  - SECD with mutually recursive functions.
* C transpiler: the generated C looks really like an interpreter script, but trust me it'll be compiled.
  - and it's fast

# Lessons
Type system is good for correctness, but only a static one (not you python!).
But dynamic languages saves me a lot of code (see `ast.py` and `astnodes.py` for how I avoid AST boilerplates).
> now I got my rs-miniml, this might not be true since a macro system is (probably good) for DSL.

The interpreter is so slow... Maybe somewhere in python a careless list operation is taking O(n^2) time?

Desugaring might be good for mathematicians but not for a working compiler.
This is why we put patmat after namer/typer even though it could be before as a desugaring pass.

De brujin form is very unstable. Even if necessary, delay the conversion into it.

Python is slow. For `adt_qsort.ml`, miniml took ~1sec while rsminiml tool <0.01sec.

# Reference
* [RSECD](https://github.com/Hoblovski/RSECD-interp)
* [miniml-rs](https://github.com/Hoblovski/miniml-rs).
* [CompFun](http://www.cse.chalmers.se/edu/year/2011/course/CompFun/)
* [CAS706](https://www.cas.mcmaster.ca/~carette/CAS706/2005/Compiling%20Functional%20Programming%20Languages.pdf)
* [SoPL](https://xavierleroy.org/talks/compilation-agay.pdf)
* Various compiler books (too many to name)
* [scala phases](https://typelevel.org/scala/docs/phases.html)
* [hindley-milner introduction](https://reasonableapproximation.net/2019/05/05/hindley-milner.html)
  - for its treatment of `let rec`, still it's not polyvariadic `let rec`
