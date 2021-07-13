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
```

# Architecture
* MiniML -> lambda calculus -> stackIR

# Reference
* [CompFun](http://www.cse.chalmers.se/edu/year/2011/course/CompFun/)
* [CAS706](https://www.cas.mcmaster.ca/~carette/CAS706/2005/Compiling%20Functional%20Programming%20Languages.pdf)
* [SoPL](https://xavierleroy.org/talks/compilation-agay.pdf)
* Various compiler books (too many to name)
* [scala phases](https://typelevel.org/scala/docs/phases.html)
