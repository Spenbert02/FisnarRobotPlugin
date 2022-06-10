# Controlling the Fisnar from python via the RS232 port
The Fisnar can be controlled in real time via the RS232 port. Generally, there
are three main stages to the RS232 control process: initialization, command
packets, and finalization. The initialization process prepares the Fisnar
to be controlled by the RS232 port. The command packets consist of commands sent
to the Fisnar over the RS232 port and the verification bytes sent back from
the Fisnar. Lastly, the finalization process is a simply byte sequence sent to
the Fisnar over the RS232 port that terminates the RS232 control process.

## Fisnar RS232 settings
First, the Fisnar RS232 protocol uses the following settings (which can be seen
in the FisnarController initialization function):
- baud rate: 115200
- start bits: 1
- data bits: 8
- parity bit: none
- stop bits: 1

## Byte representation
Each byte that is sent over is represented by the ascii value associated with it.
[Ascii table](https://www.asciitable.com/) documentation has all the associated
character values.

## Initialization
The initialization sequence between the computer and the Fisnar takes the
following form, with the characters in each column representing the ascii
bytes (some bytes are represented in hexadecimal) that are sent from the
given column header to the opposite column header.

\# |Fisnar | Computer
---|-------|---------
1|| 0xf0 0xf0 0xf2
2|0xf0 |
3|<< BASIC BIOS 2.2 >>|
4|0x0d 0x0a|

If the computer sends byte sequence 1 and the Fisnar does not send all of
byte sequences 2-4, then the initialization failed. If initialization fails,
the finalization still has to be sent to take the Fisnar out of 'RS232 mode'.

## Command packets
Each command packet consists of sending over each ascii character in the
command string - one by one - with the Fisnar reciprocating each character for
confirmation, With a final 'ok!' confirmation. It should be noted that each
command string is terminated by
an 0x0d (carriage return in ascii) byte.

For commands that return a value, the value will be sent back to the computer
in ascii characters before the 'ok!' confirmation, terminated by an 0x0a
byte.

A sample command packet sequence
is given below, where the command being sent is 'VX 10.21', which indicates
a travel from the current position to x = 10.21 at the same y and z positions.

\# | Fisnar | Computer
---|--------|---------
1|| V
2|V|
3||X
4|X
5||1
6|1|
7||0
8|0|
9||.
10|.|
11||2
12|2|
13||1
14|1|
15||0x0d
16|0x0d|
17|0x0a
18|ok!|

Byte sequences 1 through 17 comprise the actual command and are sent
immediately in order, and the Fisnar sends byte sequence 18 once it
has successfully interpreted and executed the command. Once the 'ok!'
confirmation is received, the next command packet can be sent.

For documentation on specific RS232 commands, see the table below.

#### RS232 command list

Command | Action
------- | ------
VA \<x\>, \<y\>, \<z\>| move in a straight line from the current position to the <x, y, z> position
VX \<x\> | move from the current position to the given X = \<x\> position
VY \<y\> | move from the current position to the given Y = \<y\> position
VZ \<z\> | move from the current position to the given Z = \<z\> position
PX | get the current x position of the robot
PY | get the current y position of the robot
PZ | get the current z position of the robot
HM | travel to the home position
ID | execute and wait for a move command - this must be sent after each VA, VX, VY, and VZ command to initiate the movement - the 'ok!' confirmation is sent after the movement is completed
OU \<p\>, \<s\> | turn output pin \<p\> on if \<s\> is 0, or on if \<s\> is 1 - it then follows that \<s\> must either be '0' or '1'
SP \<s\> | set the line travel speed to \<s\>, in mm/sec

## Finalization
The finalization procedure tells the Fisnar to go out of 'RS232 mode'. That is,
it stops listening for bytes sent over the RS232 port. The procedure is very simple:

\# | Fisnar | Computer
---|--------|---------
1|| 0xdf 0x00

After that single byte sequence is sent from the computer to the Fisnar, the
Fisnar is no longer in RS232 mode and must be reinitialized before it can
be controller again.

The Fisnar must be taken out of RS232 mode before it can do any other functions,
so sending this command is critical to the performance of the Fisnar after it is
taken out of RS232 mode.
