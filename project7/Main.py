#Virtual Machine Translator
#Usage: python Main.py <filename.vm>
#Output: <filename.asm>
#Build a basic VM translator that implements the arithmetic-logical and push/pop commands of the
# VM language. For the purpose of this project, we assume that the source VM code is error-free.
#Convert a VM command into Hack assembly code.

import sys
import os

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

# Define the symbols to convert from input to Hack Assembly
CONVERT_SYMBOLS = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT",
}

# Define the instruction type:
instruction_type = {
    "C_ARITHMETIC": ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"],
    "C_PUSH": ["push"],
    "C_POP": ["pop"],
}

class Parser:
    #Open file and read lines
    def __init__(self, filename):
        self.lines = []
        with open(filename, "r") as f:
            for line in f:
                # Remove comments and empty lines
                if not line.startswith("//"):
                    #Check if empty line
                    if line.strip() == "":
                        continue
                    line = line.split("//")[0].strip()
                    self.lines.append(line)
            # self.lines = f.readlines()
        self.current_line = 0

    # Checks if there are more lines to parse
    def hasMoreLines(self) -> bool:
        return self.current_line < len(self.lines)
    # Reads the next line
    def advance(self):
        self.current_line += 1
    
    #PARSING CURRENT INSTRUCTION
    def commandType(self) -> str:
        line : str = self.lines[self.current_line]
        if line in instruction_type["C_ARITHMETIC"]:
            return "C_ARITHMETIC"
        if line.startswith("push"):
            return "C_PUSH"
        elif line.startswith("pop"):
            return "C_POP"
        else:
            print(f"Failing here, line: {line}")
            return None
    
    # Returns the first argument of the current command
    def arg1(self) -> str:
        line = self.lines[self.current_line]
        command_type = self.commandType()
        if command_type == "C_ARITHMETIC":
            return line
        else:
            return line.split(" ")[1]
    
    # Returns the second argument of the current command
    def arg2(self) -> int:
        command_type = self.commandType()
        if command_type == "C_ARITHMETIC":
            return None
        return int(self.lines[self.current_line].split(" ")[2])

    
# Define Command to Hack Assembly
command_to_hack = {
    "add": "@SP\nAM=M-1\nD=M\nA=A-1\nM=D+M",
    "sub": "@SP\nAM=M-1\nD=M\nA=A-1\nM=M-D",
    "neg": "@SP\nA=M-1\nM=-M",

    "and": "@SP\nAM=M-1\nD=M\nA=A-1\nM=D&M",
    "or": "@SP\nAM=M-1\nD=M\nA=A-1\nM=D|M",
    "not": "@SP\nA=M-1\nM=!M",

    "push": "@SP\nA=M\nM=D\n@SP\nM=M+1",
    "pop": "@SP\nAM=M-1\nD=M\n@R13\nM=D\n@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D",
}

class CodeWriter:
    def __init__(self, filename : str):
        self.filename = filename
        # Output to be written to the file
        self.output = []
        # Label count for eq, gt, lt
        self.label_count = 0

    #Writes the assembly code that is the translation of the given arithmetic command
    def writeArithmetic(self, command : str):
        if command in ["eq", "gt", "lt"]:
            jump = {"eq" : "JEQ", "gt" : "JGT", "lt" : "JLT"}[command]
            self.output.append(f"@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n@TRUE{self.label_count}\nD;{jump}\n@SP\nA=M-1\nM=0\n@CONTINUE{self.label_count}\n0;JMP\n(TRUE{self.label_count})\n@SP\nA=M-1\nM=-1\n(CONTINUE{self.label_count})")
            self.label_count += 1
        else:
            self.output.append(command_to_hack[command])
    
    #Writes to the output file the assembly code that implements the given command, where command is either C_PUSH or C_POP
    #Getting currentFile helps with creating unique static variables
    def WritePushPop(self, command : str, segment : str, index : int, currentFile : str):
        if command == "C_PUSH":
            command = "push"
            if segment == "constant":
                self.output.append(f"@{index}\nD=A\n{command_to_hack[command]}")
            elif segment in ["local", "argument", "this", "that"]:
                segment = CONVERT_SYMBOLS[segment]
                self.output.append(f"@{SYMBOLS[segment]}\nD=M\n@{index}\nA=D+A\nD=M\n{command_to_hack[command]}")
            elif segment == "temp":
                self.output.append(f"@{5 + index}\nD=M\n{command_to_hack[command]}")
            elif segment == "pointer":
                self.output.append(f"@{3 + index}\nD=M\n{command_to_hack[command]}")
            #Create a unique label for each static variable
            elif segment == "static":
                currentFile = currentFile.split("/")[-1].split("\\")[-1]
                print(f"       Current File: {currentFile.split('.')[0]}")
                self.output.append(f"@{currentFile.split('.')[0]}.{index}\nD=M\n{command_to_hack[command]}")
        elif command == "C_POP":
            command = "pop"
            if segment in ["local", "argument", "this", "that"]:
                segment = CONVERT_SYMBOLS[segment]
                self.output.append(f"@{SYMBOLS[segment]}\nD=M\n@{index}\nD=D+A\n@R13\nM=D\n@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D")
            elif segment == "temp":
                self.output.append(f"@{5 + index}\nD=A\n@R13\nM=D\n@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D")
            elif segment == "pointer":
                self.output.append(f"@{3 + index}\nD=A\n@R13\nM=D\n@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D")
            #Create a unique label for each static variable
            elif segment == "static":
                currentFile = currentFile.split("/")[-1].split("\\")[-1]
                print(f"       Current File: {currentFile.split('.')[0]}")
                self.output.append(f"@SP\nAM=M-1\nD=M\n@{currentFile.split('.')[0]}.{index}\nM=D")
        else:
            #Only runs if code is invalid
            print(f"       Invalid command: {command}")
    
    #Write the output to the file and clear the output for the next file
    def close(self):
        with open(self.filename, "w") as f:
            f.write("\n".join(self.output))
        self.output = []

        
def main(path):
    #Checks if path is a directory or a file
    if os.path.isdir(path):
        #Get all the .vm files in the directory
        vm_files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".vm")]
        #Create a single .asm file for all the .vm files named after the directory
        asm_filename = os.path.join(path, os.path.basename(os.path.normpath(path)) + ".asm")
    else:
        vm_files = [path]
        asm_filename = path.replace(".vm", ".asm")
    print("VM Files: ", vm_files, "\n")
    #Make a single .asm file for all the .vm files (super weird requirement)
    codeWriter = CodeWriter(asm_filename)
    #Go through each file and convert to assembly
    for vm_file in vm_files:
        parser = Parser(vm_file)
        print("Translating file: ", vm_file, "\n"*3)
        while parser.hasMoreLines():
            print(f"Parser Line {parser.current_line}: ", parser.lines[parser.current_line])
            command_type = parser.commandType()
            command = parser.arg1()
            if command_type == "C_ARITHMETIC":
                print("       ARITHMETIC: ", command)
                codeWriter.writeArithmetic(command)
            elif command_type in ["C_PUSH", "C_POP"]:
                segment = parser.arg1()
                index = parser.arg2()
                print("       PUSHPOP: ", command_type, segment, index)
                codeWriter.WritePushPop(command_type, segment, index, currentFile=vm_file)
            parser.advance()
        print("\n"*3, "Done translating file: ", vm_file, "\n"*2, "-"*35, "\n"*2)
    codeWriter.close()


if __name__ == "__main__":
    main(sys.argv[1])


    