from lexer import lex
from lexer import table_of_symbols
from postfix_generator import PostfixGenerator
import contextlib

f_success = lex()

print('-' * 30)
print('table_of_symbols:{0}'.format(table_of_symbols))
print('-' * 30)

num_row = 1  # Номер поточної лексеми
len_table_of_symbols = len(table_of_symbols)  # Довжина таблиці лексем
indent_step = 2  # Крок відступу для виводу
current_indent = 0  # Розмір поточного відступу
postfix_generator = PostfixGenerator()  # Ініціалізація генератора постфіксного коду


@contextlib.contextmanager
def indent_manager():
    global current_indent
    current_indent += indent_step
    try:
        yield
    finally:
        current_indent -= indent_step


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

        ident = parse_identifier()
        proc_table_of_var(ident, parse_type_spec())

        if check_current_token('='):
            parse_token('=', 'assign_op')
            postfix_generator.add_to_postfix(ident, 'l-val')
            parse_expression()
            postfix_generator.add_to_postfix('=', 'assign')
            initialize_variable(ident)
        parse_token(';', 'punct')


def parse_short_variable_decl():
    """
    Функція для розбору короткої декларації:
    ShortVariableDecl = Identifier ':=' Expression ';'
    """
    print(get_indent() + 'parse_short_variable_decl():')
    with indent_manager():
        ident = parse_identifier()
        parse_token(':=', 'short_assign_op')
        postfix_generator.add_to_postfix(ident, 'l-val')
        expr_type = parse_expression()
        postfix_generator.add_to_postfix('=', 'assign')
        parse_token(';', 'punct')
        proc_table_of_var(ident, expr_type)
        initialize_variable(ident)


def parse_const_decl():
    """
    Функція для розбору декларації константи:
    ConstDecl = 'const' Identifier TypeSpec '=' Expression ';'
    """
    print(get_indent() + 'parse_const_decl():')
    with indent_manager():
        parse_token('const', 'keyword')
        ident = parse_identifier()
        proc_table_of_var(ident, parse_type_spec())
        parse_token('=', 'assign_op')
        postfix_generator.add_to_postfix(ident, 'l-val')
        parse_expression()
        initialize_variable(ident)
        postfix_generator.add_to_postfix('=', 'assign')
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
        return lexeme
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
    if num_row < len_table_of_symbols:
        extra_token = get_symbol()
        fail_parse('Неочікуваний токен після завершення main', extra_token)


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
        ident = parse_identifier()
        postfix_generator.add_to_postfix(ident, 'l-val')
        parse_token('=', 'assign_op')
        expr_type = parse_expression()
        postfix_generator.add_to_postfix('=', 'assign_op')
        parse_token(';', 'punct')

        initialize_variable(ident)
        var_type = get_type_var(ident)
        if var_type != expr_type and not (var_type == 'floatnum' and expr_type == 'intnum'):
            fail_parse('Несумісні типи при присвоєнні', (ident, var_type, expr_type))


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
        identifiers = parse_identifier_list()
        parse_token(')', 'brackets_op')
        parse_token(';', 'punct')

        for ident in identifiers:
            initialize_variable(ident)


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
        parse_short_variable_decl()
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
        identifiers = [parse_identifier()]
        while check_current_token(','):
            parse_token(',', 'punct')
            identifiers.append(parse_identifier())
        return identifiers


def parse_expression():
    """
    Парсить Expression = ArithmExpression [ RelOp ArithmExpression ].
    Повертає тип виразу.
    """
    print(get_indent() + 'parse_expression():')
    with indent_manager():
        left_type = parse_arithm_expression()
        num_line, lexeme, tok = get_symbol()
        if tok == 'rel_op':
            print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
            parse_token(lexeme, 'rel_op')
            right_type = parse_arithm_expression()
            postfix_generator.add_to_postfix(lexeme, 'rel_op')

            # Перевірка типів операндів реляційного оператора
            if left_type not in ('int', 'float', 'intnum', 'floatnum') or right_type not in (
            'int', 'float', 'intnum', 'floatnum'):
                fail_parse('Невірні типи операндів для реляційного оператора', (left_type, lexeme, right_type))

            # Результат реляційного виразу завжди 'bool'
            return 'bool'
        else:
            return left_type


def parse_arithm_expression():
    """
    Парсить ArithmExpression = Term { AddOp Term } | [ Sign ] Term.
    """
    print(get_indent() + 'parse_arithm_expression():')
    with indent_manager():
        expr_type = parse_term()

        while True:
            num_line, lexeme, tok = get_symbol()
            if tok == 'add_op':
                print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
                parse_token(lexeme, tok)
                term_type = parse_term()
                postfix_generator.add_to_postfix(lexeme, 'add_op')
                result_type = get_type_op(expr_type, lexeme, term_type)
                if result_type == 'type_error':
                    fail_parse('Несумісні типи в арифметичній операції', (expr_type, lexeme, term_type))
                expr_type = result_type
            else:
                break
        return expr_type


def parse_term():
    """
    Парсить Term = Factor { MultOp Factor }.
    Повертає тип виразу.
    """
    print(get_indent() + 'parse_term():')
    with indent_manager():
        term_type = parse_factor()

        while True:
            num_line, lexeme, tok = get_symbol()
            if tok == 'mult_op':
                print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
                parse_token(lexeme, tok)
                factor_type = parse_factor()
                postfix_generator.add_to_postfix(lexeme, 'mult_op')
                result_type = get_type_op(term_type, lexeme, factor_type)
                if result_type == 'type_error':
                    fail_parse('Несумісні типи в множенні/діленні', (term_type, lexeme, factor_type))
                term_type = result_type
            else:
                break
        return term_type


def parse_factor():
    """
    Парсить Factor = Primary { PowerOp Primary }.
    """
    print(get_indent() + 'parse_factor():')
    with indent_manager():
        factor_type = parse_primary()

        while True:
            num_line, lexeme, tok = get_symbol()
            if tok == 'power_op':
                print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
                parse_token(lexeme, tok)
                primary_type = parse_primary()
                postfix_generator.add_to_postfix(lexeme, 'power_op')
                result_type = get_type_op(factor_type, lexeme, primary_type)
                if result_type == 'type_error':
                    fail_parse('Несумісні типи в операції піднесення до степеня', (factor_type, lexeme, primary_type))
                factor_type = result_type
            else:
                break
        return factor_type


def parse_primary():
    """
    Parses Primary = Identifier | NumConst | BoolConst | '(' Expression ')'.
    """
    print(get_indent() + 'parse_primary():')
    with indent_manager():
        num_line, lexeme, tok = get_symbol()
        if tok in ('intnum', 'floatnum'):
            print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
            parse_token(lexeme, tok)
            postfix_generator.add_to_postfix(lexeme, tok)
            return tok
        elif tok == 'boolval':
            print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
            parse_token(lexeme, tok)
            postfix_generator.add_to_postfix(lexeme, tok)
            return 'bool'
        elif tok == 'id':
            print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
            parse_token(lexeme, tok)
            postfix_generator.add_to_postfix(lexeme, 'r-val')
            is_init_var(lexeme)
            return get_type_var(lexeme)
        elif lexeme == '(' and tok == 'brackets_op':
            print(f"{get_indent()}в рядку {num_line} - токен ({lexeme}, {tok})")
            parse_token('(', 'brackets_op')
            expr_type = parse_expression()
            parse_token(')', 'brackets_op')
            return expr_type
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

    return lexeme


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


# Семантичний аналіз, таблиця змінних
table_of_variables = {}


# Функція для обробки оголошення змінної
def proc_table_of_var(lexeme, var_type, value='undefined'):
    if lexeme in table_of_variables:
        fail_parse('повторне оголошення змінної', (lexeme, var_type))
    else:
        indx = len(table_of_variables) + 1
        table_of_variables[lexeme] = (indx, var_type, value)


# Функція для отримання типу змінної
def get_type_var(ident):
    try:
        return table_of_variables[ident][1]
    except KeyError:
        return 'undeclared_variable'


# Функція для перевірки ініціалізації змінної
def is_init_var(lexeme):
    if lexeme not in table_of_variables:
        fail_parse('використання неоголошеної змінної', (lexeme))
    else:
        if table_of_variables[lexeme][2] != 'assigned':
            fail_parse('використання змінної без значення', (lexeme))


# Функція для встановлення статусу ініціалізації змінної
def initialize_variable(ident):
    if ident in table_of_variables:
        indx, var_type, _ = table_of_variables[ident]
        if var_type in ['int', 'float']:
            var_type += 'num'
        table_of_variables[ident] = (indx, var_type, 'assigned')
    else:
        fail_parse("використання неоголошеної змінної", ident)


# Функція для обчислення типу операцій
def get_type_op(l_type, op, r_type):
    """
    Функція для визначення типу результату операції на основі типів операндів та оператора.
    """
    if op in ('+', '-', '*', '/', '%', '**'):
        if l_type not in ('intnum', 'floatnum') or r_type not in ('intnum', 'floatnum'):
            return 'type_error'
        if op == '/':
            if l_type == 'intnum' and r_type == 'intnum':
                return 'intnum'
            else:
                return 'floatnum'
        if l_type == 'floatnum' or r_type == 'floatnum':
            return 'floatnum'
        return 'intnum'
    elif op in ('<', '<=', '>', '>=', '==', '!='):
        if l_type not in ('intnum', 'floatnum', 'bool') or r_type not in ('intnum', 'floatnum', 'bool'):
            return 'type_error'
        return 'bool'
    else:
        return 'type_error'


# Запуск парсера
if f_success == ('Lexer', True):
    print(('len_table_of_symbols', len_table_of_symbols))
    run_parser()
    print(table_of_variables)
    print(postfix_generator.get_postfix_code())
