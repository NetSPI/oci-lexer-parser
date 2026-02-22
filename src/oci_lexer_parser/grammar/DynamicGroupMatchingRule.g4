grammar DynamicGroupMatchingRule;

/*
  OCI Dynamic Group matching_rule mini-grammar.

  Supports:
    - ALL { predicate, predicate, ... }
    - ANY { predicate, predicate, ... }
    - Nested groups produced by some UIs:
        ANY { ANY { ... }, predicate, ALL { ... } }
    - No-brace form:
        predicate, predicate, ...
        predicate
    - Optional trailing comma inside braces:
        ALL { a='1', b='2', }
*/

matchingRule
  : dgMode? groupOrList EOF
  ;

groupOrList
  : group
  | elementList
  ;

group
  : LBRACE elementList? RBRACE
  ;

elementList
  : element (COMMA element)* (COMMA)?     // allow trailing comma
  ;

element
  : dgMode? group                         // nested group may carry its own mode
  | predicate
  ;

dgMode
  : ALL
  | ANY
  ;

predicate
  : path (op literal)?
  ;

path
  : IDENT (DOT IDENT)*
  ;

op
  : EQ
  | NEQ
  ;

literal
  : STRING
  ;

// ============================================================
// Lexer
// ============================================================

ALL     : [Aa][Ll][Ll] ;
ANY     : [Aa][Nn][Yy] ;

NEQ     : '!=' ;
EQ      : '=' ;

LBRACE  : '{' ;
RBRACE  : '}' ;
COMMA   : ',' ;
DOT     : '.' ;

STRING
  : '\'' ( ESC | ~['\\] )* '\''
  ;

fragment ESC
  : '\\' [\\'nrt]
  ;

// Keep IDENT fairly permissive. Paths are formed by IDENT (DOT IDENT)*
IDENT
  : [A-Za-z0-9_-]+
  ;

// Skip whitespace INCLUDING newlines; Python parser splits rules by newline safely.
WS
  : [ \t\r\n]+ -> skip
  ;
