#Virtual Machine Translator
#Usage: python Main.py <filename.vm>
#Output: <filename.asm>
#Build a more advanced version of the VM translator that can handle more complex programs
#This version will be able to handle branching and function calls
#The VM translator will translate the VM code into Hack assembly code

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
    "push" : "C_PUSH",
    "pop" : "C_POP",
    # More VM commands to be added
    "label" : "C_LABEL",
    "goto" : "C_GOTO",
    "if-goto" : "C_IF",
    "function" : "C_FUNCTION",
    "return" : "C_RETURN",
    "call" : "C_CALL",
}

class Parser:
    #Open file and read lines
    def __init__(self, filename):
        self.lines = []
        with open(filename, "r") as f:
            for line in f:
                # Check if line is comment or empty
                line = line.strip()
                if not line.startswith("//") and line != "":
                    line = line.split("//")[0].strip()
                    self.lines.append(line)
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
        
        # check if line in instruction_type
        line = line.split(" ")[0]
        if line in instruction_type:
            return instruction_type[line]
        else:
            print(f"Failing here, line: {line}")
            return None
    
    # Returns the first argument of the current command
    def arg1(self) -> str: #Should not be called if the current command is C_RETURN
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
        # Impleting new commands for function and call
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
        # Current file being translated
        self.current_file = os.path.splitext(os.path.basename(filename))[0]
        # Function count for function calls
        self.function_count = 0
        #Store current function name
        self.current_function = None
        #Check if init has been written
        self.has_written_init = False
    
    # Informs tyranslation of new file
    def setFileName(self, filename : str):
        self.current_file = os.path.splitext(os.path.basename(filename))[0]

    #Write the Init code for the VM
    def writeInit(self):
        self.output.append("@256\nD=A\n@SP\nM=D")
        self.writeCall("Sys.init", 0)
        self.has_written_init = True

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
                # currentFile = currentFile.split("/")[-1].split("\\")[-1]
                print(f"       Current File: {self.current_file}")
                self.output.append(f"@{self.current_file}.{index}\nD=M\n{command_to_hack[command]}")
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
                print(f"       Current File: {self.current_file}")
                self.output.append(f"@SP\nAM=M-1\nD=M\n@{self.current_file}.{index}\nM=D")
        else:
            #Only runs if code is invalid
            print(f"       Invalid command: {command}")
    
    #Write the assembly code that is the translation of the given label command
    def writeLabel(self, label : str):
        self.output.append(f"({self.current_file}.{self.current_function}${label})")
    
    #Write the assembly code that is the translation of the given goto command
    def writeGoto(self, label : str):
        self.output.append(f"@{self.current_file}.{self.current_function}${label}\n0;JMP")
    
    #Write the assembly code that is the translation of the given if-goto command
    def writeIf(self, label : str):
        dollar_label = f"{self.current_file}.{self.current_function}${label}"
        self.output.append(f"@SP\nAM=M-1\nD=M\n@{dollar_label}\nD;JNE")


    #STUFF IF BREAKING HERE

    #More advanced commands for project 8
    #Write the assembly code that is the translation of the given function command
    def writeFunction(self, function_name : str, number_args : int):
        self.current_function = function_name
        self.output.append(f"({function_name})")
        # Put 0 in the local segment for the number of args
        for _ in range(number_args):
            self.WritePushPop("C_PUSH", "constant", 0, self.current_file)

    #Write the assembly code that is the translation of the given call command
    def writeCall(self, function_name : str, num_args : int):
        # Genrate and push the return address
        return_label = f"{self.current_file}.{function_name}$ret.{self.function_count}"
        self.function_count += 1
        self.output.append(f"@{return_label}\nD=A\n{command_to_hack['push']}")
        # Push LCL, ARG, THIS, THAT
        for segment in ["LCL", "ARG", "THIS", "THAT"]:
            self.output.append(f"@{segment}\nD=M\n{command_to_hack['push']}")
        # Reposition ARG = SP - 5 - num_args
        self.output.append(f"@SP\nD=M\n@{5 + num_args}\nD=D-A\n@ARG\nM=D")
        # Reposition LCL = SP
        self.output.append(f"@SP\nD=M\n@LCL\nM=D")
        # Goto function_name
        self.output.append(f"@{function_name}\n0;JMP")
        # inject the label for the return address
        self.output.append(f"({return_label})")

    #Write the assembly code that is the translation of the given return command
    def writeReturn(self):
        # Get the address at the frame's end (Stores in R13)
        self.output.append("@LCL\nD=M\n@R13\nM=D")
        # Get the return address (Stores in R14)
        self.output.append("@5\nA=D-A\nD=M\n@R14\nM=D")
        # puts the return value for the caller in the ARG[0]
        self.output.append("@SP\nAM=M-1\nD=M\n@ARG\nA=M\nM=D")
        # reposistion the SP of the caller
        self.output.append("@ARG\nD=M+1\n@SP\nM=D")
        # Restore [THAT, THIS, ARG, LCL] of the caller
        offset = 1
        for segment in ["THAT", "THIS", "ARG", "LCL"]:
            self.output.append(f"@R13\nD=M\n@{offset}\nA=D-A\nD=M\n@{segment}\nM=D")
            offset += 1
        # Goto the return address
        self.output.append("@R14\nA=M\n0;JMP")

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
    if len(vm_files) > 1:
        codeWriter.writeInit()
    #Go through each file and convert to assembly
    for vm_file in vm_files:
        codeWriter.setFileName(vm_file)
        parser = Parser(vm_file)
        print("Translating file: ", vm_file, "\n"*3)
        while parser.hasMoreLines():
            print(f"Parser Line {parser.current_line}: ", parser.lines[parser.current_line])
            command_type = parser.commandType()
            # Doesnt run if command_type is Return
            if command_type == "C_RETURN":
                print("       RETURN")
                codeWriter.writeReturn()
                parser.advance()
                continue
            
            command = parser.arg1()
            if command_type == "C_ARITHMETIC":
                print("       ARITHMETIC: ", command)
                codeWriter.writeArithmetic(command)
            elif command_type in ["C_PUSH", "C_POP"]:
                segment = parser.arg1()
                index = parser.arg2()
                print("       PUSHPOP: ", command_type, segment, index)
                codeWriter.WritePushPop(command_type, segment, index, currentFile=vm_file)
            # Working on new commands for writing for project 8
            elif command_type == "C_LABEL":
                label = parser.arg1()
                print("       LABEL: ", label)
                codeWriter.writeLabel(label)
            elif command_type == "C_GOTO":
                label = parser.arg1()
                print("       GOTO: ", label)
                codeWriter.writeGoto(label)
            elif command_type == "C_IF":
                label = parser.arg1()
                print("       IF-GOTO: ", label)
                codeWriter.writeIf(label)
            elif command_type == "C_FUNCTION":
                function_name = parser.arg1()
                number_args = parser.arg2()
                print("       FUNCTION: ", function_name, number_args)
                codeWriter.writeFunction(function_name, number_args)
            elif command_type == "C_CALL":
                function_name = parser.arg1()
                num_args = parser.arg2()
                print("       CALL: ", function_name, num_args)
                codeWriter.writeCall(function_name, num_args)
            else:
                print("       Invalid command type")
            parser.advance()
        print("\n"*3, "Done translating file: ", vm_file, "\n"*2, "-"*35, "\n"*2)
    codeWriter.close()


if __name__ == "__main__":
    main(sys.argv[1])


    