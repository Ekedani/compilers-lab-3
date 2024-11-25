class PostfixGenerator:
    def __init__(self):
        self.variables = []
        self.labels = []
        self.postfix_code = []
        self.constants = set()
        self.label_count = 0

    def add_to_postfix(self, element, token_type):
        self.postfix_code.append((element, token_type))
        if token_type in ('intnum', 'floatnum', 'boolval'):
            self.constants.add((element, token_type))

    def new_label(self):
        label = f"m{self.label_count}"
        self.label_count += 1
        return label

    def add_label(self, label):
        self.labels.append((label, len(self.postfix_code)))
        self.add_to_postfix(f'{label}', 'label')

    def get_postfix_code(self):
        return self.postfix_code

    def add_conditional_jump(self, label):
        self.add_to_postfix(f'{label}', 'label')
        self.add_to_postfix(f'JF', 'jf')

    def add_unconditional_jump(self, label):
        self.add_to_postfix(f'{label}', 'label')
        self.add_to_postfix(f'JMP', 'jump')

    def set_variables(self, table_of_variables):
        for name, (id_num, var_type, status) in table_of_variables.items():
            self.variables.append((name, var_type))

    def save_to_file(self, filename):
        with open(filename, 'w') as f:
            f.write(".target: PSM\n")
            f.write(".version: 1.0\n\n")

            f.write(".vars(\n")
            for name, var_type in self.variables:
                f.write(f"   {name:<12} {var_type:<15}\n")
            f.write(")\n\n")

            f.write(".labels(\n")
            for name, value in self.labels:
                f.write(f"   {name:<12} {value:<15}\n")
            f.write(")\n\n")

            f.write(".constants(\n")
            for value, const_type in self.constants:
                f.write(f"   {value:<12} {const_type:<15}\n")
            f.write(")\n\n")

            f.write(".code(\n")
            for element in self.postfix_code:
                f.write(f"   {element[0]:<12} {element[1]: <15}\n")
            f.write(")\n")
