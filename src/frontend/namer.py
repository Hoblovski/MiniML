"""
Fuck de brujin representations.
While SECD uses something like them, inside the miniML compiler we have named representation for its robustness.

Alpha conversion to make variables distinct.
For let-recs, they create 'grouped closures'.

TODO: when introducing type variables they ought to be renamed as well, in a different fashion from TypeVar.genFresh
"""
from .ast import *
from .astnodes import *

class NamerVisitor(ASTVisitor):
    """
    Renaming process.

    Modifies
    * `n.name` for nodes.
    """
    VisitorName = 'Namer'

    def __init__(self):
        self.nameSuffix = {} # global for all scopes
        self.vars = []       # push and pop'ed

    def genName(self, name, namespace='_'):
        suffix = self.nameSuffix.get(name, 0)
        self.nameSuffix[name] = suffix + 1
        return namespace + name + '@' + str(suffix)

    def defVar(self, oldName):
        # return: newName after alpha conversion
        newName = self.genName(oldName)
        self.vars.append((oldName, newName))
        return newName

    def undefVar(self, newName_=None):
        oldName, newName = self.vars.pop()
        if newName_ is not None and newName != newName_:
            raise MiniMLError(f'unmatched undefVar. arg={newName_}, pop() got={newName}')

    def visitVarRef(self, n):
        for (oldName, newName) in reversed(self.vars):
            if n.name == oldName:
                n.name = newName
                break
        else:
            raise MiniMLError(f'unknown name: {n.name}')

    def visitLam(self, n):
        n.name = self.defVar(n.name)
        self(n.body)
        self.undefVar(n.name)

    def visitLetRec(self, n):
        armNames = [arm.name for arm in n.arms]
        if not noDuplicates(armNames):
            raise MiniMLError('duplicate names in let-rec')

        for arm in n.arms:
            arm.name = self.defVar(arm.name)

        for arm in n.arms:
            arm.argName = self.defVar(arm.argName)
            self(arm.val)
            self.undefVar(arm.argName)

        self(n.body)

        for arm in reversed(n.arms):
            self.undefVar(arm.name)

    def visitLet(self, n):
        n.name = self.defVar(n.name)
        self(n.val)
        self(n.body)
        self.undefVar(n.name)
