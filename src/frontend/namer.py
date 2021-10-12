"""
Fuck de brujin representations.
While SECD uses something like them, inside the miniML compiler we have named representation for its robustness.

Alpha conversion to make variables distinct.
For let-recs, they create 'grouped closures'.

TODO: when introducing type variables they ought to be renamed as well, in a different fashion from TypeVar.genFresh

For data types, it checks for uniqueness of type names and constructor names,
and that type/constructor names are defined before use.
It also assigns the integer label for each constructor,
by making DataCtor.name and PtnData.name a tuple (str, int).
> This should actually be a class or variant including symbol information.
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

    def defVar(self, oldName, mangle=True):
        # return: newName after alpha conversion
        # TODO: should we mangle data ctor by just prefixing them with a namespace
        newName = self.genName(oldName) if mangle else oldName
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
            print(self.vars)
            raise MiniMLLocatedError(n, f'unknown name: {n.name}')

    def visitTop(self, n):
        # check dataTypes, declare dataType ctors
        #   * ctors are not mangled
        #   * dataTypes and ctors should be unique
        #   * types are not mangled
        #   * types use a different namespace than variables but ctors do not
        #       since they behave like terms
        #   * all ident types must be defined
        self.dataTypes = []
        self.ctorLabels = {}
        for dt in n.dataTypes:
            self(dt)

        # check the expression
        self(n.expr)

    def visitDataType(self, n):
        if n.name in self.dataTypes:
            raise MiniMLLocatedError(n, f'data type {n.name} already defined')
        self.dataTypes += [n.name]
        for ctor in n.ctors:
            self(ctor)

    def visitDataCtor(self, n):
        if n.name in self.ctorLabels:
            raise MiniMLLocatedError(n, f'data constructor {n.name} already defined')
        self.ctorLabels[n.name] = len(self.ctorLabels)
        self.defVar(n.name, mangle=False)
        n.name = (n.name, self.ctorLabels[n.name])

    def visitTyData(self, n):
        if n.name not in self.dataTypes:
            raise MiniMLLocatedError(n, f'undefined data type {n.name}')

    def visitLam(self, n):
        n.name = self.defVar(n.name)
        self(n.ty)
        self(n.body)
        self.undefVar(n.name)

    def visitLetRec(self, n):
        armNames = [arm.fnName for arm in n.arms]
        if not noDuplicates(armNames):
            raise MiniMLLocatedError(n, 'duplicate names in let-rec')

        for arm in n.arms:
            self(arm.fnTy)
            self(arm.argTy)
            arm.fnName = self.defVar(arm.fnName)

        for arm in n.arms:
            arm.argName = self.defVar(arm.argName)
            self(arm.val)
            self.undefVar(arm.argName)

        self(n.body)

        for arm in reversed(n.arms):
            self.undefVar(arm.fnName)

    def visitLet(self, n):
        n.name = self.defVar(n.name)
        self(n.ty)
        self(n.val)
        self(n.body)
        self.undefVar(n.name)

    def visitMatchArm(self, n):
        ptnBinders = self(n.ptn)
        self(n.expr)
        for v in reversed(ptnBinders):
            self.undefVar(v)

    def visitPtnBinder(self, n):
        n.name = self.defVar(n.name)
        return [n.name]

    def visitPtnTuple(self, n):
        # TODO: duplicate bindings in one pattern?
        return joinlist([], [self(p) for p in n.subs])

    def visitPtnLit(self, n):
        return []

    def visitPtnData(self, n):
        if n.name not in self.ctorLabels:
            raise MiniMLLocatedError(n, f'undefined data constructor {n.name}')
        n.name = (n.name, self.ctorLabels[n.name])
        return joinlist([], [self(p) for p in n.subs])
