# Provides routines that skip comments and white space, get the next token, and advance
# the input exactly beyond it. Other routines return the type of the current token, and its value.

import re
import sys
import os


# tokens = {
#     "KEYWORD": ["class", "constructor", "function", "method", "field", "static", "var", "int", "char", "boolean", "void", "true", "false", "null", "this", "let", "do", "if", "else", "while", "return"],
#     "SYMBOL": ["{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*", "/", "&", "|", "<", ">", "=", "~"],
#     "INT_CONST": [],
#     "STRING_CONST": [],
#     "IDENTIFIER": []
# }


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
        # self.current_token = ""
        self.current_line = 0
        self.tokenize() # Tokenize the input file
        

    # Go through each line and add each token to the list
    def tokenize(self):
        for line in self.lines:
            tokens = re.findall(r'"[^"]*"|\w+[:?]?|[\d]+|[\W]', line)
            for token in tokens:
                if token.startswith('"') and token.endswith('"'):
                    # print(token)
                    self.tokens.append(token)
                elif token.strip():
                    # print(token)
                    self.tokens.append(token.strip())
        self.current_token = self.tokens[0]
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
        return self.current_token
    def stringVal(self):
        #get rid of " at the beginning and end of the string"
        return self.current_token[1:-1]

    



class ComplilationEngine:
    def __init__(self, tokenizer, output):
        # Input: tokenizer object
        self.tokenizer : JackTokenizer = tokenizer
        # File object to write the output to
        self.output = output
        self.indent = 0
        self.compileClass()
    
    advance = lambda self: self.tokenizer.advance()
    write = lambda self, text: self.output.write("  " * self.indent + text + "\n")
    # Make iall write keywords advance the tokenizer
    def writeKeyword(self):
        self.write(f"<keyword> {self.tokenizer.keyWord()} </keyword>")
        self.advance()
    def writeSymbol(self):
        self.write(f"<symbol> {self.tokenizer.symbol()} </symbol>")
        self.advance()
    def writeIdentifier(self):
        self.write(f"<identifier> {self.tokenizer.identifier()} </identifier>")
        self.advance()
    def writeIntVal(self):
        self.write(f"<integerConstant> {self.tokenizer.intVal()} </integerConstant>")
        self.advance()
    def writeStringVal(self):
        self.write(f"<stringConstant> {self.tokenizer.stringVal()} </stringConstant>")
        self.advance()
    def writeType(self):
        self.write(f"<type> {self.tokenizer.identifier()} </type>")
        self.advance()


    # Compiles a complete class
    def compileClass(self):
        self.write("<class>")
        self.indent += 1
        self.writeKeyword()
        
        self.writeIdentifier()
        
        self.writeSymbol()
        while self.tokenizer.hasMoreTokens():
            # self.advance()
            if self.tokenizer.tokenType() == "KEYWORD":
                if self.tokenizer.keyWord() in ["constructor", "function", "method"]:
                    self.compileSubroutine()
                elif self.tokenizer.keyWord() in ["field", "static"]:
                    self.compileClassVarDec()
            elif self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() == "}":
                    self.writeSymbol()
                    break
        self.indent -= 1
        self.write("</class>")

    def compileClassVarDec(self):
        self.write("<classVarDec>")
        self.indent += 1
        self.writeKeyword()
        
        # If keyword is not a type, then it's an identifier
        if self.tokenizer.tokenType() == "IDENTIFIER":
            self.writeIdentifier()
        elif self.tokenizer.tokenType() == "KEYWORD":
            self.writeKeyword()
        else:
            self.writeType()

        self.writeIdentifier()
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "SYMBOL":
                current_symbol = self.tokenizer.symbol()    
                if current_symbol == ";":
                    self.writeSymbol()
                    break
                elif current_symbol == ",":
                    self.writeSymbol()
                else:
                    self.writeSymbol()
            elif self.tokenizer.tokenType() == "IDENTIFIER":
                self.writeIdentifier()
        self.indent -= 1
        self.write("</classVarDec>")

    def compileSubroutine(self):
        self.write("<subroutineDec>")
        self.indent += 1
        self.writeKeyword()
        # Check if keyword is a type
        if self.tokenizer.tokenType() == "KEYWORD":
            self.writeKeyword()
        else:
            self.writeIdentifier()
        
        self.writeIdentifier()
        
        self.writeSymbol()
        self.compileParameterList()
        self.writeSymbol()
        
        self.compileSubroutineBody()
        
        self.indent -= 1
        self.write("</subroutineDec>")
    
    # Compiles a (possibly empty) parameter list. Does not handle the enclosing paretnhesis tokens ( and )
    def compileParameterList(self):
        self.write("<parameterList>")
        self.indent += 1
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() == ")":
                    break
                elif self.tokenizer.symbol() == ",":
                    self.writeSymbol()
                else:
                    self.writeSymbol()
            else:
                self.writeKeyword()
                self.writeIdentifier()
            
            

        self.indent -= 1
        self.write("</parameterList>")
    
    # Compiles a subroutine's body
    def compileSubroutineBody(self):
        self.write("<subroutineBody>")
        self.indent += 1
        self.writeSymbol()
        # print(self.tokenizer.tokens) 
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "KEYWORD":
                if self.tokenizer.keyWord() == "var":
                    self.compileVarDec()
                else:
                    break

        self.compileStatements()
        self.writeSymbol()
        self.indent -= 1
        self.write("</subroutineBody>")

    # Compiles a var declaration
    def compileVarDec(self):
        self.write("<varDec>")
        self.indent += 1
        self.writeKeyword()
        # If keyword is not a type, then it's an identifier
        if self.tokenizer.tokenType() == "KEYWORD":
            self.writeKeyword()
        else:
            self.writeIdentifier()

        self.writeIdentifier()
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() == ";":
                    self.writeSymbol()
                    break
                elif self.tokenizer.symbol() == ",":
                    self.writeSymbol()
                # Write a empty symbol because it's not a comma or semicolon
                else:
                    self.writeSymbol()
            elif self.tokenizer.tokenType() == "IDENTIFIER":
                self.writeIdentifier()
        self.indent -= 1
        self.write("</varDec>")

    # Compiles a sequence of statements. Does not handle the enclosing curly bracket tockens { and }
    def compileStatements(self):
        self.write("<statements>")
        self.indent += 1
        while self.tokenizer.hasMoreTokens():
            # print(self.tokenizer.current_token)
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
        self.indent -= 1
        self.write("</statements>")

    # Compiles a let statement
    def compileLet(self):
        self.write("<letStatement>")
        self.indent += 1
        self.writeKeyword()
        self.writeIdentifier()
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() == "[":
                    self.writeSymbol()
                    self.compileExpression()
                    self.writeSymbol()
                elif self.tokenizer.symbol() == "=":
                    self.writeSymbol()
                    self.compileExpression()
                    break
        self.writeSymbol()
        self.indent -= 1
        self.write("</letStatement>")

    # Compiles an if statement, possibly with a trailing else clause
    def compileIf(self):
        self.write("<ifStatement>")
        self.indent += 1
        self.writeKeyword()
        
        self.writeSymbol()
        self.compileExpression()
        self.writeSymbol()
        
        self.writeSymbol()
        self.compileStatements()
        self.writeSymbol()
        if self.tokenizer.hasMoreTokens():
            if self.tokenizer.keyWord() == "else":
                self.writeKeyword()
                self.writeSymbol()
                self.compileStatements()
                self.writeSymbol()
        self.indent -= 1
        self.write("</ifStatement>")

    # Compiles a while statement
    def compileWhile(self):
        self.write("<whileStatement>")
        self.indent += 1
        self.writeKeyword()
        
        self.writeSymbol()
        self.compileExpression()
        self.writeSymbol()
        
        self.writeSymbol()
        self.compileStatements()
        self.writeSymbol()

        self.indent -= 1
        self.write("</whileStatement>")
    
    # Compiles a do statement
    def compileDo(self):
        self.write("<doStatement>")
        self.indent += 1
        self.writeKeyword()
        self.writeIdentifier()
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() == "(":
                    self.writeSymbol()
                    self.compileExpressionList()
                    self.writeSymbol()
                elif self.tokenizer.symbol() == ".":
                    self.writeSymbol()
                    self.writeIdentifier()
                elif self.tokenizer.symbol() == ";":
                    self.writeSymbol()
                    break
        self.indent -= 1
        self.write("</doStatement>")

    # Compiles a return statement
    def compileReturn(self):
        self.write("<returnStatement>")
        self.indent += 1
        self.writeKeyword()
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() == ";":
                    self.writeSymbol()
                    break
                else:
                    self.writeSymbol()
            else:
                self.compileExpression()
        self.indent -= 1
        self.write("</returnStatement>")

    # Compiles an expression
    def compileExpression(self):
        self.write("<expression>")
        self.indent += 1
        self.compileTerm()
        while self.tokenizer.hasMoreTokens():
            print("inside expression", self.tokenizer.current_token)
            if self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() in ["+", "-", "*", "/", "&", "|", "<", ">", "="]:
                    # If we have > or <, we need to trnslate to &gt; and &lt;
                    if self.tokenizer.symbol() == "<":
                        self.write("<symbol> &lt; </symbol>")
                        self.advance()
                    elif self.tokenizer.symbol() == ">":
                        self.write("<symbol> &gt; </symbol>")
                        self.advance()
                    elif self.tokenizer.symbol() == "&":
                        self.write("<symbol> &amp; </symbol>")
                        self.advance()
                    # elif self.tokenizer.symbol() == "=":

                    else:
                        self.writeSymbol()
                    
                    
                    # self.writeSymbol()
                    self.compileTerm()
                else:
                    break
            else:
                break
        self.indent -= 1
        self.write("</expression>")
    
    # Compiles a term. If the current token is an identifier, the routine must resolve it into a variable, an array entry, or a subroutine call
    # A single lookeahead token, which may be one of [, (, or . suffices to distinguish between the possibilities. 
    # Any other token is not part of this term and should not be advanced over

    def compileTerm(self):
        self.write("<term>")
        self.indent += 1
        while self.tokenizer.hasMoreTokens():
            if self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() == "(":
                    self.writeSymbol()
                    self.compileExpression()
                    self.writeSymbol()
                    break
                elif self.tokenizer.symbol() in ["-", "~"]:
                    self.writeSymbol()
                    self.compileTerm()
                    break

                else:
                    break    
                # # self.writeSymbol()
                    # break
            elif self.tokenizer.tokenType() == "IDENTIFIER":
                self.writeIdentifier()
                if self.tokenizer.tokenType() == "SYMBOL":
                    if self.tokenizer.symbol() == "[":
                        self.writeSymbol()
                        self.compileExpression()
                        self.writeSymbol()
                    elif self.tokenizer.symbol() == ".":
                        self.writeSymbol()
                        self.writeIdentifier()
                        self.writeSymbol()
                        self.compileExpressionList()
                        self.writeSymbol()
                    elif self.tokenizer.symbol() == "(":
                        self.writeSymbol()
                        self.compileExpressionList()
                        self.writeSymbol()
            elif self.tokenizer.tokenType() == "INT_CONST":
                self.writeIntVal()
            elif self.tokenizer.tokenType() == "STRING_CONST":
                self.writeStringVal()
            elif self.tokenizer.tokenType() == "KEYWORD":
                self.writeKeyword()
        
        self.indent -= 1
        self.write("</term>")



    # Compiles a (possibly empty) comma-separated list of expressions, returns the number of expressions in the list
    def compileExpressionList(self):
        self.write("<expressionList>")
        self.indent += 1
        while self.tokenizer.hasMoreTokens():
            print(self.tokenizer.current_token)
            if self.tokenizer.tokenType() == "SYMBOL":
                if self.tokenizer.symbol() == ")":
                    break
                elif self.tokenizer.symbol() == "(":
                    self.compileExpression()
                elif self.tokenizer.symbol() == ",":
                    self.writeSymbol()
                    self.compileExpression()
            else:
                print("Compiing list")
                self.compileExpression()
            
        self.indent -= 1
        self.write("</expressionList>")

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

    print(files)
    for file in files:
        tokenizer = JackTokenizer(file)
        output = open(file.replace(".jack", "T.xml"), "w")
        engine = ComplilationEngine(tokenizer, output)
        output.close()

    