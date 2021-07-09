import sys
import argparse
from antlr4 import *

from .utils import *
from .generated.MiniMLLexer import MiniMLLexer
from .generated.MiniMLParser import MiniMLParser


def doParseArgs(argv):
    parser = argparse.ArgumentParser(description='MiniML compiler')
    parser.add_argument(
            'infile', type=str,
            help='input file')
    parser.add_argument(
            'outfile', default=sys.stdout, type=argparse.FileType('w'), nargs='?',
            help='output file, default is sysout')
    parser.add_argument(
            '-s', '--stage', type=str, choices={'l', 'c'},
            help='print debug info for that stage (lex, cst)')
    args = parser.parse_args()
    return args


def doLex(inputStream):
    lexer = MiniMLLexer(inputStream)
    class BailErrorListener:
        def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
            raise MiniMLError(f'lexer error at {line},{column}')
    lexer.addErrorListener(BailErrorListener())
    if args.stage == 'l':
        dumpLexerTokens(lexer)
        exit(0)
    return CommonTokenStream(lexer)


def doParse(tokenStream):
    parser = MiniMLParser(tokenStream)
    # BailErrorStrategy halts execution rather than try to recover on any parser error.
    # The Python antlr4 API has not yet exposed a get/set interface,
    # so we just assign to the error handler.
    parser._errHandler = BailErrorStrategy()
    cst = parser.top()
    if args.stage == 'c':
        print(cst.toStringTree(recog=parser))
        exit(0)
    return cst


def doConstructAST(cst):
    pass


def main(argv):
    try:
        global args
        args = doParseArgs(argv)
        inputs = FileStream(args.infile)
        tokens = doLex(inputs)
        cst = doParse(tokens)
        return 0
    except MiniMLError as e:
        if args.backtrace:
            raise e
        print(e, file=sys.stderr)
        return 1
