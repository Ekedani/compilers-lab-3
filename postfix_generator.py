class PostfixGenerator:
    def __init__(self):
        self.postfix_code = []
        self.label_count = 0

    def add_to_postfix(self, element, token_type):
        self.postfix_code.append((element, token_type))

    def new_label(self):
        label = f"L{self.label_count}"
        self.label_count += 1
        return label

    def add_label(self, label):
        self.add_to_postfix(f'{label}:', 'label')

    def get_postfix_code(self):
        return self.postfix_code
