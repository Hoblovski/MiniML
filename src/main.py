import sys
import argparse
from antlr4 import *

from .utils import *
from .generated.MiniMLLexer import MiniMLLexer
from .generated.MiniMLParser import MiniMLParser
from .frontend import *


def printAst(ast):
    if args.format == 'lisp':
        print(LISPStylePrintVisitor()(ast), file=args.outfile)
    elif args.format == 'indent':
        print(IndentedPrintVisitor()(ast), file=args.outfile)
    elif args.format == 'code':
        print(FormattedPrintVisitor()(ast), file=args.outfile)


def doParseArgs(argv):
    parser = argparse.ArgumentParser(description='MiniML compiler')
    parser.add_argument(
            'infile', type=str,
            help='input file')
    parser.add_argument(
            'outfile', default=sys.stdout, type=argparse.FileType('w'), nargs='?',
            help='output file, default is sysout')
    parser.add_argument(
            '-f', '--format', choices={'lisp', 'indent', 'code'}, default='lisp',
            help='AST print format')
    parser.add_argument(
            '-s', '--stage', type=str, choices={'cst', 'lex', 'ast', 'name', 'secd', 'c', 'patmat'},
            help='[Debug] print debug info for that stage')
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
    if args.stage == 'lex':
        dumpLexerTokens(lexer)
        exit(0)
    return CommonTokenStream(lexer)


def doParse(tokenStream):
    parser = MiniMLParser(tokenStream)
    cst = parser.top()
    if parser.getNumberOfSyntaxErrors() != 0:
        print('Invalid syntax.')
        exit(1)
    if args.stage == 'cst':
        print(cst.toStringTree(recog=parser), file=args.outfile)
        exit(0)
    return cst


def doConstructAST(cst):
    ast = ConstructASTVisitor().visit(cst)
    if args.stage == 'ast':
        printAst(ast)
        exit(0)
    return ast


def doPatMat(ast):
    PatMatVisitor().visit(ast)
    if args.stage == 'patmat':
        printAst(ast)
        exit(0)
    return ast


def doNamer(ast):
    NamerVisitor().visit(ast)
    if args.stage == 'name':
        printAst(ast)
        exit(0)
    return ast


def doSECD(ast):
    secd = SECDGenVisitor().visit(ast)
    if args.stage == 'secd':
        print(secd.emit(fmt='secdi'), file=args.outfile)
        exit(0)
    elif args.stage == 'c':
        print(secd.emit(fmt='c'), file=args.outfile)
        exit(0)
    return secd


def main(argv):
    try:
        global args
        args = doParseArgs(argv)
        inputs = FileStream(args.infile)
        tokens = doLex(inputs)
        cst = doParse(tokens)
        ast = doConstructAST(cst)
        ast = doPatMat(ast)
        ast = doNamer(ast)
        secd = doSECD(ast)
        return 0
    except MiniMLError as e:
        if args.backtrace:
            raise e
        print(e, file=sys.stderr)
        return 1
