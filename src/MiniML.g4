grammar MiniML;

top
    : expr EOF
    ;

expr
    : let
    ;

let
    : lam # let0
    | 'let' Ident (':' ty)? '=' expr 'in' expr # let1    // by default recursive
    ;

lam
    : seq # lam0
    | '\\' Ident ':' ty '->' expr  # lam1
    ;

seq
    : rel   # seq0
    | rel ';' seq                # seq1
    ;

rel
    : add # rel0
    | rel op=RelOp add # rel1
    ;

add
    : mul # add0
    | add op=AddOp mul # add1
    ;

mul
    : una # mul0
    | mul op=MulOp una # mul1
    ;

una
    : app # una0
    | op=UnaOp una # una1
    ;

app
    : atom # app0
    | app atom # app1
    ;

atom
    : '(' ')' # atomUnit
    | Integer # atomInt
    | Ident # atomIdent
    | '(' expr ')' # atomParen
    | 'println' # atomPrint
    ;

ty
    : 'unit'
    | 'int'
    | <assoc=right> ty '->' ty
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
