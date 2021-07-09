grammar MiniML;

top
    : expr EOF
    ;

expr
    : let
    ;

let
    : lam                                      # let0
    | 'let' Ident (':' ty)? '=' expr 'in' expr # let1    // by default recursive
    ;

lam
    : seq                                      # lam0
    | '\\' Ident ':' ty '->' expr              # lam1
    ;

seq
    : rel (';' rel)*
    ;

rel
    : add                                      # rel0
    | rel RelOp add                            # rel1
    ;

add
    : mul                                      # add0
    | add AddOp mul                            # add1
    ;

mul
    : una                                      # mul0
    | mul MulOp una                            # mul1
    ;

una
    : app                                      # una0
    | UnaOp una                                # una1
    ;

app
    : atom                                     # app0
    | app atom                                 # app1
    ;

atom
    : '(' ')'                                  # atomUnit
    | Integer                                  # atomInt
    | Ident                                    # atomIdent
    | '(' expr ')'                             # atomParen
    | 'println'                                # atomPrint
    ;

ty
    : 'unit'                                   # tyUnit
    | 'int'                                    # tyInt
    | <assoc=right> ty '->' ty                 # tyArrow
    ;

MulOp : '*' | '/' | '%' ;
AddOp : '+' | '-' ;
RelOp : '>' | '<' | '>=' | '<=' | '==' | '!=' ;
UnaOp : '-' ;

Integer
    : Digit+
    ;

Whitespace
    : [ \t\n\r]+ -> skip
    ;

Ident
    : IdentLead WordChar*
    ;

fragment IdentLead: [a-zA-Z_];
fragment WordChar: [0-9a-zA-Z_];
fragment Digit: [0-9];
