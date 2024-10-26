from lexer_minigopher import lex
from lexer_minigopher import table_of_symbols
import contextlib

f_success = lex()

print('-' * 30)
print('table_of_symbols:{0}'.format(table_of_symbols))
print('-' * 30)

num_row = 1  # Номер поточної лексеми
len_table_of_symbols = len(table_of_symbols)  # Довжина таблиці лексем


@contextlib.contextmanager
def indent_manager():
    global current_indent
    current_indent += indent_step
    try:
        yield
    finally:
        current_indent -= indent_step


indent_step = 2
current_indent = 0


def get_indent():
    return ' ' * current_indent


def run_parser():
    """
    Функція для розбору програми за правилом Program = { Declaration } MainSection.
    :return: True якщо розбір успішний, інакше викликає SystemExit
    """
    try:
        with indent_manager():
            parse_declaration_list()
            parse_main_section()
        print(get_indent() + 'Parser: Синтаксичний аналіз завершився успішно')
        return True
    except SystemExit as e:
        print(get_indent() + f'Parser: Аварійне завершення програми з кодом {e}')
        return False


def parse_declaration_list():
    """
    Функція для розбору списку декларацій {Declaration}
    """
    print(get_indent() + 'parse_declaration_list():')
    with indent_manager():
        while parse_declaration():
            pass


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
    print(get_indent() + 'parse_variable_decl():')
    with indent_manager():
        parse_token('var', 'keyword')
        parse_identifier()
        parse_type_spec()
        if check_current_token('='):
            parse_token('=', 'assign_op')
            parse_expression()
        parse_token(';', 'punct')


def parse_short_variable_decl():
    """
    Функція для розбору короткої декларації:
    ShortVariableDecl = Identifier ':=' Expression ';'
    """
    print(get_indent() + 'parse_short_variable_decl():')
    with indent_manager():
        parse_identifier()
        parse_token(':=', 'short_assign_op')
        parse_expression()
        parse_token(';', 'punct')


def parse_const_decl():
    """
    Функція для розбору декларації константи:
    ConstDecl = 'const' Identifier TypeSpec '=' Expression ';'
    """
    print(get_indent() + 'parse_const_decl():')
    with indent_manager():
        parse_token('const', 'keyword')
        parse_identifier()
        parse_type_spec()
        parse_token('=', 'assign_op')
        parse_expression()
        parse_token(';', 'punct')


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
    print(get_indent() + 'parse_main_section():')
    with indent_manager():
        parse_token('func', 'keyword')
        parse_token('main', 'keyword')
        parse_token('(', 'brackets_op')
        parse_token(')', 'brackets_op')
        parse_token('{', 'block_op')
        with indent_manager():
            while parse_statement() or parse_declaration():
                pass
        parse_token('}', 'block_op')


def parse_statement():
    """
    Функція для розбору інструкції (Statement).
    Підтримує всі типи інструкцій згідно з граматикою.
    """
    num_line, lexeme, tok = get_symbol()
    if tok == 'id' and check_next_token('='):
        parse_assign()
        return True
    elif lexeme == 'print':
        parse_output_stmt()
        return True
    elif lexeme == 'scan':
        parse_input_stmt()
        return True
    elif lexeme == 'for':
        parse_for_stmt()
        return True
    elif lexeme == 'while':
        parse_while_stmt()
        return True
    elif lexeme == 'if':
        parse_if_stmt()
        return True
    elif lexeme == 'switch':
        parse_switch_stmt()
        return True
    else:
        return False


def parse_assign():
    """
    Функція для розбору інструкції присвоювання:
    AssignmentStmt = Identifier '=' Expression ';'
    """
    print(get_indent() + 'parse_assign():')
    with indent_manager():
        parse_identifier()
        parse_token('=', 'assign_op')
        parse_expression()
        parse_token(';', 'punct')


def parse_output_stmt():
    """
    Функція для розбору інструкції виведення:
    OutputStmt = 'print' '(' ExpressionList ')' ';'
    """
    print(get_indent() + 'parse_output_stmt():')
    with indent_manager():
        parse_token('print', 'keyword')
        parse_token('(', 'brackets_op')
        parse_expression_list()
        parse_token(')', 'brackets_op')
        parse_token(';', 'punct')


def parse_input_stmt():
    """
    Функція для розбору інструкції введення:
    InputStmt = 'scan' '(' IdentifierList ')' ';'
    """
    print(get_indent() + 'parse_input_stmt():')
    with indent_manager():
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
    Функція для розбору інструкції ітеративного циклу:
    ForStmt = 'for' '(' Identifier ':=' ArithmExpression ';' Expression ';' Identifier '=' ArithmExpression ')' DoBlock.
    """
    print(get_indent() + 'parse_for_stmt():')
    with indent_manager():
        parse_token('for', 'keyword')
        parse_token('(', 'brackets_op')
        parse_identifier()
        parse_token(':=', 'short_assign_op')
        parse_arithm_expression()
        parse_token(';', 'punct')
        parse_expression()
        parse_token(';', 'punct')
        parse_identifier()
        parse_token('=', 'assign_op')
        parse_arithm_expression()
        parse_token(')', 'brackets_op')
        parse_do_block()


def parse_while_stmt():
    """
    Функція для розбору інструкції умовного циклу:
    WhileStmt = 'while' Expression DoBlock
    """
    print(get_indent() + 'parse_while_stmt():')
    with indent_manager():
        parse_token('while', 'keyword')
        parse_expression()
        parse_do_block()


def parse_if_stmt():
    """
    Функція для розбору інструкції розгалуження:
    IfStmt = 'if' Expression DoBlock [ 'else' DoBlock ]
    """
    print(get_indent() + 'parse_if_stmt():')
    with indent_manager():
        parse_token('if', 'keyword')
        parse_expression()
        parse_do_block()
        if check_current_token('else'):
            parse_token('else', 'keyword')
            parse_do_block()


def parse_switch_stmt():
    """
    Функція для розбору інструкції багатонаправленого розгалуження:
    SwitchStmt = 'switch' Expression '{' { CaseClause } [ DefaultClause ] '}'
    """
    print(get_indent() + 'parse_switch_stmt():')
    with indent_manager():
        parse_token('switch', 'keyword')
        parse_expression()
        parse_token('{', 'block_op')
        with indent_manager():
            while check_current_token('case'):
                parse_case_clause()
            if check_current_token('default'):
                parse_default_clause()
        parse_token('}', 'block_op')


def parse_case_clause():
    """
    CaseClause = 'case' Const ':' DoBlock
    """
    print(get_indent() + 'parse_case_clause():')
    with indent_manager():
        parse_token('case', 'keyword')
        parse_expression()
        parse_token(':', 'punct')
        parse_do_block()


def parse_default_clause():
    """
    DefaultClause = 'default' ':' DoBlock
    """
    print(get_indent() + 'parse_default_clause():')
    with indent_manager():
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
        with indent_manager():
            while parse_statement():
                pass
        parse_token('}', 'block_op')
    else:
        parse_statement()


def parse_expression_list():
    print(get_indent() + 'parse_expression_list():')
    with indent_manager():
        parse_expression()
        while check_current_token(','):
            parse_token(',', 'punct')
            parse_expression()


def parse_identifier_list():
    print(get_indent() + 'parse_identifier_list():')
    with indent_manager():
        parse_identifier()
        while check_current_token(','):
            parse_token(',', 'punct')
            parse_identifier()


def parse_expression():
    """
    Парсить головний нетермінал Expression = BoolExpression.
    """
    print(get_indent() + 'parse_expression():')
    with indent_manager():
        parse_bool_expression()


def parse_bool_expression():
    """
    Парсить BoolExpression = ArithmExpression [ RelOp ArithmExpression ]
                         | BoolConst
                         | '(' BoolExpression ')'.
    """
    print(get_indent() + 'parse_bool_expression():')
    with indent_manager():
        num_line, lexeme, tok = get_symbol()

        if tok == 'boolval':
            print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
            parse_token(lexeme, tok)
        elif lexeme == '(' and tok == 'brackets_op':
            print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
            parse_token('(', 'brackets_op')
            parse_bool_expression()
            parse_token(')', 'brackets_op')
        else:
            parse_arithm_expression()
            num_line, lexeme, tok = get_symbol()
            if tok == 'rel_op':
                # Парсинг реляційного оператора
                print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
                parse_token(lexeme, 'rel_op')
                parse_arithm_expression()


def parse_arithm_expression():
    """
    Парсить ArithmExpression = Term { AddOp Term } | [ Sign ] Term.
    """
    print(get_indent() + 'parse_arithm_expression():')
    with indent_manager():
        num_line, lexeme, tok = get_symbol()

        if tok == 'sign':
            # Парсинг унарного знака
            print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
            parse_token(lexeme, tok)

        parse_term()

        while True:
            num_line, lexeme, tok = get_symbol()
            if tok == 'add_op':
                print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
                parse_token(lexeme, tok)
                parse_term()
            else:
                break


def parse_term():
    """
    Парсить Term = Factor { MultOp Factor }.
    """
    print(get_indent() + 'parse_term():')
    with indent_manager():
        parse_factor()

        while True:
            num_line, lexeme, tok = get_symbol()
            if tok == 'mult_op':
                print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
                parse_token(lexeme, tok)
                parse_factor()
            else:
                break


def parse_factor():
    """
    Парсить Factor = Primary { PowerOp Primary }.
    """
    print(get_indent() + 'parse_factor():')
    with indent_manager():
        parse_primary()

        while True:
            num_line, lexeme, tok = get_symbol()
            if tok == 'power_op':
                print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
                parse_token(lexeme, tok)
                parse_primary()
            else:
                break


def parse_primary():
    """
    Парсить Primary = Identifier | NumConst | '(' ArithmExpression ')'.
    """
    print(get_indent() + 'parse_primary():')
    with indent_manager():
        num_line, lexeme, tok = get_symbol()

        if tok in ('id', 'intnum', 'floatnum'):
            print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
            parse_token(lexeme, tok)
        elif lexeme == '(' and tok == 'brackets_op':
            print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
            parse_token('(', 'brackets_op')
            parse_arithm_expression()
            parse_token(')', 'brackets_op')
        else:
            fail_parse('невідповідність у Primary', (num_line, lexeme, tok))


def parse_token(expected_lexeme, expected_token):
    global num_row

    if num_row > len_table_of_symbols:
        fail_parse('неочікуваний кінець програми', (expected_lexeme, expected_token, num_row))

    num_line, lexeme, token = get_symbol()
    num_row += 1

    if (lexeme, token) == (expected_lexeme, expected_token):
        print(f"{get_indent()}parse_token: В рядку {num_line} - токен {(expected_lexeme, expected_token)}")
        return True
    else:
        fail_parse('невідповідність токенів', (num_line, lexeme, token, expected_lexeme, expected_token))
        return False


def parse_identifier():
    global num_row

    if num_row > len_table_of_symbols:
        fail_parse('неочікуваний кінець програми', ('<ідентифікатор>', 'id', num_row))

    num_line, lexeme, token = get_symbol()
    num_row += 1

    if token == 'id':
        print(f"{get_indent()}parseIdentifier: В рядку {num_line} - ідентифікатор {lexeme}")
    else:
        fail_parse('невідповідність токенів', (num_line, lexeme, token, '<ідентифікатор>', 'id'))

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


if f_success == ('Lexer', True):
    print(('len_table_of_symbols', len_table_of_symbols))
    run_parser()
