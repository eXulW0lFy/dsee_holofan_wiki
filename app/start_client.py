try:
    import cv2
except ImportError:
    print('You must install opencv-python and numpy. '
          'To get more info see `requirements.txt` file.')
    print('Необходимо установить opencv-python и numpy. '
          'Для подробностей см. файл `requirements.txt`.')
import binascii
import socket
import sys
import os
from argparse import ArgumentParser, ArgumentTypeError
import logging
from command import Command


# creating log file
log_file = os.path.join('..', 'client.log')
if not os.path.isfile(log_file) or \
        os.path.getsize(log_file) > 5120:
    open(log_file, 'w').close()
fh = logging.FileHandler(log_file, mode="a")
ftm = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(ftm)
logger = logging.getLogger('client')
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)


class Client:
    def __init__(self,
                 server_ip: str,
                 server_port: int,
                 buff_size: int) -> None:
        """Creates instance of client

        Args:
            server_ip (str): Server's IP address for connection.
            client_port (int): Port number in range [1024, 65535]
            buff_size (int): Max data size in packet.
                Default (1460) as in DSEE-65H
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.buff_size = buff_size

        self.is_binary_mode = False

    def create_connection(self):
        """Creates socket connection.

        Creates a value:
                self.client_socket (socket.socket): client's instance
                self.client_socket (socket.socket): Client's instance
        """
        try:
            # socket.AF_INET = IPv4; socket.SOCK_STREAM = TCP
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.connect((self.server_ip, self.server_port))
        except ConnectionRefusedError as msg:
            logger.error(f'Unable to connect to server: {msg}')
            quit(2)
        else:
            logger.info(f'Client connected to server {self.server_ip}')
            # server_socket.settimeout(0.2)
            self.server_socket = server_socket

    def menu(self):
        """Receive packet and check type (command or file)"""
        received = self.server_socket.recv(self.buff_size).hex()
        logger.debug(f'Received {received[:12]}')
        if received.startswith('05'):  # commands
            self.receive(received)
        elif received == '01':  # files
            self.is_binary_mode = True
            # receive file
            received = self.server_socket.recv(self.buff_size)
            self.receive_file(received)
            self.is_binary_mode = False

    def receive(self, received: str):
        """Parse received command"""
        op_code = int(received[6:8], 16)
        op_name = Command.describe(op_code)
        print(f'Received command: {op_name}')
        logger.info(f'Received command: {op_name}')

        # call function by str name
        response = getattr(Command(), op_name)(is_request=False)
        self.server_socket.send(response.get_data())  # file received
        logger.debug('Response has been sent')

    def receive_file(self, received: str):
        """Receive and parse video file"""
        data = b''
        file_size = int(binascii.hexlify(received[:10]), 16)
        name_len = int(binascii.hexlify(received[14:16]), 16)
        file_path = os.path.join('..', 'media', 'tmp',
                                 received[16:16+name_len].decode('utf-8'))
        logger.debug(f'Received {received[:16+name_len]}')

        data += received
        while len(data) < file_size:
            received = self.server_socket.recv(self.buff_size)
            if len(data) >= file_size:
                logger.info('File has been received')
                break
            data += received

        # Send `change binary mode` status (b'01')
        self.server_socket.send(b'\x01')

        with open(file_path, 'wb') as file:
            file.write(data[16+name_len:])
            logger.info('File was written')

        self.play(file_path)

    def play(self, file_path):
        """Play video file using OpenCV (cv2) python library.

        Args:
            file_path (_type_): path to file
        """
        WINDOW_NAME = 'Dsee-65H Holofan Imitation'
        cv2.namedWindow(WINDOW_NAME)
        cv2.moveWindow(WINDOW_NAME, 0, 0)
        cv2.resizeWindow(WINDOW_NAME, 800, 600)
        logger.info(f'Window named "{WINDOW_NAME}" has been opened')

        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            logger.error('Error opening file')
            cap.release()  # clear window
            cv2.destroyAllWindows()  # close window
            logger.info(f'Window named "{WINDOW_NAME}" has been closed')
            return

        # Read the entire file until it is completed
        while cap.isOpened():  # while status OK
            ret, frame = cap.read()
            if not ret:  # if status not OK: break
                break

            cv2.imshow(WINDOW_NAME, frame)  # else: display frame
            if (cv2.waitKey(34) & 0xFF) == 27:  # Esc
                break  # whole playing ends

        # When everything done, release the capture
        cap.release()  # clear window
        cv2.destroyAllWindows()  # close window
        logger.info(f'Window named "{WINDOW_NAME}" has been closed')
        return


if __name__ == '__main__':
    """Prepares launch parameters.

    This section parses command-line arguments to prepare for client start.

    Args/Vars:
        client_ip (str): client's IP address for connection.
        client_port (int): Port number in range [1024, 65535]
        buff_size (int): Max data size in packet. Default (1460) as in DSEE-65H
    """
    # parsing of command-line args
    parser = ArgumentParser()
    parser.add_argument('-i', '--ipaddr', default='localhost')
    parser.add_argument('-p', '--port', type=int, default=6060)
    parser.add_argument('-b', '--buff', type=int, default=1460)
    params = parser.parse_args(sys.argv[1:])

    # assigning all parameters
    server_ip = params.ipaddr

    server_port = params.port
    if not 1024 <= server_port <= 65535:
        raise ArgumentTypeError('Invalid port number')
        quit(2)

    buff_size = params.buff
    if not 1024 <= buff_size <= 1600:
        raise ArgumentTypeError('Invalid buff size number')
        quit(2)

    client = Client(server_ip, server_port, buff_size)
    client.create_connection()
    while True:
        client.receive()
