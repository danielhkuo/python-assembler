import sys

class Parser:
    def __init__(self, input_file):
        with open(input_file, 'r') as f:
            self.lines = self.preprocess_lines(f)
        self.current_line = -1
        self.current_instruction = None

    def preprocess_lines(self, file):
        preprocessed = []
        for line in file:
            # Remove leading/trailing whitespace
            line = line.strip()
            # Remove inline comments
            line = line.split('//')[0].strip()
            # Skip empty lines and full-line comments
            if line and not line.startswith('//'):
                preprocessed.append(line)
        return preprocessed

    def has_more_lines(self):
        return self.current_line < len(self.lines) - 1

    def advance(self):
        self.current_line += 1
        self.current_instruction = self.lines[self.current_line]

    def instruction_type(self):
        if self.current_instruction.startswith('@'):
            return 'A_INSTRUCTION'
        elif self.current_instruction.startswith('('):
            return 'L_INSTRUCTION'
        else:
            return 'C_INSTRUCTION'

    def symbol(self):
        if self.instruction_type() == 'A_INSTRUCTION':
            return self.current_instruction[1:]
        elif self.instruction_type() == 'L_INSTRUCTION':
            return self.current_instruction[1:-1]
        else:
            raise ValueError("Called symbol() on a C-instruction")

    def dest(self):
        if '=' in self.current_instruction:
            return self.current_instruction.split('=')[0]
        return ''

    def comp(self):
        instruction = self.current_instruction.split('=')[-1]
        return instruction.split(';')[0]

    def jump(self):
        if ';' in self.current_instruction:
            return self.current_instruction.split(';')[-1]
        return ''

class Code:
    def __init__(self):
        self.dest_table = {
            '': '000', 'M': '001', 'D': '010', 'MD': '011',
            'A': '100', 'AM': '101', 'AD': '110', 'AMD': '111'
        }
        self.jump_table = {
            '': '000', 'JGT': '001', 'JEQ': '010', 'JGE': '011',
            'JLT': '100', 'JNE': '101', 'JLE': '110', 'JMP': '111'
        }
        self.comp_table = {
            '0': '0101010', '1': '0111111', '-1': '0111010', 'D': '0001100',
            'A': '0110000', '!D': '0001101', '!A': '0110001', '-D': '0001111',
            '-A': '0110011', 'D+1': '0011111', 'A+1': '0110111', 'D-1': '0001110',
            'A-1': '0110010', 'D+A': '0000010', 'D-A': '0010011', 'A-D': '0000111',
            'D&A': '0000000', 'D|A': '0010101',
            'M': '1110000', '!M': '1110001', '-M': '1110011', 'M+1': '1110111',
            'M-1': '1110010', 'D+M': '1000010', 'D-M': '1010011', 'M-D': '1000111',
            'D&M': '1000000', 'D|M': '1010101'
        }

    def dest(self, mnemonic):
        return self.dest_table.get(mnemonic, '000')

    def comp(self, mnemonic):
        return self.comp_table.get(mnemonic, '0000000')

    def jump(self, mnemonic):
        return self.jump_table.get(mnemonic, '000')

class SymbolTable:
    def __init__(self):
        self.table = {
            'SP': 0, 'LCL': 1, 'ARG': 2, 'THIS': 3, 'THAT': 4,
            'R0': 0, 'R1': 1, 'R2': 2, 'R3': 3, 'R4': 4, 'R5': 5, 'R6': 6, 'R7': 7,
            'R8': 8, 'R9': 9, 'R10': 10, 'R11': 11, 'R12': 12, 'R13': 13, 'R14': 14, 'R15': 15,
            'SCREEN': 16384, 'KBD': 24576
        }
        self.next_variable_address = 16

    def add_entry(self, symbol, address):
        self.table[symbol] = address

    def contains(self, symbol):
        return symbol in self.table

    def get_address(self, symbol):
        return self.table.get(symbol)

    def add_variable(self, symbol):
        if not self.contains(symbol):
            self.table[symbol] = self.next_variable_address
            self.next_variable_address += 1
        return self.table[symbol]


def assemble(input_file, output_file):
    # First pass: build symbol table
    symbol_table = SymbolTable()
    parser = Parser(input_file)
    rom_address = 0

    while parser.has_more_lines():
        parser.advance()
        if parser.instruction_type() == 'L_INSTRUCTION':
            symbol_table.add_entry(parser.symbol(), rom_address)
        else:
            rom_address += 1

    # Second pass: generate code
    parser = Parser(input_file)
    code = Code()
    with open(output_file, 'w') as f:
        while parser.has_more_lines():
            parser.advance()
            if parser.instruction_type() == 'A_INSTRUCTION':
                symbol = parser.symbol()
                if symbol.isdigit():
                    value = int(symbol)
                elif symbol_table.contains(symbol):
                    value = symbol_table.get_address(symbol)
                else:
                    value = symbol_table.add_variable(symbol)
                binary = format(value, '016b')
                f.write(binary + '\n')
            elif parser.instruction_type() == 'C_INSTRUCTION':
                dest = code.dest(parser.dest())
                comp = code.comp(parser.comp())
                jump = code.jump(parser.jump())
                binary = '111' + comp + dest + jump
                f.write(binary + '\n')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python assembler.py <input.asm>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = input_file.replace('.asm', '.hack')
    assemble(input_file, output_file)
    print(f"Assembly complete. Output written to {output_file}")
