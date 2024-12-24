// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

//// Replace this comment with your code.
(CLEAR)
@SCREEN
D=A
@0
M=D

(CHECKKEY) //Check if key is pressed
@1 
M=0
@KBD 
D=M 
@DRAW //If key is not pressed set value in R1 to 0 (will clear screen)
D;JEQ 

(SETBLACK) //Set R1 to black value
@1 
M=-1 

(DRAW)
@1 //Grab color from R1
D=M 
@0 //Get index of pixel to fill and fill it
A=M 
M=D 
@0 //Go to next pixel in line
DM=M+1 
@KBD 
D=A-D 
@DRAW //Continue drawing untill screen is filled
D;JGT 
@CLEAR //Go back to beggining
0;JMP 