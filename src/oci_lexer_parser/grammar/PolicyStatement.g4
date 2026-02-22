grammar PolicyStatement;

// ==================== Entry points (multi-statement) ====================
statements  : statement+ EOF ;
statement   : allowStmt | defineStmt | admitStmt | endorseStmt ;

// ==================== Allow/Deny statement ====================
// Multiple subjects are allowed via name/id lists (e.g., "group A, B").
allowStmt   : effect subject TO verb (resource)? IN location (WHERE conditionExpr)? ;
effect      : ALLOW | DENY ;

subject
    : ANY_GROUP                                 #AnyGroup
    | ANY_USER                                  #AnyUser
    | SERVICE nameList                          #ServiceSubject   // list of services
    | GROUP nameList                            #GroupByName
    | GROUP idList                              #GroupById
    | DYNAMIC_GROUP nameList                    #DynGroupByName
    | DYNAMIC_GROUP idList                      #DynGroupById
    ;

// -------------------- Verb ----------------------
verb
    : MANAGE
    | USE
    | READ
    | INSPECT
    | WORD                                      // fallback for service-defined verbs
    | LBRACE WORD (COMMA WORD)* RBRACE          // {KEY_READ} or {A,B,C}
    ;

// -------------------- Resource ------------------
resource
    : ALL_RESOURCES
    | WORD                                      // vcns, instances, groups, audit-events, ...
    ;

// -------------------- Location ------------------
location
    : TENANCY                                   #LocTenancy
    | COMPARTMENT ID ocid                       #LocCompartmentId
    | COMPARTMENT compartmentPath               #LocCompartmentName
    ;

compartmentPath : name (COLON name)* ;

// -------------------- Lists & names/ocids -------
nameList : qualifiedName (COMMA qualifiedName)* ;
idList   : ID ocid (COMMA ID ocid)* ;

qualifiedName : name (SLASH name)? ;
name          : WORD | QUOTED ;
ocid          : OCID | QUOTED_OCID ;

// ==================== DEFINE statement ====================
defineStmt
    : DEFINE defineTarget AS (ID)? ocid
    ;

defineTarget
    : TENANCY name
    | GROUP qualifiedName
    | DYNAMIC_GROUP qualifiedName
    | COMPARTMENT name
    ;

// ==================== ADMIT statement ====================
// Plural subjects allowed; base mode rejects >1.
admitStmt
    : (DENY)? ADMIT subject (OF TENANCY name)? TO verb (resource)? IN location (WHERE conditionExpr)?
    ;

// ==================== ENDORSE statement ====================
// Plural subjects allowed; base mode rejects >1.
// Support multiple endorse scopes (targets): "IN TENANCY A, TENANCY B, ANY-TENANCY"
endorseStmt
    : (DENY)? ENDORSE subject TO endorseVerb resource IN endorseScope (WHERE conditionExpr)?
    ;

endorseVerb
    : verb
    | ASSOCIATE
    ;

endorseScope
    : ANY_TENANCY
    | TENANCY name
    ;

// ==================== Conditions (incl. time ops) ====================
conditionExpr
    : conditionGroup
    | condition
    ;

conditionGroup
    : (ANY | ALL) LBRACE conditionExpr (COMMA conditionExpr)* RBRACE
    ;

condition
    : WORD (EQ | NEQ) condValue                                  #CondEq
    | WORD IN LPAREN condValue (COMMA condValue)* RPAREN         #CondIn
    | WORD BEFORE condValue                                      #CondBefore
    | WORD AFTER  condValue                                      #CondAfter
    | WORD BETWEEN condValue AND condValue                       #CondBetween
    ;

condValue
    : QUOTED
    | QUOTED_OCID
    | OCID
    | PATTERN
    | WORD
    ;

// ==================== Lexer ====================
ALLOW         : A L L O W ;
DENY          : D E N Y ;
TO            : T O ;
IN            : I N ;
WHERE         : W H E R E ;
DEFINE        : D E F I N E ;
AS            : A S ;
ADMIT         : A D M I T ;
OF            : O F ;
ENDORSE       : E N D O R S E ;
ASSOCIATE     : A S S O C I A T E ;

GROUP         : G R O U P ;
DYNAMIC_GROUP : D Y N A M I C '-' G R O U P ;
ANY_GROUP     : A N Y '-' G R O U P ;
ANY_USER      : A N Y '-' U S E R ;
SERVICE       : S E R V I C E ;
COMPARTMENT   : C O M P A R T M E N T ;
TENANCY       : T E N A N C Y ;
ANY_TENANCY   : A N Y '-' T E N A N C Y ;
ID            : I D ;

MANAGE        : M A N A G E ;
USE           : U S E ;
READ          : R E A D ;
INSPECT       : I N S P E C T ;

ANY           : A N Y ;
ALL           : A L L ;
ALL_RESOURCES : A L L '-' R E S O U R C E S ;

BEFORE        : B E F O R E ;
AFTER         : A F T E R ;
BETWEEN       : B E T W E E N ;
AND           : A N D ;

COMMA         : ',' ;
SLASH         : '/' ;
COLON         : ':' ;
LBRACE        : '{' ;
RBRACE        : '}' ;
LPAREN        : '(' ;
RPAREN        : ')' ;
EQ            : '=' ;
NEQ           : '!=' ;

// ---- String/OCID/PATTERN/WORD ----
OCID          : 'ocid1.' ~[ \t\r\n,}]+ ;
QUOTED_OCID   : '\'' 'ocid1.' ~['\r\n]* '\'' ;

// Support escaped sequences (e.g., '\/', '\n', '\x'), without interpreting them here.
PATTERN       : '/' ( ESC | ~[/\r\n] )* '/' ;

WORD          : [A-Za-z0-9] [A-Za-z0-9._-]* ;
QUOTED        : '\'' ( ESC | ~['\\\r\n] )* '\'' ;
fragment ESC  : '\\' . ;

WS            : [ \t\r\n]+ -> skip ;
OTHER         : . -> skip ;

// ---- Fragments for case-insensitive keywords ----
fragment A:[aA]; fragment B:[bB]; fragment C:[cC]; fragment D:[dD]; fragment E:[eE];
fragment F:[fF]; fragment G:[gG]; fragment H:[hH]; fragment I:[iI]; fragment J:[jJ];
fragment K:[kK]; fragment L:[lL]; fragment M:[mM]; fragment N:[nN]; fragment O:[oO];
fragment P:[pP]; fragment Q:[qQ]; fragment R:[rR]; fragment S:[sS]; fragment T:[tT];
fragment U:[uU]; fragment V:[vV]; fragment W:[wW]; fragment X:[xX]; fragment Y:[yY];
fragment Z:[zZ];
