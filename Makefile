ANTLR_JAR ?= /usr/local/lib/antlr-4.8-complete.jar
i ?= i.ml
o ?=
e ?=
LANGNAME = MiniML
RUNCMD = python3 -m src $(EXTRA_ARGS)

CLASSPATH = $(ANTLR_JAR):generated

all: run

help: grammar-py
	$(RUNCMD) --help

run: grammar-py
	$(RUNCMD) $(i) $(o) $(e)

cst: grammar-java
	java -cp $(CLASSPATH) org.antlr.v4.gui.TestRig $(LANGNAME) top -gui $(i)

grammar-java:
	cd src && java -jar $(ANTLR_JAR) -o ../generated $(LANGNAME).g4
	javac -cp $(CLASSPATH) generated/*.java

grammar-py:
	cd src && java -jar $(ANTLR_JAR) -Dlanguage=Python3 -visitor -o generated $(LANGNAME).g4

clean:
	rm -rf generated src/generated
	find . -name __pycache__ | xargs rm -rf

.PHONY: all clean run cst grammar-java grammar-py help
