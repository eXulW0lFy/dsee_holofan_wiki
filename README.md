# DSEE Holofan controller

This is a control app for DSEE holofans.

## Code structure

![UML-diagram](https://raw.githubusercontent.com/eXulW0lFy/dsee_holofan_wiki/dev/img/classes.png)

<!-- finally working image -->

### Connection

Data class, that combines sockets, ports, IPv4 addresses, and other data for connection to holofan. 1 holofan = 1 connection.

- `comm_socket: socket.socket` - socket for sending and receiving holofan [commands](#command).

- `file_socket: socket.socket` - socket for sending and receiving [video files](#video) and [video stream](#stream). Holofan uses 2 different port for commands and files, so there must me 2 different sockets.

- `_comm_socket_server_if_given: socket.socket|None` - server socket, given only if Connection was created by server (otherwise it is None). It is used only by [ConnectionManager](#connectionmanager) for closing this connection and freeing command port.

- `_file_socket_server_if_given: socket.socket|None` - server socket, given only if Connection was created by server (otherwise it is None). It is used only by [ConnectionManager](#connectionmanager) for closing this connection and freeing file port.

- `ip_addr: str` - IPv4 address. For server, it is client's address. Uses `'localhost'` by default, so server can listen for any connections in local network. For client, it is server's address.

- `comm_port: int` - TCP port for sending and receiving [commands](#command).

- `file_port: int` - TCP port for sending and receiving [video files](#video) and [video stream](#stream).

- `buff_size: int` - Buffer size of data in tcp packets. By default set to `1460`.

### ConnectionManager

Class for managing all available connections, creating/deleting one, sending and receiving [packets](#packet).

- `__connections: list[Connection]` - list of all available [connections](#connection).

- `new_connection(ip_addr, command_port, file_port, buff_size)` - Creates new [Connection](#connection). You must create new connection each time new holofan must be connected.

- `del_connection(idx)` - Deletes existing [Connection](#connection) by it's index in `__connections`.

- `close()` - Deletes all available [connections](#connection) and closes this app.

- `send(packet, dst_list: list | tuple)` - Sends [Packet](#packet) to multiple destinations. `dst_list` is a list or tuple of [connections](#connection) from `__connections`.

- `reveive(packet, src_list: list | tuple)` - Receives [Packet](#packet) from multiple sources. `src_list` is a list or tuple of [connections](#connection) from `__connections`.

- `__send_command(packet, dst)` - Sends [Command](#command) to single destination. `dst` is a [connections](#connection) from `__connections`.

- `__send_video(packet, dst)` - Sends [Video file](#video) to single destination. `dst` is a [connections](#connection) from `__connections`.

- `__send_stream(packet, dst)` - Sends [Video stream](#command) to single destination. `dst` is a [connections](#connection) from `__connections`.

- `__reveive_command(packet, src)` - Receives [Command](#command) from single sources. `src` is a [connections](#connection) from `__connections`.

### Packet

Base class for everything that can be sent to holofan.

- `__data: bytes` - Binary data to be sent to holofan. Private variable, inaccessible from outside this class.

- `get_data() -> bytes` - Getter for `__data`. Returns binary data ready to be sent.

- `__str__() -> str` - Realization of biult-in method to convert this object into str. Usually used for displaying on screen. Use: `str(packet)` or `f'{packet}'`

### Command

Clild class of [Packet](#packet) for command that can be sent to holofan.

- `__data: bytes` - Binary data to be sent to holofan. Private variable, inaccessible from outside this class.

- `__op_code: int` - Operation code value. Values were taken from captured traffic of DSEE holofasn.

- `__params: int` - Parameters value. Values were taken from captured traffic of DSEE holofasn. For most of commands set to `b'0000'` by default.

- `get_op_code()` - Static method, used to get code value of received command.

- `get_op_name()` - Static method, used to get code name of received command.

- `get_data() -> bytes` - Getter for `__data`. Returns binary data ready to be sent.

- `__str__() -> str` - Realization of biult-in method to convert this object into str. Usually used for displaying on screen. Use: `str(packet)` or `f'{packet}'`


### Video

Clild class of [Packet](#packet) for video files that can be sent to holofan.

- `__data: bytes` - Binary data to be sent to holofan. Private variable, inaccessible from outside this class.

- `__path: str` - Full absolute path to the file.

- `__folder_name: str` - Name of folders of the file. In other words, Full absolute path without file name and extention.

- `__file_name: str` - Name of file with extention.

- `get_properties()` - Static method, used to get video file properties, such as FPS, file size (in bytes), file name length.

- `encode_file() -> bytes` - Encodes video file with FFMPEG.

- `get_data() -> bytes` - Getter for `__data`. Returns binary data ready to be sent.

- `__str__() -> str` - Realization of biult-in method to convert this object into str. Usually used for displaying on screen. Use: `str(packet)` or `f'{packet}'`


### Stream

TODO

