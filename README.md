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

# Typical usage
make i=testcases/fact.ml e='-s fmt'

# Run with interpreter
./miniml -s secd testcases/higherorder.ml  path/to/output.secd
cd path/to/RSECD-interp         # see [RSECD] below
./secdi path/to/output.secd
```

# Architecture
* MiniML
* lexing parsing desugaring stuff
* naming: uses de brujin representation
* [TODO] typing
* [RSECD](https://github.com/Hoblovski/RSECD-interp): stack based functional IR

# Features
* Function as first-class citizen, higher ordered functions
* [TODO] custom data types
* [TODO] pattern matching
* [TODO] polymorphic types
* [TODO] optimizations
* [TODO] compile to native

# Lessons
Programmers who like to use type systems to ensure the correctness of their program are advised not to use python.

# Reference
* [RSECD](https://github.com/Hoblovski/RSECD-interp)
* [CompFun](http://www.cse.chalmers.se/edu/year/2011/course/CompFun/)
* [CAS706](https://www.cas.mcmaster.ca/~carette/CAS706/2005/Compiling%20Functional%20Programming%20Languages.pdf)
* [SoPL](https://xavierleroy.org/talks/compilation-agay.pdf)
* Various compiler books (too many to name)
* [scala phases](https://typelevel.org/scala/docs/phases.html)
