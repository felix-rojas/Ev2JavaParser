# Java parser using LL(1) grammars

## Restrictions

This parser can only process:
- Main declaration
- Scopes within scopes
- Arithmetic expressions
- Parenthesized expressions
- Expression comparisons
- Numeric and String-like variable assignments
- String assignments for any character that can be a variable name 'ID'

This parser will *not* detect semantic errors such as:
- Wrong Type comparisons
    - Expressions, comparative expressions

## Complexity

### Tokenizer

The complexity in time is $O(n)$ from the technicality that the token specification is constantly defined, though the worst case is definitely in case the value belongs in the reserved keywords. It should be at least *somewhat amortized* since it is an access by key-pair in a dictionary, and is implemented in a hashmap, it should be $O(n)$ assuming the hash is bad, but average *should be* $O(1)$

### Parser

Now, the parser is another story. *Assuming* it uses a PDA implementation, it should be $O(n)$ where $n$ is the length of the text to parse since the grammar is an LL(1) type.

## Grammar for algebraic expressions

### EBNF

```
Expression ::= Term
Expression ::= Term Operator Term 
Term ::= ( Expression )
Term ::= number
Term ::= id
Operator ::= ^ | + | - | / | *
```

### Process

The problem is the `Expression:: Term Operator Term` production. Expression and Term productions do not have a common prefix factored out. 

We proceed to factor it out as Expression_prime and make it nullable. 

With these changes we now have an LL1 grammar.


### LL(1) version

```
Expression ::= Term Expression_prime
Expression_prime ::= Operator Term Expression_prime
Expression_prime ::= ''


Term ::= ( Expression )
Term ::= number
Term ::= id

Operator ::= ^
Operator ::= +
Operator ::= -
Operator ::= /
Operator ::= *
```

### Tests

```
number + number * ( number - number / number ) + number ^ id - ( id + number )
number + number + ( id * ( id - id ) )
```

## Grammar for comparison expressions

All we need for a comparison grammar is to add the comparison operators, because they follow the same structure as any binary operator!

The Expressions now include comparisons with any term, including expressions! However there might be semantic errors due to different type comparisons.

This would require *semantic parsing*, so we just skip it.

### Grammar

```
Expression ::= Term Expression_prime

Expression_prime ::= Operator Term Expression_prime

Expression_prime ::= Comp_Operator Term Expression_prime
Expression_prime ::= ''

Term ::= ( Expression )
Term ::= number
Term ::= id
Term ::= false
Term ::= true

Comp_Operator ::= &&
Comp_Operator ::= ||
Comp_Operator ::= ==
Comp_Operator ::= !=
Comp_Operator ::= >
Comp_Operator ::= >=
Comp_Operator ::= <
Comp_Operator ::= <=

Operator ::= ^
Operator ::= +
Operator ::= -
Operator ::= /
Operator ::= *

```

### LL1 Grammar
### Tests

```
( true ) != ( false )
( true ) == ( id )
( number ) >= ( id )
( number ) <= ( id )
( number ) < ( id )
( number ) > ( number )
( true && true ) == ( true )
true && true
number + number * ( number - number / number ) + number ^ id - ( id + number )
```

### Scope Grammar

```
Main ::= public static void main ( ) Scope
Scope ::= { Statement }
Statement ::= Statement || ;
```

Basically every scope is whatever statements are between our scope delimiters "{ }" and a statement can be as simple as just ";". 

We develop `Statement` to `Statements` so we can eliminate left recursion but now we have a non terminal that can end in two different non terminals!

```
Statements ::= Statement Statements
Statements ::= Statement
Statement ::= ;
```

Our grammar is ambiguous because of `Statements` which can produce multiple trees.

We simply add an intermediate state `Statements_prime` which can be nulled. This removes ambiguity completely.

However, we still need to come back from other scopes, so `Statements_prime` can also call the `Scope_prime`, which allows us to have several statements before another scope.

### Scope LL1 Grammar

```
Main ::= public static void main ( ) Main_scope
Main_scope ::= { Scope }

Scope ::= Scope_prime
Scope ::= Statements
Scope_prime ::= { Statements }

Statements ::= Statement Statements_prime
Statements_prime ::= Statements
Statements_prime ::= Scope_prime
Statements_prime ::= ''
Statement ::= ;
```

### Tests 

public static void main ( ) { ; }
public static void main ( ) { { ; { ; } } }
public static void main ( ) { ; { ; { ; } } }


### Assignment grammar

```
Statement ::= ;
Statement ::= Expression ;
Statement ::= Num_Assignment ;
Statement ::= String_Assignment ;

Num_Type ::= int
Num_Type ::= double
Num_Type ::= float

Num_Assignment ::= Num_Type id = Expression
String_Assignment ::= string id = String_like
String_like ::= quot Valid_Chars quot

Valid_Chars ::= Char Valid_Chars_prime
Valid_Chars_prime ::= Valid_Chars
Valid_Chars_prime ::= ''

Char ::= char

```

I subdivide assignments into num like and string like assignments to avoid any ambiguity and recursion directly.

### Tests
public static void main ( ) { ; { ; { string id = quot char quot ; } } }
public static void main ( ) { string id = quot char quot ; }
public static void main ( ) { int id = number * number ; }

## Full grammar

Now that we have gruesomely defined every gramamr and made sure they are all LL(1) we can join all of them together. Yes, all of them.

```
Main ::= public static void main ( ) Main_scope
Main_scope ::= { Scope }

Scope ::= Scope_prime
Scope ::= Statements
Scope_prime ::= { Statements }

Statements ::= Statement Statements_prime
Statements_prime ::= Statements
Statements_prime ::= Scope_prime
Statements_prime ::= ''

Statement ::= ;
Statement ::= Expression ;
Statement ::= Num_Assignment ;
Statement ::= String_Assignment ;

Expression ::= Term Expression_prime

Expression_prime ::= Operator Term Expression_prime

Expression_prime ::= Comp_Operator Term Expression_prime
Expression_prime ::= ''

Term ::= ( Expression )
Term ::= number
Term ::= id
Term ::= false
Term ::= true

Comp_Operator ::= &&
Comp_Operator ::= ||
Comp_Operator ::= ==
Comp_Operator ::= !=
Comp_Operator ::= >
Comp_Operator ::= >=
Comp_Operator ::= <
Comp_Operator ::= <=

Operator ::= ^
Operator ::= +
Operator ::= -
Operator ::= /
Operator ::= *

Num_Type ::= int
Num_Type ::= double
Num_Type ::= float

Num_Assignment ::= Num_Type id = Expression
String_Assignment ::= string id = String_like
String_like ::= quot Valid_Chars quot

Valid_Chars ::= Char Valid_Chars_prime
Valid_Chars_prime ::= Valid_Chars
Valid_Chars_prime ::= ''

Char ::= char

```

public static void main ( ) { float id = number ; { string id = quot char quot ; int id = number + id ; number != id ; ( id && id ) ; } }

### Translated grammar

We can now transform this grammar for our tokenizer and parser as follows:

```
Main -> public static void main 'L_PAR' 'R_PAR' Main_scope
Main_scope -> 'L_CUR' Scope 'R_CUR'

Scope -> Scope_prime
Scope -> Statements
Scope_prime -> 'L_CUR' Statements 'R_CUR'

Statements -> Statement Statements_prime
Statements_prime -> Statements
Statements_prime -> Scope_prime
Statements_prime ->

Statement -> 'END'
Statement -> Expression 'END'
Statement -> Num_Assignment 'END'
Statement -> String_Assignment 'END'

Expression -> Term Expression_prime

Expression_prime -> Operator Term Expression_prime

Expression_prime -> Comp_Operator Term Expression_prime
Expression_prime -> 

Term -> 'L_PAR' Expression 'R_PAR'
Term -> 'NUMBER'
Term -> 'ID'
Term -> 'TRUE'
Term -> 'FALSE'

Comp_Operator -> 'AMPERSAND' 'AMPERSAND'
Comp_Operator -> 'PIPE' 'PIPE'
Comp_Operator -> 'ASSIGN' 'ASSIGN'
Comp_Operator -> 'NOT' 'ASSIGN'
Comp_Operator -> 'MORE'
Comp_Operator -> 'MORE' 'ASSIGN'
Comp_Operator -> 'LESS'
Comp_Operator -> 'LESS' 'ASSIGN'

Operator -> 'POW'
Operator -> 'PLUS'
Operator -> 'MINUS'
Operator -> 'DIV'
Operator -> 'MULT'


Num_Assignment -> 'NUMTYPE' 'ID' 'ASSIGN' Expression
String_Assignment -> string 'ID' 'ASSIGN' String_like
String_like -> 'QUOT' Valid_Chars 'QUOT'

Valid_Chars -> Char Valid_Chars_prime
Valid_Chars_prime -> Valid_Chars
Valid_Chars_prime -> 

Char -> Statements
```

