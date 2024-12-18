# Take a .asm file and convert it to hack binary
# Usage: python HackAssembler.py <file.asm>
# Output: <file.hack>

#HackAssembler will use the services of the Parser, Code, and SymbolTable modules to convert the assembly code to binary code.
import sys

# Define the symbols
SYMBOLS = {
    "R0": 0,
    "R1": 1,
    "R2": 2,
    "R3": 3,
    "R4": 4,
    "R5": 5,
    "R6": 6,
    "R7": 7,
    "R8": 8,
    "R9": 9,
    "R10": 10,
    "R11": 11,
    "R12": 12,
    "R13": 13,
    "R14": 14,
    "R15": 15,
    "SCREEN": 16384,
    "KBD": 24576,
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
}

# Define the comp codes
COMP = {
    "0": "0101010",
    "1": "0111111",
    "-1": "0111010",
    "D": "0001100",
    "A": "0110000",
    "!D": "0001101",
    "!A": "0110001",
    "-D": "0001111",
    "-A": "0110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "D+A": "0000010",
    "D-A": "0010011",
    "A-D": "0000111",
    "D&A": "0000000",
    "D|A": "0010101",
    "M": "1110000",
    "!M": "1110001",
    "-M": "1110011",
    "M+1": "1110111",
    "M-1": "1110010",
    "D+M": "1000010",
    "D-M": "1010011",
    "M-D": "1000111",
    "D&M": "1000000",
    "D|M": "1010101",
}

# Define the dest codes
DEST = {
    "null": "000",
    "M": "001",
    "D": "010",
    "MD": "011",
    "DM" : "011",
    "A": "100",
    "AM": "101",
    "AD": "110",
    "AMD": "111",
    "ADM": "111",
}

# Define the jump codes
JUMP = {
    "null": "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}

# Define the parser
class Parser:
    def __init__(self, filename):
        self.lines = []
        #Open the file and read the lines and add it to the list of lines
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                #This if statement tells us that if the line is not empty and does not start with //, then we will split the line at the // and take the first part of the line.
                if line and not line.startswith("//"):
                    line = line.split("//")[0].strip()
                    self.lines.append(line)
        self.current = 0
    #Check if there are more lines in the list of lines
    def hasMoreLines(self):
        return self.current < len(self.lines)
    #Advance our pointer to list of lines
    def advance(self):
        self.current += 1
    def instructionType(self):
        #Tells us if line is an A or C instruction
        if self.lines[self.current].startswith("@"):
            return "A_INSTRUCTION"
        elif "=" in self.lines[self.current] or ";" in self.lines[self.current]:
            return "C_INSTRUCTION"
        #Tells us if line is a label
        else:
            return "L_INSTRUCTION"
    def symbol(self):
        #Used only if current instruction is @symbol or (symbol)
        if self.instructionType() == "A_INSTRUCTION":
            return self.lines[self.current][1:]
        if self.instructionType() == "L_INSTRUCTION":
            return self.lines[self.current][1:-1]
        else:
            return None
    def dest(self):
        dests = self.lines[self.current]
        #Returns the instruction dest
        if "=" in dests:
            return dests.split("=")[0]
        else:
            return "null"

    def comp(self):
        #Returns the instruction comp
        comps = self.lines[self.current]
        if "=" in self.lines[self.current]:
            comps = comps.split("=")[1]
        if ";" in comps:
            comps = comps.split(";")[0]
        return comps
    def jump(self):
        #Returns the instruction jump
        jumps = self.lines[self.current]
        if ";" in jumps:
            return jumps.split(";")[1]
        else:
            return "null"

# Define the code (generates binary code)
class Code:
    #Deals only with C instructions
    def dest(self, line):
        print("dest: ", line)
        return DEST[line]
    def comp(self, line):
        print("comp: ", line)
        return COMP[line]
    def jump(self, line):
        print("jump: ", line)
        return JUMP[line]


# Define the routines for the symbol table
class SymbolTable:
    def __init__(self):
        self.symbols = SYMBOLS
    def addEntry(self, symbol, address):
        self.symbols[symbol] = address
    def contains(self, symbol):
        return symbol in self.symbols
    def getAddress(self, symbol):
        return self.symbols[symbol]


# Define the main assembler
def main(filename):
    parser = Parser(filename)
    symbolTable = SymbolTable()
    rom_address = 0

    # First pass:   
    while parser.hasMoreLines():
        if parser.instructionType() == "L_INSTRUCTION":
            #get address of the label
            symbolTable.addEntry(parser.symbol(), rom_address)
        else:
            rom_address += 1
        parser.advance()
    
    # Second pass:
    parser = Parser(filename)
    code = Code()
    output = []
    startAdress = 16
    while parser.hasMoreLines():
        if parser.instructionType() == "A_INSTRUCTION":
            symbol = parser.symbol()
            #if symbol is not in the symbol table
            if not symbolTable.contains(symbol):
                #add symbol to the symbol table
                symbolTable.addEntry(symbol, int(startAdress))
                startAdress += 1
                if symbol.isdigit():
                    address = int(symbol)
                    symbolTable.addEntry(symbol, int(symbol))
            address = symbolTable.getAddress(symbol)
            output.append(f"{address:016b}")
            print(f"Line {parser.current+1}: ", parser.lines[parser.current])
            print("Instruction Type: ", parser.instructionType())
            print("output: ", output[-1], "\n")
        elif parser.instructionType() == "C_INSTRUCTION":
            print(f"Line {parser.current+1}: ", parser.lines[parser.current])
            print("Instruction Type: ", parser.instructionType())
            dest = code.dest(parser.dest())
            comp = code.comp(parser.comp())
            jump = code.jump(parser.jump())
            output.append("111" + comp + dest + jump)
            print("output: ", output[-1], "\n")
        parser.advance()
    with open(filename.replace(".asm", ".hack"), "w") as f:
        f.write("\n".join(output))

# Run the assembler with a MakeFile and 
if __name__ == "__main__":
    main(sys.argv[1])
    print("Done!")

# End of HackAssembler.py

                        