Reverse engineered client implementation of the Stratasys proprietary network protocol that presents data from a Stratasys 3D printer via a JSON based web interface. A basic web GUI utilizing bootstrap is also provided.

# Requirements
 * Python 3.x
 * flask

# Stratasys Protocol Documentation
The network protocol used by Stratasys machines uses a request/response system, listening on port 53742, where all commands and responses are null terminated C strings, padded to 64 bytes if shorter than such. Furthermore, the commands are sent such that the command is sent first, followed by each of its arguments as a separate 64 byte message. The argument list is then terminated by sending the negative acknowledgement command, NA. Once a full command and arguments is sent, the command and arguments are then sent back to the sender and have to be acknowledged individually with an acknowledgement, 'OK'. Furthermore, when a command is sent that will return more than 64 bytes, the machine will respond with a packet containing an ASCII string comprised of only digits. In this case, the numeric value of the string is the size of the data payload that is to be returned. If this is acknowledged by replying with 'OK', the next N bytes of data returned will then be returned. Putting this all together, sending the 'GetFile' command followed by the argument 'status.sts' and 'NA', replying OK to all responses and finally reading N bytes from the socket will allow you to read the full machine status.
