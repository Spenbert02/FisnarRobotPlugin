# Controlling the Fisnar from python via the RS 232 port
The Fisnar can be controlled from within python via the RS232 port. Fisnar
(the company) has been very unhelpful in figuring out the format that these
commands need to be in, so some work has been done to figure out the command
format by 'packet sniffing' (tracking the packets of bytes that are sent over
the RS232 port during the command upload process). All RS232 communication occurs
in the SerialUploader class (SerialUploader.py) - the user initiates the serial
upload procedure from the extension menu in Cura.

There are a few areas of prerequisite knowledge for this document: [RS232 protocol](https://circuitdigest.com/article/rs232-serial-communication-protocol-basics-specifications#:~:text=RS232%20is%20a%20standard%20protocol,data%20exchange%20between%20the%20devices.)
and [single-precision (32 bit) floating point number representation](https://www.geeksforgeeks.org/ieee-standard-754-floating-point-numbers/).
Also, it might be useful to know the different ways that bytes can be represented
([see here](http://www.edu4java.com/en/concepts/hexadecimal-binary-number-byte-bit-word.html)).

## Fisnar RS232 settings
First, the Fisnar RS232 protocol uses the following settings (which can be seen
in the SerialUploader initialization function):
- baud rate: 115200
- start bits: 1
- data bits: 8
- parity bit: none
- stop bits: 1

## General communication format
The figure below shows the flow of communication that is used when a sequence
of commands are uploaded over the RS232 port.

![](doc_pics/RS232_comm_figure.png)

The general structure consists of the initialization, many commands,
and the finalization. To let the Fisnar know commands are about to be sent, the host computer sends two 0xF0 bytes over. If the Fisnar is able to receive commands, it will return with a single 0xF0 byte.

After initialization, up to 65,535 commands can be sent over in the 'command bytes' format shown in the figure. First, the host computer sends an 0xe8 byte to prepare the Fisnar for the immediately incoming command. Then, the actual command bytes are uploaded in the format described in the next section. Part of this command format is a checksum - a form of error checking. When the Fisnar receives a command, it will calculate the 
