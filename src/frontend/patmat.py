"""
Convert pattern matching into plain lambda.

Done before Namer and Typer.
-- Before namer: uses compiler generated names
   - why not after: this pass introduces temporary variables which is likely to
     break de brujin indices.
     Possibly to get around, but I do not want work with de brujin variables.
-- Before typer: may not have good type error info.
"""
from .ast import *
from .astnodes import *

class PatMatVisitor(ASTTransformer):
    VisitorName = 'PatMat'
