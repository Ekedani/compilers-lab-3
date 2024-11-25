import os


def map_type_to_cil(var_type):
    type_map = {
        "intnum": "int32",
        "floatnum": "float32",
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
                f.write(f"        // {value} ({cil_type})\n")
            for line in self.cil_code:
                f.write(f"            {line}\n")
            f.write("        ret\n")
            f.write("    }\n")
            f.write("}\n")
