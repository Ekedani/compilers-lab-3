import os


def map_type_to_cil(var_type):
    type_map = {
        "intnum": "int32",
        "floatnum": "float64",
        "bool": "bool"
    }
    return type_map.get(var_type, var_type)


class CILGenerator:
    def __init__(self):
        self.variables = []
        self.constants = set()
        self.labels = []
        self.cil_code = []
        self.label_count = 0

    def add_to_cil(self, instruction, *args):
        self.cil_code.append(f"    {instruction} {' '.join(map(str, args))}")

    def new_label(self):
        label = f"L{self.label_count}"
        self.label_count += 1
        return label

    def add_label(self, label):
        self.cil_code.append(f"{label}:")

    def add_conditional_jump(self, label):
        self.add_to_cil("brfalse", label)

    def add_unconditional_jump(self, label):
        self.add_to_cil("br", label)

    def set_variables(self, table_of_variables):
        for name, (id_num, var_type, status) in table_of_variables.items():
            cil_type = map_type_to_cil(var_type)
            self.variables.append((name, cil_type))

    def add_constant(self, value, const_type):
        cil_type = map_type_to_cil(const_type)
        self.constants.add((value, cil_type))

    def save_to_file(self, filename):
        base_filename = os.path.splitext(os.path.basename(filename))[0]
        with open(filename, 'w') as f:
            f.write(".assembly extern mscorlib\n{\n")
            f.write("  .publickeytoken = (B7 7A 5C 56 19 34 E0 89)\n")
            f.write("  .ver 4:0:0:0\n}\n\n")
            f.write(f".assembly {base_filename}\n{{\n")
            f.write("  .hash algorithm 0x00008004\n")
            f.write("  .ver 0:0:0:0\n}\n\n")
            f.write(f".module {base_filename}.exe\n\n")
            f.write(".class private auto ansi beforefieldinit Program\n")
            f.write("  extends [mscorlib]System.Object\n{\n")
            f.write("    .method private hidebysig static void Main(string[] args) cil managed\n")
            f.write("    {\n")
            f.write("        .entrypoint\n")

            f.write("        .locals init (\n")
            variables_str = ",\n".join([f"            {cil_type} {name}" for name, cil_type in self.variables])
            f.write(variables_str)
            f.write("\n        )\n\n")

            for value, cil_type in self.constants:
                f.write(f"    // {value} ({cil_type})\n")
            for line in self.cil_code:
                f.write(f"    {line}\n")
            f.write("        ret\n")
            f.write("    }\n")
            f.write("}\n")

    def perform_operation(self, op):
        op_map = {
            '+': 'add',
            '-': 'sub',
            '*': 'mul',
            '/': 'div',
            '%': 'rem',
            '**': 'call float64 [mscorlib]System.Math::Pow(float64, float64)',
        }
        cil_op = op_map.get(op)
        if op == '**':
            self.add_to_cil('conv.r8')
            self.add_to_cil('conv.r8')
            self.add_to_cil('swap')
        self.add_to_cil(cil_op)

    def perform_unary_operation(self, op):
        if op == '+':
            pass
        elif op == '-':
            self.add_to_cil('neg')

    def perform_relational_operation(self, op):
        op_map = {
            '==': 'ceq',
            '!=': ('ceq', 'ldc.i4.0', 'ceq'),
            '<': 'clt',
            '>': 'cgt',
            '<=': ('cgt', 'ldc.i4.0', 'ceq'),
            '>=': ('clt', 'ldc.i4.0', 'ceq'),
        }
        cil_ops = op_map.get(op)
        if isinstance(cil_ops, tuple):
            for instruction in cil_ops:
                self.add_to_cil(instruction)
        else:
            self.add_to_cil(cil_ops)

    def read_input(self, var_name, var_type):
        var_type = map_type_to_cil(var_type)
        self.add_to_cil('call', 'string [mscorlib]System.Console::ReadLine()')
        if var_type == 'int32':
            self.add_to_cil('call', 'int32 [mscorlib]System.Int32::Parse(string)')
        elif var_type == 'float64':
            self.add_to_cil('call', 'float64 [mscorlib]System.Double::Parse(string)')
        self.add_to_cil('stloc', var_name)

    def write_output(self, var_type):
        var_type = map_type_to_cil(var_type)
        if var_type == 'int32':
            self.add_to_cil('call', 'void [mscorlib]System.Console::WriteLine(int32)')
        elif var_type == 'float64':
            self.add_to_cil('call', 'void [mscorlib]System.Console::WriteLine(float64)')
        elif var_type == 'string':
            self.add_to_cil('call', 'void [mscorlib]System.Console::WriteLine(string)')
        elif var_type == 'bool':
            self.add_to_cil('call', 'void [mscorlib]System.Console::WriteLine(bool)')
        else:
            self.add_to_cil('callvirt', 'instance string [mscorlib]System.Object::ToString()')
            self.add_to_cil('call', 'void [mscorlib]System.Console::WriteLine(string)')

    def load_constant(self, value, var_type):
        cil_type = map_type_to_cil(var_type)
        if cil_type == 'int32':
            if -128 <= int(value) <= 127:
                self.add_to_cil(f'ldc.i4.s {value}')
            else:
                self.add_to_cil(f'ldc.i4 {value}')
        elif cil_type == 'float64':
            self.add_to_cil(f'ldc.r8 {value}')
        elif cil_type == 'bool':
            val = '1' if value.lower() == 'true' else '0'
            self.add_to_cil('ldc.i4', val)

    def load_variable(self, var_name):
        self.add_to_cil('ldloc', var_name)

    def store_variable(self, var_name):
        self.add_to_cil('stloc', var_name)

    def get_variable_type(self, var_name):
        for name, cil_type in self.variables:
            if name == var_name:
                return cil_type
        return None
