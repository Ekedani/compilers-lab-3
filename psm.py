class PSMException(Exception):
    def __init__(self, msg):
        self.msg = msg


def i2f(int_val):
    if isinstance(int_val, int):
        return float(int_val)
    else:
        return int_val


def f2i(float_val):
    if isinstance(float_val, float):
        return int(float_val)
    else:
        return float_val


def get_value(lex, tok):
    if tok == 'floatnum':
        return float(lex)
    elif tok == 'intnum':
        return int(lex)
    elif tok == 'boolval':
        return lex.lower() == 'true'
    else:
        return lex


class PostfixStackMachine:
    def __init__(self):
        self.table_of_id = {}
        self.table_of_label = {}
        self.table_of_const = {}
        self.postfix_code = []
        self.debug_map = {}
        self.line_number = 0
        self.filename = ""
        self.file = None
        self.current_line = ""
        self.section_headers = {
            "VarDecl": ".vars(",
            "LblDecl": ".labels(",
            "ConstDecl": ".constants(",
            "Code": ".code("
        }
        self.error_messages = {
            1: "Unexpected header",
            2: "An empty line was expected here",
            3: "A section header was expected here",
            4: "Two elements were expected in the line",
            7: "Variable type differs from value type",
            8: "Uninitialized variable",
            9: "Operand types differ",
            10: "Division by zero"
        }
        self.stack = []
        self.instruction_pointer = 0
        self.max_instructions = 0

    def load_postfix_file(self, filename):
        try:
            self.filename = f"{filename}.postfix"
            with open(self.filename, 'r') as self.file:
                self.parse_postfix_program()
        except PSMException as e:
            print(f"Error at line {self.line_number}: {self.error_messages.get(e.msg, 'Unknown error')}")
        except FileNotFoundError:
            print(f"File {self.filename} not found.")

    def parse_postfix_program(self):
        self._parse_header(".target: PSM")
        self._parse_header(".version: 1.0")
        self._parse_section("VarDecl")
        self._parse_section("LblDecl")
        # self._parse_section("ConstDecl")
        self._parse_section("Code")

    def _parse_header(self, expected_header):
        line = self.file.readline().strip()
        self.line_number += 1
        if line != expected_header:
            raise PSMException(1)

    def _parse_section(self, section):
        expected_header = self.section_headers[section]
        while True:
            line = self.file.readline().split("#")[0].strip()
            self.line_number += 1
            if line == "":
                continue
            elif line == expected_header:
                break
            else:
                raise PSMException(3)
        while True:
            line = self.file.readline().split("#")[0].strip()
            self.line_number += 1
            if line == "":
                continue
            elif line == ")":
                break
            else:
                self.current_line = line
                self._process_section(section)

    def _process_section(self, section):
        tokens = self.current_line.split()
        if len(tokens) != 2:
            raise PSMException(4)
        key, value = tokens
        if section == "VarDecl":
            index = len(self.table_of_id) + 1
            if value == 'bool' :
                value = 'boolval'
            self.table_of_id[key] = (index, value, 'val_undef')
            print(self.table_of_id[key])
        elif section == "LblDecl":
            self.table_of_label[key] = int(value)
        elif section == "ConstDecl":
            index = len(self.table_of_const) + 1
            val = get_value(key, value)
            self.table_of_const[key] = (index, value, val)
        elif section == "Code":
            self.postfix_code.append((key, value))
            instruction_number = len(self.postfix_code) - 1
            self.debug_map[instruction_number] = self.line_number

    def execute_postfix(self):
        self.max_instructions = len(self.postfix_code)
        try:
            while self.instruction_pointer < self.max_instructions:
                lex, tok = self.postfix_code[self.instruction_pointer]
                if tok in ('intnum', 'floatnum', 'l-val', 'r-val', 'label', 'boolval'):
                    self.stack.append((lex, tok))
                    self.instruction_pointer += 1
                elif tok in ('jump', 'jf', 'colon'):
                    self._handle_jumps(tok)
                elif tok == 'out':
                    identifier, _ = self.stack.pop()
                    self.instruction_pointer += 1
                    value = self.table_of_id.get(identifier, ('', '', 'Undefined'))[2]
                    print(f'{identifier} = {value}')
                else:
                    self._execute_operation(lex, tok)
                    self.instruction_pointer += 1
        except PSMException as e:
            print(f'Runtime Error: {self.error_messages.get(e.msg, "Unknown error")}')
        except IndexError:
            print('Runtime Error: Stack underflow')

    def _handle_jumps(self, tok):
        if tok == 'jump':
            label, _ = self.stack.pop()
            self.instruction_pointer = self.table_of_label.get(label, self.instruction_pointer)
        elif tok == 'colon':
            self.stack.pop()
            self.instruction_pointer += 1
        elif tok == 'jf':
            label, _ = self.stack.pop()
            condition, _ = self.stack.pop()
            if condition.lower() == 'false':
                self.instruction_pointer = self.table_of_label.get(label, self.instruction_pointer)
            else:
                self.instruction_pointer += 1

    def _execute_operation(self, lex, tok):
        print(f'Executing operation: {lex} {tok}')
        right_lex, right_tok = self.stack.pop()
        left_lex, left_tok = self.stack.pop()

        print(f'Left operand: {left_lex}, Righ operand: {right_lex}')
        if (lex, tok) == ('=', 'assign_op'):
            var_type = self.table_of_id[left_lex][1]
            if var_type != right_tok:
                if not(var_type == 'floatnum' and right_tok == 'intnum'):
                    raise PSMException(7)
            self.table_of_id[left_lex] = (
                self.table_of_id[left_lex][0],
                right_tok,
                get_value(right_lex, right_tok)
            )
        else:
            self._process_arithmetic_or_boolean_op(
                (left_lex, left_tok),
                lex,
                (right_lex, right_tok)
            )

    def _process_arithmetic_or_boolean_op(self, left, operator, right):
        left_type, left_value = self._get_operand_value(*left)
        right_type, right_value = self._get_operand_value(*right)
        self._apply_operator(
            (left[0], left_type, left_value),
            operator,
            (right[0], right_type, right_value)
        )

    def _get_operand_value(self, lex, tok):
        if tok == 'r-val':
            _, var_type, value = self.table_of_id.get(lex, (None, None, 'val_undef'))
            if value == 'val_undef':
                raise PSMException(8)
            return var_type, value
        elif tok == 'l-val':
            return self.table_of_id[lex][1], self.table_of_id[lex][2]
        else:
            return tok, get_value(lex, tok)

    def _apply_operator(self, left, operator, right):
        _, left_type, left_value = left
        _, right_type, right_value = right
        if left_type != right_type:
            raise PSMException(9)
        result_type = left_type

        try:
            if operator == '+':
                result = left_value + right_value
            elif operator == '-':
                result = left_value - right_value
            elif operator == '*':
                result = left_value * right_value
            elif operator == '**':
                result = left_value ** right_value
            elif operator == '%':
                result = left_value % right_value
            elif operator == '/':
                if right_value == 0:
                    raise PSMException(10)
                if result_type == 'floatnum':
                    result = left_value / right_value
                else:
                    result = f2i(left_value / right_value)
            elif operator in ('<', '<=', '>', '>=', '==', '!='):
                result = str(eval(f'{left_value} {operator} {right_value}')).lower()
                result_type = 'boolval'
            else:
                raise PSMException(f'Unknown operator {operator}')
        except ZeroDivisionError:
            raise PSMException(10)

        self.stack.append((str(result), result_type))

    def display_tables(self):
        print("\nIdentifier Table:")
        for key, value in self.table_of_id.items():
            print(f'  {key}: {value}')

        print("\nLabel Table:")
        for key, value in self.table_of_label.items():
            print(f'  {key}: {value}')

        print("\nConstant Table:")
        for key, value in self.table_of_const.items():
            print(f'  {key}: {value}')

        print("\nPostfix Code:")
        for index, code in enumerate(self.postfix_code):
            print(f'  {index}: {code}')

        print("\nDebug Map (Instruction Number to Line Number):")
        for instr_num, line_num in self.debug_map.items():
            print(f'  Instruction {instr_num}: Line {line_num}')


if __name__ == '__main__':
    psm = PostfixStackMachine()
    psm.load_postfix_file("test")
    print('Executing postfix code:')
    psm.execute_postfix()
    psm.display_tables()
