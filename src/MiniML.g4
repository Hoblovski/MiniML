grammar MiniML;

top
    : expr EOF
    ;

expr
    : let
    ;

let
    : lam                                                # let0
    | 'let rec' (letRecArm ('and' letRecArm)*) 'in' expr # let1
    | 'let' Ident (':' ty)? '=' expr 'in' expr           # let2
    ;

letRecArm
    : Ident Ident '=' expr
    | Ident '(' Ident ':' ty ')' '=' expr
    ;

lam
    : seq                                                # lam0
    | '\\' Ident (':' ty)? '->' expr                     # lam1
    ;

seq
    : ite (';' ite)*
    ;

ite
    : rel                                                # ite0
    | 'if' rel 'then' rel 'else' ite                     # ite1
    ;

rel
    : add                                                # rel0
    | rel relOp add                                      # rel1
    ;

add
    : mul                                                # add0
    | add addOp mul                                      # add1
    ;

mul
    : una                                                # mul0
    | mul mulOp una                                      # mul1
    ;

una
    : app                                                # una0
    | unaOp una                                          # una1
    ;

app
    : atom                                               # app0
    | app atom                                           # app1
    ;

atom
    : '(' ')'                                            # atomUnit
    | Integer                                            # atomInt
    | Ident                                              # atomIdent
    | '(' expr ')'                                       # atomParen
    | 'println'                                          # atomPrint
    ;

ty
    : 'unit'                                             # tyUnit
    | 'int'                                              # tyInt
    | '(' ty ')'                                         # tyParen
    | <assoc=right> ty '->' ty                           # tyArrow
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
