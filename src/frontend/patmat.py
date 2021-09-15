"""
Bad design. Should come after typer and namer.
"""
from .ast import *
from .astnodes import *

class PatMatVisitor(ASTTransformer):
    pass
