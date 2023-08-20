import binascii
import socket
import sys
import os
from argparse import ArgumentParser, ArgumentTypeError
import logging
import cv2
from command import Command


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

    def launch(self):
        pass
        # self.video = FragmentedVideo()

        # self.video_received = Event()
        # thread_receive = Thread(target=self.receiving,
        #                         args=(),
        #                         name='receiving fragment')
        # thread_play = Thread(target=self.playing,
        #                      args=(),
        #                      name='send pseudo stream')
        # try:
        #     thread_receive.start()
        #     thread_play.start()
        #     thread_receive.join()
        #     thread_play.join()
        # finally:  # whatever happens, all connections will be closed
        #     self.server_socket.close()
        #     self.video.clear()
        # "\x05\x35\xa4\x05\x00\x00"

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
            logger.warning(f'Connection failed: {msg}')
            print(f'Connection failed: {msg}')
            quit(2)
        else:
            logger.warning(f'Client connected to server {self.server_ip}')
            print(f'Client connected to server {self.server_ip}')
            # server_socket.settimeout(0.2)
            self.server_socket = server_socket

    def receive(self):
        request = self.server_socket.recv(self.buff_size).hex()
        logger.debug(request)
        if request.startswith('05'):
            op_name = Command.describe(request)
            print(f'Received command: {op_name}')
            logger.info(f'Received command: {op_name}')

            # call function by str name
            response = getattr(Command(), op_name)(is_request=False)
            self.server_socket.send(response.get_data())  # file received
        elif request == '01':
            self.is_binary_mode = True
            self.receive_file()
            self.is_binary_mode = False

    def receive_file(self):
        data = b''
        receive = self.server_socket.recv(self.buff_size)
        file_size = int(binascii.hexlify(receive[:10]), 16)
        name_len = int(binascii.hexlify(receive[14:16]), 16)
        file_path = os.path.join('..', 'media', 'tmp',
                                 receive[16:16+name_len].decode('utf-8'))

        data += receive
        while len(data) < file_size:
            print(f'{len(data)} < {file_size}')
            receive = self.server_socket.recv(self.buff_size)
            if len(data) >= file_size:
                logger.debug('File has been received')
                break
            data += receive
        self.server_socket.send(b'\x01')

        with open(file_path, 'wb') as file:
            file.write(data[16+name_len:])
            print('file was written')
        self.play(file_path)

    def play(self, file_path):
        WINDOW_NAME = 'Dsee-65H Holofan Imitation'
        cv2.namedWindow(WINDOW_NAME)
        cv2.moveWindow(WINDOW_NAME, 0, 0)
        cv2.resizeWindow(WINDOW_NAME, 800, 600)
        logger.info(f'Player "{WINDOW_NAME}" has been initialized')

        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            logger.warning('Error opening file')
            cap.release()
            cv2.destroyAllWindows()
            return

        # Read the entire file until it is completed
        while cap.isOpened():  # status OK
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow(WINDOW_NAME, frame)  # Display the resulting frame
            if (cv2.waitKey(34) & 0xFF) == 27:  # Esc
                break  # whole playing ends

        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()

        logger.info('Stop playing stream')
        print('Stop playing stream')
        return

    # def receiving(self):
    #     self.last_received = -1
    #     idx = -1
    #     while True:
    #         idx += 1
    #         # receiving b'01'
    #         response = self.server_socket.recv(self.buff_size)
    #         if response != b'01':
    #             break
    #         # we dont know file name yet
    #         data = self.server_socket.recv(self.buff_size)
    #         # first 69 bytes is header
    #         # convert hex length to dec
    #         logger.info(f'Converting {data[69:71]} from hex to dec')
    #         length = int(data[69:71], 16)
    #         # название файла
    #         frag_path = os.path.join('media', 'tmp',
    #                                  data[71:71+length].decode('utf-8'))

    #         with open(frag_path, 'wb') as frag_file:
    #             while True:
    #                 data = self.server_socket.recv(self.buff_size)
    #                 if not data:
    #                     logger.debug(f'File {frag_file} has been written')
    #                     break
    #                 frag_file.write(data)
    #         self.video.open(frag_file)

    #         self.last_received = idx
    #         self.video_received.set()  # now it's received, can play fragment

    #         self.server_socket.send(b'01')  # file received

    # def playing(self):
    #     WINDOW_NAME = 'Dsee-65H Holofan Imitation'
    #     cv2.namedWindow(WINDOW_NAME)
    #     cv2.moveWindow(WINDOW_NAME, 0, 0)
    #     cv2.resizeWindow(WINDOW_NAME, 800, 600)
    #     logger.info(f'Player "{WINDOW_NAME}" has been initialized')

    #     idx = -1
    #     while True:
    #         idx += 1

    #         # if file to play hasn't been received yet
    #         if self.last_received < idx:
    #             self.video_received.wait()  # wait until it is received
    #         frag_path = self.video.get_path(idx)

    #         cap = cv2.VideoCapture(frag_path)
    #         if not cap.isOpened():
    #             logger.warning('Error opening file')
    #             break

    #         # Read the entire file until it is completed
    #         while cap.isOpened():  # status OK
    #             ret, frame = cap.read()
    #             if not ret:
    #                 break

    #             cv2.imshow(WINDOW_NAME, frame)  # Display the resulting frame
    #             if (cv2.waitKey(34) & 0xFF) == 27:  # Esc
    #                 break  # whole playing ends

    #     # When everything done, release the capture
    #     cap.release()
    #     cv2.destroyAllWindows()

    #     logger.info('Stop playing stream')
    #     print('Stop playing stream')
    #     raise SystemExit('EXIT')


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
    # client.launch()
