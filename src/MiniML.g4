grammar MiniML;

top
    : expr EOF
    ;

expr
    : let
    ;

let
    : mat                                                # let_
    | 'let rec' (letRecArm ('and' letRecArm)*) 'in' expr # let1
    | 'let' Ident (':' ty)? '=' expr 'in' expr           # let2
    ;

letRecArm
    : Ident (':' t1=ty)? '=' '\\' Ident (':' t2=ty)? '->' expr
    ;

mat
    : lam                                     # mat_
    | 'match' expr ('|' ptn '->' expr)+ 'end' # mat1
    ;

ptn
    : ptn1
    ;

ptn1
    : ptn0             # ptn1_
    | ptn0 (',' ptn0)+ # ptnTuple
    ;

ptn0
    : Ident          # ptnBinder
    | '(' ptn ')'    # ptnParen
    ;

lam
    : seq                            # lam_
    | '\\' Ident (':' ty)? '->' expr # lam1
    ;

seq
    : ite (';' ite)*
    ;

ite
    : rel                            # ite_
    | 'if' rel 'then' rel 'else' ite # ite1
    ;

rel
    : add           # rel_
    | rel relOp add # rel1
    ;

add
    : mul           # add_
    | add addOp mul # add1
    ;

mul
    : una           # mul_
    | mul mulOp una # mul1
    ;

una
    : app       # una_
    | unaOp una # una1
    ;

app
    : atom     # app_
    | app atom # app1
    ;

atom
    : '(' expr (',' expr)+ ')' # atomTuple
    | lit                      # atomLit
    | Ident                    # atomIdent
    | '(' expr ')'             # atomParen
    | 'println'                # atomPrint
    | 'nth' Integer atom       # atomNth
    ;

lit
    : Integer                  # litInt
    | '(' ')'                  # litUnit
    | ('false' | 'true')       # litBool
    ;

ty
    : 'unit'                   # tyUnit
    | 'int'                    # tyInt
    | '(' ty ')'               # tyParen
    | <assoc=right> ty '->' ty # tyArrow
    ;

mulOp : '*' | '/' | '%' ;
addOp : '+' | '-' ;
relOp : '>' | '<' | '>=' | '<=' | '==' | '!=' ;
unaOp : '-' ;

Integer
    : Digit+
    ;

Whitespace
    : [ \t\n\r]+ -> skip
    ;

Ident
    : IdentLead WordChar*
    ;

Comment  : '--' (~[\r\n])* -> skip;

fragment IdentLead: [a-zA-Z_];
fragment WordChar: [0-9a-zA-Z_];
fragment Digit: [0-9];
