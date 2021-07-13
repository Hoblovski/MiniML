import sys
import argparse
from antlr4 import *

from .utils import *
from .generated.MiniMLLexer import MiniMLLexer
from .generated.MiniMLParser import MiniMLParser
from .frontend.ast import ConstructASTVisitor, FormattedPrintVisitor
from .frontend.namer import Namer


def printAst(ast):
    if args.formatted:
        print(FormattedPrintVisitor().visit(ast))
    else:
        print(ast)


def doParseArgs(argv):
    parser = argparse.ArgumentParser(description='MiniML compiler')
    parser.add_argument(
            'infile', type=str,
            help='input file')
    parser.add_argument(
            'outfile', default=sys.stdout, type=argparse.FileType('w'), nargs='?',
            help='output file, default is sysout')
    parser.add_argument(
            '-f', '--formatted', action='store_true',
            help='Print formatted code rather than ast')
    parser.add_argument(
            '-s', '--stage', type=str, choices={'l', 'c', 'a', 'name'},
            help='[Debug] print debug info for that stage (lex, cst, ast, name)')
    parser.add_argument(
            '-bt', '--backtrace', action='store_true',
            help='[Debug] print backtrace within compiler on any error')
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
    ast = ConstructASTVisitor().visit(cst)
    if args.stage == 'a':
        printAst(ast)
        exit(0)
    return ast


def doNamer(ast):
    ast = Namer().visit(ast)
    if args.stage == 'name':
        printAst(ast)
        exit(0)
    return ast



def main(argv):
    try:
        global args
        args = doParseArgs(argv)
        inputs = FileStream(args.infile)
        tokens = doLex(inputs)
        cst = doParse(tokens)
        ast = doConstructAST(cst)
        namedAst = doNamer(ast)
        return 0
    except MiniMLError as e:
        if args.backtrace:
            raise e
        print(e, file=sys.stderr)
        return 1
