import nltk
import re
from nltk import Nonterminal, nonterminals, Production, CFG
from typing import NamedTuple

nltk.download('punkt')
nltk.download('words')
nltk.download('treebank')


class JavaToken(NamedTuple):
  type: str
  value: str
  line: int
  col: int

def tokenize(code):
  reserved_words = {
      "NUMTYPE" : {"int" : 1, "double" : 2, "double" :3, "short" : 4, "float" :5},
      "TYPES": { "enum" :1, "char" :2 , "String" : 3, "boolean" :4},
      "KEYWORDS": {"public", "static", "void", "main", "abstract", "continue", "for", "new", "switch","assert" , "default", "package", "synchronized", "do", "goto", "private", "this","break" ,  "implements", "throw", "byte", "import", "throws","case" ,  "instanceof", "return", "transient","catch" , "extends",  "try", "final", "interface", "static","class", "finally",  "strictfp", "volatile","const",  "native", "super", "while","_"}
  }

  token_specification = [
        ('NOT',   r'\!'),  
        ('PIPE',   r'\|'),  
        ('AMPERSAND',   r'\&'),  
        ('TRUE',   r'true'),  
        ('FALSE',   r'false'),  
        ('POW',   r'\^'),  
        ('DIV',   r'\/'),  
        ('MULT',   r'\*'),  
        ('MINUS',   r'\-'),  
        ('PLUS',   r'\+'),  
        ('QUOT',   r'\"'),  
        ('DOT',   r'\.'),  # Dot
        ('L_BRKT',   r'\['),  # Left bracket
        ('R_BRKT',   r'\]'),  # Right bracket
        ('L_PAR',   r'\('),  # Left parenthesis
        ('R_PAR',   r'\)'),  # Right parenthesis
        ('L_CUR',   r'\{'),  # Left curly
        ('R_CUR',   r'\}'),  # Right curly
        ('NUMBER',   r'\d+(\.\d*)?'),  # Number
        ('ASSIGN',   r'='),            # Assignment operator
        ('LESS',     r'[\<]'),       # Comparison operators
        ('MORE',     r'[\>]'),       # Comparison operators
        ('END',      r';'),            # Statement terminator
        ('ID',       r'\$*[\$_a-zA-Z]+[\$_a-zA-Z\d]*\$*'),    # Identifiers
        ('SKIP',     r'\s+'),    # Skip over spaces, tabs and nl
        ('MISMATCH', r'.'),            # Any other character
    ]
  tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
  line_num = 1
  line_start = 0
  for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start
        if kind == 'NUMBER':
          if '.' in value:
            value = float(value)
          else:
            value = int(value)
        elif value in reserved_words['NUMTYPE']:
          kind = 'NUMTYPE'
        elif value in reserved_words['KEYWORDS']:
            kind = value
        elif value in reserved_words['TYPES']:
            kind = value
        elif kind == 'ID' and value == 'Main':
          kind = 'Main'
        elif kind == 'ID' and value == 'main':
          kind = 'main'
        elif kind == 'NEWLINE':
            line_start = mo.end()
            line_num += 1
            continue
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f'{value!r} unexpected on line {line_num}')
        yield JavaToken(kind, value, line_num, column)

grammar = CFG.fromstring("""
Main -> 'public' 'static' 'void' 'main' 'L_PAR' 'R_PAR' Main_scope
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
String_Assignment -> 'String' 'ID' 'ASSIGN' String_like
String_like -> 'QUOT' Valid_Chars 'QUOT'

Valid_Chars -> Char Valid_Chars_prime
Valid_Chars_prime -> Valid_Chars
Valid_Chars_prime -> 

Char -> 'ID'
""")

# Create a parser with the defined grammar
parser = nltk.ChartParser(grammar)
grammar.productions()

test_sentences = [
'''public static void main ( ) { ; { ; { String id = "thing" ; } } } ''',
'''public static void main ( ) { String id = "as a thing" ; } ''',
'''public static void main ( ) { int id = 28 * 2.3 ; }''',
'''public static void main ( ) { ; } ''',
'''
public static void main ( ) { float id = 2.8 ; { String id = " character adn others " ; int id = 2 + id ; 8 != id ; ( id >= id ) ; } }
''',
'''public static void main ( ) { ; }''',
'''public static void main ( ) { { ; { ; } } }''',
'''public static void main ( ) { ; { ; { ; } } }''',
'''public static void main ( ) { ( true ) != ( false ) ; }''',
'''public static void main ( ) { ( true ) == ( id ) ; }''',
'''public static void main ( ) { ( 2.0 ) >= ( id ) ; }''',
'''public static void main ( ) { ( 22.0 ) <= ( id ) ; }''',
'''public static void main ( ) { ( 2.0 ) < ( id ) ; }''',
'''public static void main ( ) { ( 2 ) > ( 28 ) ; }''',
'''public static void main ( ) { ( true && true ) == ( true ) ; }''',
'''public static void main ( ) { true && true ; }''',
'''public static void main ( ) { 28 + 28 * ( 28 - 28 / 28 ) + 28 ^ id - ( id + 28 ) ; }''',
]

token_lists = []
for sentence in test_sentences:
    tokens = tokenize(sentence)
    t_list = []
    for t in tokens:
        t_list.append(t.type)
    token_lists.append(t_list)

count = 0
for token_list in token_lists:
    print("---- Different tree -----")
    for tree in parser.parse(token_list):
        print("---- Same tree -----")
        count += 1
        tree.pretty_print()

# Numbers have to match 
if len(test_sentences) == count:
    print("No ambiguity!")