// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
// The algorithm is based on repetitive addition.

//// Replace this comment with your code.
@R2 //Reset R2 
M=0

@R0
D=M 

//If any of the variables are zero, jump to end
@END
D;JEQ 
@1 
D=M 
@END 
D;JEQ

//Add R2 as many times as the constant 1 goes into R1
(LOOP)
@R1 //Get value of R1 (Addition Number)
D=M
@R2 //SET R2 = R2+D
M=D+M 
@R0 //Go and edit R0 to subtract its number for addition
M=M-1 //Subtract
D=M 
@LOOP //Keep on looping through as long as R0 > 0
D;JGT 

(END)
@END
0;JMP
	
