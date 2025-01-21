import re
import sys
import os

class SymbolTable:
    def __init__(self):
        self.class_table = {}
        self.subroutine_table = {}
        self.class_index = {'static': 0, 'field': 0}
        self.subroutine_index = {'argument': 0, 'local': 0}

    def startSubroutine(self):
        self.subroutine_table = {}
        self.subroutine_index = {'argument': 0, 'local': 0}

    def define(self, name, type, kind):
        if kind in ['static', 'field']:
            self.class_table[name] = (type, kind, self.class_index[kind])
            self.class_index[kind] += 1
        else:  # argument or local
            self.subroutine_table[name] = (type, kind, self.subroutine_index[kind])
            self.subroutine_index[kind] += 1

    def varCount(self, kind):
        if kind in ['static', 'field']:
            return self.class_index[kind]
        else:
            return self.subroutine_index[kind]

    def kindOf(self, name):
        if name in self.subroutine_table:
            return self.subroutine_table[name][1]
        elif name in self.class_table:
            return self.class_table[name][1]
        else:
            return None

    def typeOf(self, name):
        if name in self.subroutine_table:
            return self.subroutine_table[name][0]
        elif name in self.class_table:
            return self.class_table[name][0]
        else:
            return None

    def indexOf(self, name):
        if name in self.subroutine_table:
            return self.subroutine_table[name][2]
        elif name in self.class_table:
            return self.class_table[name][2]
        else:
            return None

class JackTokenizer:
    # Constructor: opens the input .jack file /stream and gets ready to tokenize it
    def __init__(self, file):
        self.file = file
        self.lines = []
        with open(file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line.startswith("//") and line != "" and not line.startswith("/**") and not line.startswith("*/") and not line.startswith("*") and not line.startswith("/*"):
                    line = line.split("//")[0].strip()
                    self.lines.append(line)
        self.current_token = ""
        self.tokens = []
        self.current_line = 0
        self.tokenize()  # Tokenize the input file

    # Go through each line and add each token to the list
    def tokenize(self):
        for line in self.lines:
            tokens = re.findall(r'"[^"]*"|\w+[:?]?|[\d]+|[\W]', line)
            for token in tokens:
                if token.startswith('"') and token.endswith('"'):
                    self.tokens.append(token)
                elif token.strip():
                    self.tokens.append(token.strip())
        if len(self.tokens) > 0:
            self.current_token = self.tokens[0]
        else:
            self.current_token = None
    # Are there more tokens in the input

    def hasMoreTokens(self):
        if len(self.tokens) > 0:
            return True

    # Gets the next token from the input and makes it the current token.
    def advance(self):
        self.tokens = self.tokens[1:]
        if len(self.tokens) > 0:
            self.current_token = self.tokens[0]
        else:
            self.current_token = None
    # Returns the type of the current token as a constant

    def tokenType(self):
        if self.current_token is None:
            return None
        token = self.current_token
        if token in ["class", "constructor", "function", "method", "field", "static", "var", "int", "char", "boolean", "void", "true", "false", "null", "this", "let", "do", "if", "else", "while", "return"]:
            return "KEYWORD"
        elif token in ["{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*", "/", "&", "|", "<", ">", "=", "~"]:
            return "SYMBOL"
        elif token.isdigit():
            return "INT_CONST"
        # Test if token is string constant
        elif token.startswith('"') and token.endswith('"'):
            return "STRING_CONST"
        else:
            return "IDENTIFIER"

    # Returns the keyword which is the current token. Should be called only when tokenType() is KEYWORD
    def keyWord(self):
        return self.current_token

    def symbol(self):
        return self.current_token

    def identifier(self):
        return self.current_token

    def intVal(self):
        return int(self.current_token)

    def stringVal(self):
        # get rid of " at the beginning and end of the string"
        return self.current_token[1:-1]

class VMWriter:
    def __init__(self, output_file):
        self.output_file = output_file

    def writePush(self, segment, index):
        self.output_file.write(f"    push {segment} {index}\n")

    def writePop(self, segment, index):
        self.output_file.write(f"    pop {segment} {index}\n")

    def writeArithmetic(self, command):
        self.output_file.write(f"    {command}\n")

    def writeLabel(self, label):
        self.output_file.write(f"label {label}\n")

    def writeGoto(self, label):
        self.output_file.write(f"    goto {label}\n")

    def writeIf(self, label):
        self.output_file.write(f"    if-goto {label}\n")

    def writeCall(self, name, nArgs):
        self.output_file.write(f"    call {name} {nArgs}\n")

    def writeFunction(self, name, nLocals):
        self.output_file.write(f"function {name} {nLocals}\n")

    def writeReturn(self):
        self.output_file.write(f"    return\n")

    def close(self):
        self.output_file.close()

class ComplilationEngine:
    def __init__(self, tokenizer, output, path):
        # Input: tokenizer object
        self.tokenizer: JackTokenizer = tokenizer
        # File object to write the output to
        self.output = VMWriter(output)
        self.indent = 0
        self.last_token = ""
        self.symbol_table = SymbolTable()
        self.label_index = 0
        self.class_name = ""
        self.file_name = path
        # Start compiling the class (recursivley)
        self.compileClass()

    # Function to advance the tokenizer
    advance = lambda self: self.tokenizer.advance()

    def printSymbolTable(self):
        print("Class Table")
        print("Name\tType\tKind\tIndex")
        for key, value in self.symbol_table.class_table.items():
            print(f"{key}\t{value[0]}\t{value[1]}\t{value[2]}")
        print("Subroutine Table")
        print("Name\tType\tKind\tIndex")
        for key, value in self.symbol_table.subroutine_table.items():
            print(f"{key}\t{value[0]}\t{value[1]}\t{value[2]}")
    # Functions to write the different tokens
    def writeKeyword(self):
        self.last_token = self.tokenizer.keyWord()
        self.advance()

    def writeSymbol(self):
        self.last_token = self.tokenizer.symbol()
        self.advance()

    def writeIdentifier(self):
        self.last_token = self.tokenizer.identifier()
        self.advance()

    def writeIntVal(self):
        self.last_token = self.tokenizer.intVal()
        self.advance()

    def writeStringVal(self):
        self.last_token = self.tokenizer.stringVal()
        self.advance()

    def writeType(self):
        self.last_token = self.tokenizer.identifier()
        self.advance()

    # Compiles a complete class
    def compileClass(self):
        self.writeKeyword()  # class
        self.class_name = self.tokenizer.identifier()
        self.writeIdentifier()
        self.writeSymbol()
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "KEYWORD":
                if self.tokenizer.keyWord() in ["constructor", "function", "method"]:
                    self.compileSubroutine()
                elif self.tokenizer.keyWord() in ["field", "static"]:
                    self.compileClassVarDec()
            elif self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() == "}":
                    self.writeSymbol()
                    break

    def compileClassVarDec(self):
        kind = self.tokenizer.keyWord()
        self.writeKeyword()  # static or field
        # If keyword is not a type, then it's an identifier
        if self.tokenizer.tokenType() == "IDENTIFIER":
            type = self.tokenizer.identifier()
            self.writeIdentifier()
        elif self.tokenizer.tokenType() == "KEYWORD":
            type = self.tokenizer.keyWord()
            self.writeKeyword()
        else:
            type = self.tokenizer.identifier()
            self.writeType()

        name = self.tokenizer.identifier()
        self.symbol_table.define(name, type, kind)
        self.writeIdentifier()
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "SYMBOL":
                current_symbol = self.tokenizer.symbol()
                if current_symbol == ";":
                    self.writeSymbol()
                    break
                elif current_symbol == ",":
                    self.writeSymbol()
                    name = self.tokenizer.identifier()
                    self.symbol_table.define(name, type, kind)
                    self.writeIdentifier()
                else:
                    self.writeSymbol()
            elif self.tokenizer.tokenType() == "IDENTIFIER":
                self.writeIdentifier()

    def compileSubroutine(self):
        self.symbol_table.startSubroutine()
        subroutine_type = self.tokenizer.keyWord()
        self.writeKeyword()  # constructor, function, or method
        if subroutine_type == "method":
            self.symbol_table.define("this", self.class_name, "argument")
        # Check if keyword is a type
        if self.tokenizer.tokenType() == "KEYWORD":
            self.writeKeyword()  # void or type
        else:
            self.writeIdentifier()  # type
        subroutine_name = f"{self.class_name}.{self.tokenizer.identifier()}"
        self.writeIdentifier()  # subroutine name
        self.writeSymbol()  # (
        self.compileParameterList()
        self.writeSymbol()  # )

        self.compileSubroutineBody(subroutine_name, subroutine_type)

    # Compiles a (possibly empty) parameter list. Does not handle the enclosing paretnhesis tokens ( and )
    def compileParameterList(self):
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() == ")":
                    break
                else:  # Should be a comma
                    self.writeSymbol()
            else:
                type = self.tokenizer.keyWord() if self.tokenizer.tokenType() == "KEYWORD" else self.tokenizer.identifier()
                self.writeKeyword() if self.tokenizer.tokenType() == "KEYWORD" else self.writeIdentifier()  # type
                name = self.tokenizer.identifier()
                self.symbol_table.define(name, type, "argument")
                self.writeIdentifier()  # varName

    # Compiles a subroutine's body
    def compileSubroutineBody(self, subroutine_name, subroutine_type):
        self.writeSymbol()  # {
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "KEYWORD":
                if self.tokenizer.keyWord() == "var":
                    self.compileVarDec()
                else:
                    break

        nLocals = self.symbol_table.varCount("local")
        self.output.writeFunction(subroutine_name, nLocals)
        if subroutine_type == "constructor":
            self.output.writePush(
                "constant", self.symbol_table.varCount("field"))
            self.output.writeCall("Memory.alloc", 1)
            self.output.writePop("pointer", 0)  # this = Memory.alloc(nFields)
        elif subroutine_type == "method":
            self.output.writePush("argument", 0)
            self.output.writePop("pointer", 0)
        self.compileStatements()
        self.writeSymbol()  # }

    # Compiles a var declaration
    def compileVarDec(self):
        self.writeKeyword()  # var
        # If keyword is not a type, then it's an identifier
        if self.tokenizer.tokenType() == "KEYWORD":
            type = self.tokenizer.keyWord()
            self.writeKeyword()  # type
        else:
            type = self.tokenizer.identifier()
            self.writeIdentifier()  # type

        name = self.tokenizer.identifier()
        self.symbol_table.define(name, type, "local")
        self.writeIdentifier()  # varName
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() == ";":
                    self.writeSymbol()
                    break
                elif self.tokenizer.symbol() == ",":
                    self.writeSymbol()
                    name = self.tokenizer.identifier()
                    self.symbol_table.define(name, type, "local")
                    self.writeIdentifier()  # varName
                # Write a empty symbol because it's not a comma or semicolon
                else:
                    self.writeSymbol()
            elif self.tokenizer.tokenType() == "IDENTIFIER":
                self.writeIdentifier()

    # Compiles a sequence of statements. Does not handle the enclosing curly bracket tockens { and }
    def compileStatements(self):
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "KEYWORD":
                if self.tokenizer.keyWord() == "let":
                    self.compileLet()
                elif self.tokenizer.keyWord() == "if":
                    self.compileIf()
                elif self.tokenizer.keyWord() == "while":
                    self.compileWhile()
                elif self.tokenizer.keyWord() == "do":
                    self.compileDo()
                elif self.tokenizer.keyWord() == "return":
                    self.compileReturn()
                else:
                    break
            else:
                break

    # Compiles a let statement
    def compileLet(self):
        self.writeKeyword()
        var_name = self.tokenizer.identifier()
        self.writeIdentifier()
        is_array = False
        if self.tokenizer.tokenType() == "SYMBOL" and self.tokenizer.symbol() == "[":
            is_array = True
            self.writeSymbol()  # [
            self.compileExpression()
            self.writeSymbol()  # ]
            self.output.writePush(self.get_segment(var_name), self.symbol_table.indexOf(var_name))
            self.output.writeArithmetic("add")
        self.writeSymbol()  # =
        self.compileExpression()
        self.writeSymbol()  # ;
        if is_array:
            self.output.writePop("temp", 0)
            self.output.writePop("pointer", 1)
            self.output.writePush("temp", 0)
            self.output.writePop("that", 0)
        else:
            self.output.writePop(self.get_segment(var_name), self.symbol_table.indexOf(var_name))

    # Compiles an if statement, possibly with a trailing else clause
    def compileIf(self):
        self.writeKeyword()
        self.writeSymbol()  # (
        self.compileExpression()
        self.writeSymbol()  # )
        self.output.writeArithmetic("not")
        label1 = self.generate_label()
        self.output.writeIf(label1)  # if-goto L1
        self.writeSymbol()  # {
        self.compileStatements()
        self.writeSymbol()  # }
        label2 = self.generate_label()
        self.output.writeGoto(label2)  # goto L2
        self.output.writeLabel(label1)  # label L1
        if self.tokenizer.hasMoreTokens() and self.tokenizer.tokenType() == "KEYWORD" and self.tokenizer.keyWord() == "else":
            self.writeKeyword()
            self.writeSymbol()  # {
            self.compileStatements()
            self.writeSymbol()  # }
        self.output.writeLabel(label2)  # label L2

    # Compiles a while statement
    def compileWhile(self):
        self.writeKeyword()
        label1 = self.generate_label()
        self.output.writeLabel(label1)  # label L1
        self.writeSymbol()  # (
        self.compileExpression()
        self.writeSymbol()  # )
        self.output.writeArithmetic("not")
        label2 = self.generate_label()
        self.output.writeIf(label2)  # if-goto L2
        self.writeSymbol()  # {
        self.compileStatements()
        self.writeSymbol()  # }
        self.output.writeGoto(label1)  # goto L1
        self.output.writeLabel(label2)  # label L2

    # Compiles a do statement
    def compileDo(self):
        self.writeKeyword()
        name = self.tokenizer.identifier()
        self.writeIdentifier()
        nArgs = 0
        if self.tokenizer.tokenType() == "SYMBOL" and self.tokenizer.symbol() == ".":
            self.writeSymbol()  # .
            if self.symbol_table.kindOf(name):
                # method call
                self.output.writePush(
                    self.get_segment(name), self.symbol_table.indexOf(name))
                nArgs += 1
                name = f"{self.symbol_table.typeOf(name)}.{self.tokenizer.identifier()}"
            else:
                name = f"{name}.{self.tokenizer.identifier()}"
            self.writeIdentifier()
        else:
            # It is a method call on the current object
            self.output.writePush("pointer", 0)
            name = f"{self.class_name}.{name}"
            nArgs += 1

        self.writeSymbol()  # (
        nArgs += self.compileExpressionList()
        self.writeSymbol()  # )
        self.writeSymbol()  # ;
        self.output.writeCall(name, nArgs)
        self.output.writePop("temp", 0)

    # Compiles a return statement
    def compileReturn(self):
        self.writeKeyword()
        if self.tokenizer.tokenType() == "SYMBOL" and self.tokenizer.symbol() == ";":
            self.output.writePush("constant", 0)
        else:
            self.compileExpression()
        self.writeSymbol()
        self.output.writeReturn()

    # Compiles an expression
    def compileExpression(self):
        self.compileTerm()
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() in ["+", "-", "*", "/", "&", "|", "<", ">", "="]:
                    op = self.tokenizer.symbol()
                    self.writeSymbol()
                    self.compileTerm()
                    self.write_op(op)
                else:
                    break
            else:
                break

    # Compiles a term. If the current token is an identifier, the routine must resolve it into a variable, an array entry, or a subroutine call
    # A single lookeahead token, which may be one of [, (, or . suffices to distinguish between the possibilities.
    # Any other token is not part of this term and should not be advanced over

    def compileTerm(self):
        if self.tokenizer.tokenType() == "SYMBOL":
            if self.tokenizer.symbol() in ["-", "~"]:
                op = self.tokenizer.symbol()
                self.writeSymbol()
                self.compileTerm()
                self.write_unary_op(op)
            elif self.tokenizer.symbol() == "(":
                self.writeSymbol()  # (
                self.compileExpression()
                self.writeSymbol()  # )
            else:
                # This is like an extra symbol so just ignore it
                pass
        elif self.tokenizer.tokenType() == "IDENTIFIER":
            name = self.tokenizer.identifier()
            self.writeIdentifier()
            if self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() == "[":
                    self.writeSymbol()  # [
                    self.compileExpression()
                    self.writeSymbol()  # ]
                    self.output.writePush(
                        self.get_segment(name), self.symbol_table.indexOf(name))
                    self.output.writeArithmetic("add")
                    self.output.writePop("pointer", 1)
                    self.output.writePush("that", 0)
                elif self.tokenizer.symbol() in ["(", "."]:
                    nArgs = 0
                    if self.tokenizer.symbol() == ".":
                        self.writeSymbol()  # .
                        if self.symbol_table.kindOf(name):
                            self.output.writePush(
                                self.get_segment(name), self.symbol_table.indexOf(name))
                            nArgs += 1
                            name = f"{self.symbol_table.typeOf(name)}.{self.tokenizer.identifier()}"
                        else:
                            name = f"{name}.{self.tokenizer.identifier()}"
                        self.writeIdentifier()
                    else:
                        # It is a method call on the current object
                        self.output.writePush("pointer", 0)
                        name = f"{self.class_name}.{name}"
                        nArgs += 1
                    self.writeSymbol()  # (
                    nArgs += self.compileExpressionList()
                    self.writeSymbol()  # )
                    self.output.writeCall(name, nArgs)
                else:
                    segment = self.get_segment(name)
                    if segment:
                        self.output.writePush(segment, self.symbol_table.indexOf(name))
                    else:
                        self.output.writePush("constant", 0)

            else:
                segment = self.get_segment(name)
                if segment:
                     self.output.writePush(segment, self.symbol_table.indexOf(name))
                else:
                    self.output.writePush("constant", 0)

        elif self.tokenizer.tokenType() == "INT_CONST":
            self.output.writePush("constant", self.tokenizer.intVal())
            self.writeIntVal()
        elif self.tokenizer.tokenType() == "STRING_CONST":
            string_val = self.tokenizer.stringVal()
            self.writeStringVal()
            self.output.writePush("constant", len(string_val))
            self.output.writeCall("String.new", 1)
            for char in string_val:
                self.output.writePush("constant", ord(char))
                self.output.writeCall("String.appendChar", 2)
        elif self.tokenizer.tokenType() == "KEYWORD":
            keyword = self.tokenizer.keyWord()
            if keyword == "true":
                self.output.writePush("constant", 0)
                self.output.writeArithmetic("not")
            elif keyword == "false" or keyword == "null":
                self.output.writePush("constant", 0)
            elif keyword == "this":
                self.output.writePush("pointer", 0)
            self.writeKeyword()

    # Compiles a (possibly empty) comma-separated list of expressions, returns the number of expressions in the list
    def compileExpressionList(self):
        nArgs = 0
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() == ")":
                    break
                elif self.tokenizer.symbol() == ",":
                    self.writeSymbol()
                    self.compileExpression()
                    nArgs += 1
                elif self.tokenizer.symbol() == "(":
                    self.compileExpression()
                    nArgs += 1
                else:
                    # Extra symbol so do nothing
                    pass
            else:
                self.compileExpression()
                nArgs += 1
        return nArgs

    def generate_label(self):
        label = f"{self.file_name}_{self.label_index}"
        self.label_index += 1
        return label

    def get_segment(self, name):
        kind = self.symbol_table.kindOf(name)
        if kind == "field":
            return "this"
        elif kind == "local":
            return "local"
        elif kind == "argument":
            return "argument"
        elif kind == "static":
            return "static"
        else:
            return None  # Should never happen

    def write_op(self, op):
        if op == "+":
            self.output.writeArithmetic("add")
        elif op == "-":
            self.output.writeArithmetic("sub")
        elif op == "*":
            self.output.writeCall("Math.multiply", 2)
        elif op == "/":
            self.output.writeCall("Math.divide", 2)
        elif op == "&":
            self.output.writeArithmetic("and")
        elif op == "|":
            self.output.writeArithmetic("or")
        elif op == "<":
            self.output.writeArithmetic("lt")
        elif op == ">":
            self.output.writeArithmetic("gt")
        elif op == "=":
            self.output.writeArithmetic("eq")

    def write_unary_op(self, op):
        if op == "-":
            self.output.writeArithmetic("neg")
        elif op == "~":
            self.output.writeArithmetic("not")

# How to run: python Main.py file.jack
if __name__ == "__main__":
    path = sys.argv[1]
    files = []

    if os.path.isdir(path):
        for file in os.listdir(path):
            if file.endswith(".jack"):
                files.append(os.path.join(path, file))
    else:
        files.append(path)

    print("List of Files: ", files)
    for file in files:
        tokenizer = JackTokenizer(file)
        output_file = file.replace(".jack", "C.vm")
        with open(output_file, "w") as output:
            # Print a stripped version of the file name without the extension and the path
            engine = ComplilationEngine(tokenizer, output, os.path.basename(file).replace(".jack", ""))
        print(f"Compiled {file} to {output_file}")
        engine.printSymbolTable()

    print("Done!")