# Таблиця лексем мови
tokenTable = {'var': 'keyword', 'const': 'keyword', 'int': 'keyword', 'float': 'keyword', 'bool': 'keyword',
              'print': 'keyword', 'scan': 'keyword', 'true': 'boolval', 'false': 'boolval', 'func': 'keyword',
              'if': 'keyword', 'else': 'keyword', 'switch': 'keyword', 'case': 'keyword', 'for': 'keyword',
              'default': 'keyword', 'while': 'keyword', 'main': 'keyword', ':=': 'assign_op', '=': 'assign_op',
              '+': 'add_op', '-': 'add_op', '*': 'mult_op', '/': 'mult_op', '%': 'mult_op', '**': 'power_op',
              '(': 'brackets_op', ')': 'brackets_op', '{': 'block_op', '}': 'block_op', '<': 'rel_op', '<=': 'rel_op',
              '==': 'rel_op', '>': 'rel_op', '>=': 'rel_op', '!=': 'rel_op', ',': 'punct', ';': 'punct', ':': 'punct',
              ' ': 'ws', '\t': 'ws', '\n': 'eol', '\r': 'eol'}

# Решту токенів визначаємо не за лексемою, а за заключним станом
tokStateTable = {2: 'id', 6: 'floatnum', 7: 'intnum', 9: 'short_assign_op', 10: 'punct'}

# Алфавіт Σ
alphabet = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/=:!<>(){},.;%{} \t\n\r')

# Класи символів
Letter = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
Digit = set('0123456789')
Dot = {'.'}
Colon = {':'}
Equal = {'='}
Operator = set('+-*/%();{},')
Whitespace = {' ', '\t'}
EndOfLine = {'\n', '\r'}
Other = alphabet - (Letter | Digit | Dot | Colon | Equal | Operator | Whitespace | EndOfLine)

# δ - state-transition_function
stf = {
    (0, 'ws'): 0,
    (0, 'eol'): 0,
    (0, 'Other'): 101,
    (0, 'Letter'): 1,
    (1, 'Letter'): 1,
    (1, 'Digit'): 1,
    (1, 'Other'): 2,
    (0, 'Digit'): 3,
    (3, 'Digit'): 3,
    (3, 'Dot'): 4,
    (4, 'Digit'): 5,
    (5, 'Digit'): 5,
    (5, 'Other'): 6,
    (3, 'Other'): 7,
    (0, 'Colon'): 8,
    (8, 'Equal'): 9,
    (8, 'Other'): 10,
    (0, 'Operator'): 11,
    (0, 'Equal'): 12,
    (12, 'Other'): 13,
    (12, 'Equal'): 14,
    (0, '*'): 15,
    (15, 'Other'): 16,
    (15, '*'): 17,
    (0, '<'): 18,
    (18, 'Other'): 19,
    (18, 'Equal'): 20,
    (0, '>'): 21,
    (21, 'Other'): 22,
    (21, 'Equal'): 23,
    (0, '!'): 24,
    (24, 'Equal'): 25,
    (28, 'Other'): 102
}

initState = 0  # q0 - стартовий стан
F = {2, 6, 7, 9, 10, 11, 13, 14, 16, 17, 19, 20, 22, 23, 25, 30, 101, 102}

Ferror = {101, 102}  # обробка помилок

table_of_id = {}  # Таблиця ідентифікаторів
table_of_const = {}  # Таблиць констант
table_of_symbols = {}  # Таблиця символів програми (таблиця розбору)

state = initState  # поточний стан

f = open('test.mgo', 'r')
sourceCode = f.read()
f.close()

# FSuccess - ознака успішності/неуспішності розбору
FSuccess = ('Lexer', False)

lenCode = len(sourceCode) - 1  # номер останнього символа у файлі з кодом програми
numLine = 1  # лексичний аналіз починаємо з першого рядка
numChar = -1  # з першого символа (в Python'і нумерація - з 0)
char = ''  # ще не брали жодного символа
lexeme = ''  # ще не починали розпізнавати лексеми


def lex():
    global state, numLine, char, lexeme, numChar, FSuccess
    try:
        while numChar < lenCode:
            char = nextChar()  # прочитати наступний символ
            classCh = classOfChar(char)  # до якого класу належить
            state = nextState(state, classCh)  # обчислити наступний стан
            if classCh == 'eol':
                numLine += 1
            if (is_final(state)):  # якщо стан заключний
                if lexeme == '':
                    lexeme += char
                processing()  # виконати семантичні процедури
            elif state == initState:
                lexeme = ''  # якщо стан НЕ заключний, а стартовий - нова лексема
            else:
                lexeme += char  # якщо стан НЕ закл. і не стартовий - додати символ до лексеми
        print('Lexer: Лексичний аналіз завершено успішно')
        FSuccess = ('Lexer', True)
        return FSuccess
    except SystemExit as e:
        # Повідомити про факт виявлення помилки
        print('Lexer: Аварійне завершення програми з кодом {0}'.format(e))


def processing():
    global state, lexeme, char, numChar, table_of_symbols

    if state == 2:  # keyword, id
        # Визначаємо, чи це keyword, id чи boolval
        if lexeme in ['true', 'false']:
            token = 'boolval'
        else:
            token = getToken(state, lexeme)
        if token == 'id':  # Якщо це id
            index = indexIdConst(state, lexeme)
            print('{:<10s} {:<10s} {:<5d}'.format(lexeme, token, index))
            table_of_symbols[len(table_of_symbols) + 1] = (numLine, lexeme, token, index)
        else:
            print('{:<10s} {:<10s}'.format(lexeme, token))
            table_of_symbols[len(table_of_symbols) + 1] = (numLine, lexeme, token, '')
        lexeme = ''
        numChar = putCharBack(numChar)
        state = initState

    elif state == 6:  # floatnum
        index = indexIdConst(state, lexeme)
        print('{:<10s} {:<10s} {:<5d}'.format(lexeme, 'floatnum', index))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, lexeme, 'floatnum', index)
        lexeme = ''
        numChar = putCharBack(numChar)
        state = initState

    elif state == 7:  # intnum
        index = indexIdConst(state, lexeme)
        if isinstance(index, tuple):
            index = index[1]
        print('{:<10s} {:<10s} {:<5d}'.format(lexeme, 'intnum', index))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, lexeme, 'intnum', index)
        lexeme = ''
        numChar = putCharBack(numChar)
        state = initState

    elif state == 9:  # short_assign_op (:=)
        print('{:<10s} {:<10s}'.format(':=', 'short_assign_op'))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, ':=', 'short_assign_op', '')
        lexeme = ''
        state = initState

    elif state == 10:  # punct (:)
        print('{:<10s} {:<10s}'.format(lexeme, 'punct'))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, lexeme, 'punct', '')
        lexeme = ''
        state = initState

    elif state == 11:  # add_op, mult_op, brackets_op, block_op, punct (, ;)
        # print(lexeme)

        token = getToken(state, lexeme)
        print('{:<10s} {:<10s}'.format(lexeme, token))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, lexeme, token, '')
        lexeme = ''
        state = initState

    elif state == 13:  # assign_op (=)
        print('{:<10s} {:<10s}'.format(lexeme, 'assign_op'))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, lexeme, 'assign_op', '')
        lexeme = ''
        state = initState

    elif state == 14:  # rel_op (==)
        print('{:<10s} {:<10s}'.format('==', 'rel_op'))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, '==', 'rel_op', '')
        lexeme = ''
        state = initState

    elif state == 16:  # mult_op (*)
        print('{:<10s} {:<10s}'.format(lexeme, 'mult_op'))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, lexeme, 'mult_op', '')
        lexeme = ''
        state = initState

    elif state == 17:  # power_op (**)
        print('{:<10s} {:<10s}'.format('**', 'power_op'))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, '**', 'power_op', '')
        lexeme = ''
        state = initState

    elif state == 19:  # rel_op (<)
        print('{:<10s} {:<10s}'.format(lexeme, 'rel_op'))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, lexeme, 'rel_op', '')
        lexeme = ''
        state = initState

    elif state == 20:  # rel_op (<=)
        print('{:<10s} {:<10s}'.format('<=', 'rel_op'))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, '<=', 'rel_op', '')
        lexeme = ''
        state = initState

    elif state == 22:  # rel_op (>)
        print('{:<10s} {:<10s}'.format(lexeme, 'rel_op'))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, lexeme, 'rel_op', '')
        lexeme = ''
        state = initState

    elif state == 23:  # rel_op (>=)
        print('{:<10s} {:<10s}'.format('>=', 'rel_op'))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, '>=', 'rel_op', '')
        lexeme = ''
        state = initState

    elif state == 25:  # rel_op (!=)
        print('{:<10s} {:<10s}'.format('!=', 'rel_op'))
        table_of_symbols[len(table_of_symbols) + 1] = (numLine, '!=', 'rel_op', '')
        lexeme = ''
        state = initState
    elif state in Ferror:  # (101,102):  # ERROR
        fail()


def fail():
    global state, numLine, char
    print(numLine)
    if state == 101:
        print('Помилка: у рядку ', numLine, ' неочікуваний символ ' + char)
        exit(101)
    if state == 102:
        print('Помилка: у рядку ', numLine, ' неочікуваний символ після!')
        exit(102)


def is_final(state):
    if (state in F):
        return True
    else:
        return False


def nextState(state, classCh):
    try:
        return stf[(state, classCh)]
    except KeyError:
        return stf[(state, 'Other')]


def nextChar():
    global numChar
    numChar += 1
    return sourceCode[numChar]


def putCharBack(numChar):
    return numChar - 1


def classOfChar(c):
    if c in Letter:
        return 'Letter'
    elif c in Digit:
        return 'Digit'
    elif c in Dot:
        return 'Dot'
    elif c in Colon:
        return 'Colon'
    elif c in Equal:
        return 'Equal'
    elif c in {'<', '>', '!', '*'}:
        return c
    elif c in Operator:
        return 'Operator'
    elif c in Whitespace:
        return 'ws'
    elif c in EndOfLine:
        return 'eol'
    else:
        return 'Other'


def getToken(state, lexeme):
    try:
        return tokenTable[lexeme]
    except KeyError:
        return tokStateTable[state]


def indexIdConst(state, lexeme):
    indx = 0
    if state == 2:
        indx = table_of_id.get(lexeme)
        if indx is None:
            indx = len(table_of_id) + 1
            table_of_id[lexeme] = indx
    if state in (6, 7):
        indx = table_of_const.get(lexeme)
        if indx is None:
            indx = len(table_of_const) + 1
            table_of_const[lexeme] = (tokStateTable[state], indx)
    return indx
