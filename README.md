# MiniML
Functional language compiler for fun.

# Usage
Requires:
* python >= 3.6
* pip of the same python version
  - And do `pip3 install -r src/requirements.txt`
* jdk >= 11
* [antlr](antlr.org)
  - Set `ANTLR_JAR` environment variable to the location of ANTLR jar
  - Set `CLASSPATH` to include that path

> ANTLR is great. ANTLR+Scala and ANTLR+py is even greater.

Then
```
# Examine command line args
make help

# Run with makefile, print the indented AST
make i=testcases/fact.ml e='-s ast -f indent'

# Run with interpreter.
./miniml -s secd testcases/higherorder.ml path/to/output.secd
cd path/to/RSECD-interp                                         # see [RSECD] below
./secdi path/to/output.secd

# Compile to native. Should be orders of magnitudes (>100x) faster than intrepreting.
./miniml -s c testcases/higherorder.ml higherorder.c
gcc -m32 -Isrc higherorder.c
./a.out                                                         # same result as interpreter
```

If you see `ModuleNotFoundError: No module named 'src.generated'`, run `make grammar-py` and then rerun your command.

# Architecture
* MiniML
* lexing parsing desugaring stuff
* naming: uses de brujin representation
* [TODO] typing
* [RSECD](https://github.com/Hoblovski/RSECD-interp): stack based functional IR
* C transpiler: the generated C looks really like an interpreter script, but trust me it'll be compiled.

# Features
* Function as first-class citizen, higher ordered functions
* Compile (or transpile) to native. Uses C as backend.
* Associated IR interpreter, [RSECD](https://github.com/Hoblovski/RSECD-interp)
* [TODO] custom data types
* [TODO] garbage collection
* [TODO] pattern matching
* [TODO] polymorphic types
* [TODO] optimizations
  - [Tail recursive SECD](https://www.cs.utexas.edu/users/boyer/ftp/nqthm/trsecd/trsecd.html)
  - CPS
  - Even G machine maybe?

# Lessons
Type system is good for correctness, but only a static one (not you python!).
But dynamic languages saves me a lot of code (see `ast.py` and `astnodes.py` for how I avoid AST boilerplates).

The interpreter is so slow... Maybe somewhere in python a careless list operation is taking O(n^2) time?

# Reference
* [RSECD](https://github.com/Hoblovski/RSECD-interp)
* [CompFun](http://www.cse.chalmers.se/edu/year/2011/course/CompFun/)
* [CAS706](https://www.cas.mcmaster.ca/~carette/CAS706/2005/Compiling%20Functional%20Programming%20Languages.pdf)
* [SoPL](https://xavierleroy.org/talks/compilation-agay.pdf)
* Various compiler books (too many to name)
* [scala phases](https://typelevel.org/scala/docs/phases.html)
