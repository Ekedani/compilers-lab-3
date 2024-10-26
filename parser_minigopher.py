from lexer_minigopher import lex
from lexer_minigopher import table_of_symbols

f_success = lex()

print('-' * 30)
print('table_of_symbols:{0}'.format(table_of_symbols))
print('-' * 30)

num_row = 1  # Номер поточної лексеми
len_table_of_symbols = len(table_of_symbols)  # Довжина таблиці лексем


def run_parser():
    """
    Функція для розбору програми за правилом Program = { Declaration } MainSection.
    :return: True якщо розбір успішний, інакше викликає SystemExit
    """
    try:
        parse_declaration_list()
        parse_main_section()
        print('Parser: Синтаксичний аналіз завершився успішно')
        return True
    except SystemExit as e:
        print('Parser: Аварійне завершення програми з кодом {0}'.format(e))
        return False


def parse_declaration_list():
    """
    Функція для розбору списку декларацій {Declaration}
    """
    print(next_indt() + 'parse_declaration_list():')
    while parse_declaration():
        pass
    pred_indt()


def parse_declaration():
    """
    Функція для розбору однієї декларації за правилом:
    Declaration = VariableDecl | ShortVariableDecl | ConstDecl
    """
    num_line, lexeme, token = get_symbol()
    if lexeme == 'var':
        parse_variable_decl()
    elif lexeme == 'const':
        parse_const_decl()
    elif token == 'id' and check_next_token(':='):
        parse_short_variable_decl()
    else:
        return False
    return True


def parse_variable_decl():
    """
    Функція для розбору декларації змінної:
    VariableDecl = 'var' Identifier TypeSpec [ '=' Expression ] ';'
    """
    print(next_indt() + 'parse_variable_decl():')
    parse_token('var', 'keyword')
    parse_identifier()
    parse_type_spec()
    if check_current_token('='):
        parse_token('=', 'assign_op')
        parse_expression()
    parse_token(';', 'punct')
    pred_indt()


def parse_short_variable_decl():
    """
    Функція для розбору короткої декларації:
    ShortVariableDecl = Identifier ':=' Expression ';'
    """
    print(next_indt() + 'parse_short_variable_decl():')
    parse_identifier()
    parse_token(':=', 'short_assign_op')
    parse_expression()
    parse_token(';', 'punct')
    pred_indt()


def parse_const_decl():
    """
    Функція для розбору декларації константи:
    ConstDecl = 'const' Identifier TypeSpec '=' Expression ';'
    """
    print(next_indt() + 'parse_const_decl():')
    parse_token('const', 'keyword')
    parse_identifier()
    parse_type_spec()
    parse_token('=', 'assign_op')
    parse_expression()
    parse_token(';', 'punct')
    pred_indt()


def parse_type_spec():
    """
    Функція для розбору специфікації типу:
    TypeSpec = 'int' | 'float' | 'bool'
    """
    num_line, lexeme, tok = get_symbol()
    if lexeme in ['int', 'float', 'bool']:
        global num_row
        num_row += 1
    else:
        fail_parse('невідповідний тип', (num_line, lexeme, tok))


def parse_main_section():
    """
    Функція для розбору основної секції main:
    MainSection = 'func' 'main' '(' ')' '{' Statement { Statement | Declaration } '}'
    """
    print(next_indt() + 'parse_main_section():')

    parse_token('func', 'keyword')
    parse_token('main', 'keyword')
    parse_token('(', 'brackets_op')
    parse_token(')', 'brackets_op')
    parse_token('{', 'block_op')
    while parse_statement() or parse_declaration():
        pass
    parse_token('}', 'block_op')

    pred_indt()


def parse_statement():
    """
    Функція для розбору інструкції (Statement).
    Підтримує всі типи інструкцій згідно з граматикою.
    """
    num_line, lexeme, tok = get_symbol()
    if tok == 'id' and check_next_token('='):
        parse_assign()
        res = True
    elif lexeme == 'print':
        parse_output_stmt()
        res = True
    elif lexeme == 'scan':
        parse_input_stmt()
        res = True
    elif lexeme == 'for':
        parse_for_stmt()
        res = True
    elif lexeme == 'while':
        parse_while_stmt()
        res = True
    elif lexeme == 'if':
        parse_if_stmt()
        res = True
    elif lexeme == 'switch':
        parse_switch_stmt()
        res = True
    else:
        res = False
    return res


def parse_assign():
    """
    AssignmentStmt = Identifier '=' Expression ';'
    """
    parse_identifier()
    parse_token('=', 'assign_op')
    parse_expression()
    parse_token(';', 'punct')


def parse_output_stmt():
    """
    OutputStmt = 'print' '(' ExpressionList ')' ';'
    """
    parse_token('print', 'keyword')
    parse_token('(', 'brackets_op')
    parse_expression_list()
    parse_token(')', 'brackets_op')
    parse_token(';', 'punct')


def parse_input_stmt():
    """
    InputStmt = 'scan' '(' IdentifierList ')' ';'
    """
    parse_token('scan', 'keyword')
    parse_token('(', 'brackets_op')
    parse_identifier_list()
    parse_token(')', 'brackets_op')
    parse_token(';', 'punct')


def check_current_token(expected_lexeme):
    num_line, lexeme, tok = get_symbol()
    return lexeme == expected_lexeme


def check_next_token(expected_lexeme):
    num_line, lexeme, tok = get_next_symbol()
    return lexeme == expected_lexeme


def parse_for_stmt():
    """
    ForStmt = 'for' '(' Identifier ':=' ArExpr1 ';' ArExpr2 ';' [ AssignmentStmt ] ')' DoBlock
    """
    parse_token('for', 'keyword')
    parse_token('(', 'brackets_op')
    parse_identifier()
    parse_token(':=', 'assign_op')
    parse_expression()  # ArExpr1
    parse_token(';', 'punct')
    parse_expression()  # ArExpr2
    parse_token(';', 'punct')
    if check_current_token('id'):
        parse_assign()
    parse_token(')', 'brackets_op')
    parse_do_block()


def parse_while_stmt():
    """
    WhileStmt = 'while' Expression DoBlock
    """
    parse_token('while', 'keyword')
    parse_expression()
    parse_do_block()


def parse_if_stmt():
    """
    IfStmt = 'if' Expression DoBlock [ 'else' DoBlock ]
    """
    parse_token('if', 'keyword')
    parse_expression()
    parse_do_block()
    if check_current_token('else'):
        parse_token('else', 'keyword')
        parse_do_block()


def parse_switch_stmt():
    """
    SwitchStmt = 'switch' Expression '{' { CaseClause } [ DefaultClause ] '}'
    """
    parse_token('switch', 'keyword')
    parse_expression()
    parse_token('{', 'block_op')
    while check_current_token('case'):
        parse_case_clause()
    if check_current_token('default'):
        parse_default_clause()
    parse_token('}', 'block_op')


def parse_case_clause():
    """
    CaseClause = 'case' Constant ':' DoBlock
    """
    parse_token('case', 'keyword')
    parse_expression()
    parse_token(':', 'punct')
    parse_do_block()


def parse_default_clause():
    """
    DefaultClause = 'default' ':' DoBlock
    """
    parse_token('default', 'keyword')
    parse_token(':', 'punct')
    parse_do_block()


def parse_do_block():
    """
    DoBlock = Statement | Block
    """
    num_line, lexeme, tok = get_symbol()
    if lexeme == '{':
        parse_token('{', 'block_op')
        while parse_statement():
            pass
        parse_token('}', 'block_op')
    else:
        parse_statement()


def parse_expression_list():
    parse_expression()
    while check_current_token(','):
        parse_token(',', 'punct')
        parse_expression()


def parse_identifier_list():
    parse_identifier()
    while check_current_token(','):
        parse_token(',', 'punct')
        parse_identifier()


def parse_expression():
    indent = next_indt()
    print(indent + 'parse_expression():')

    parse_term()
    while True:
        num_line, lexeme, tok = get_symbol()
        if tok in 'add_op':
            print(indent + f"в рядку {num_line} - токен ({lexeme}, {tok})")
            global num_row
            num_row += 1
            parse_term()
        else:
            break

    pred_indt()


def parse_term():
    indent = next_indt()
    print(indent + 'parse_term():')

    parse_factor()
    while True:
        num_line, lexeme, tok = get_symbol()
        if tok in 'mult_op':
            print(indent + f"в рядку {num_line} - токен ({lexeme}, {tok})")
            global num_row
            num_row += 1
            parse_factor()
        else:
            break

    pred_indt()


def parse_factor():
    indent = next_indt()
    print(indent + 'parse_factor():')

    num_line, lexeme, token = get_symbol()
    global num_row
    if token in ('intnum', 'floatnum', 'id', 'boolval'):
        print(indent + f"в рядку {num_line} - токен ({lexeme}, {token})")
        num_row += 1
    elif lexeme == '(':
        print(indent + f"в рядку {num_line} - токен ({lexeme}, 'brackets_op')")
        num_row += 1
        parse_expression()
        parse_token(')', 'brackets_op')
    else:
        fail_parse('невідповідність у Expression.Factor', (num_line, lexeme, token))

    pred_indt()


def parse_token(expected_lexeme, expected_token):
    global num_row

    indent = next_indt()
    if num_row > len_table_of_symbols:
        fail_parse('неочікуваний кінець програми', (expected_lexeme, expected_token, num_row))

    num_line, lexeme, token = get_symbol()
    num_row += 1

    if (lexeme, token) == (expected_lexeme, expected_token):
        print(indent + 'parseToken: В рядку {0} токен {1}'.format(num_line, (expected_lexeme, expected_token)))
        res = True
    else:
        fail_parse('невідповідність токенів', (num_line, lexeme, token, expected_lexeme, expected_token))
        res = False

    pred_indt()
    return res


def parse_identifier():
    global num_row

    indent = next_indt()

    if num_row > len_table_of_symbols:
        fail_parse('неочікуваний кінець програми', ('<ідентифікатор>', 'id', num_row))

    num_line, lexeme, token = get_symbol()
    num_row += 1

    if token == 'id':
        print(indent + 'parseIdentifier: В рядку {0} ідентифікатор {1}'.format(num_line, lexeme))
    else:
        fail_parse('невідповідність токенів', (num_line, lexeme, token, '<ідентифікатор>', 'id'))

    pred_indt()
    return True


def get_symbol():
    if num_row > len_table_of_symbols:
        fail_parse('get_symbol(): неочікуваний кінець програми', num_row)
    num_line, lexeme, token, _ = table_of_symbols[num_row]
    return num_line, lexeme, token


def get_next_symbol():
    if num_row + 1 > len_table_of_symbols:
        fail_parse('get_next_symbol(): неочікуваний кінець програми', num_row + 1)
    num_line, lexeme, token, _ = table_of_symbols[num_row + 1]
    return num_line, lexeme, token


def fail_parse(message, details):
    print(f'Parser ERROR: {message} - {details}')
    exit(1)


stepIndt = 2
indt = 0


def next_indt():
    global indt
    indt += stepIndt
    return ' ' * indt


def pred_indt():
    global indt
    indt -= stepIndt
    return ' ' * indt


# Запуск парсера
if f_success == ('Lexer', True):
    print(('len_table_of_symbols', len_table_of_symbols))
    run_parser()
