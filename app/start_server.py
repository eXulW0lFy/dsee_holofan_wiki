import socket
import sys
import os
from argparse import ArgumentParser, ArgumentTypeError
import logging
from video import Video
from command import Command


log_file = os.path.join('..', 'server.log')
if not os.path.isfile(log_file) or \
        os.path.getsize(log_file) > 5120:
    open(log_file, 'w').close()
fh = logging.FileHandler(log_file, mode="a")
ftm = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(ftm)
logger = logging.getLogger('server')
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)


class Server:
    def __init__(self,
                 client_ip: str,
                 server_port: int,
                 buff_size: int) -> None:
        """Creates instance of server

        Args:
            client_ip (str): Used to limit client's IP address for connection.
                If empty string, it uses all interfaces.
            client_port (int): Port number in range [1024, 65535]
            buff_size (int): Max data size in packet.
                Default (1460) as in DSEE-65H
        """
        self.client_ip = client_ip
        self.server_port = server_port
        self.buff_size = buff_size

        self.is_binary_mode = False

    def create_connection(self):
        """Creates socket connection with client.

        Creates a pair of values as tuple:
                self.server_socket (socket.socket): Server's instance
                self.client_socket (socket.socket): Client's instance
        """
        # open socket
        try:
            # socket.AF_INET is IPv4; socket.SOCK_STREAM is TCP
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # '' opens socket for everyone
            server_socket.bind(('', self.server_port))
        except (socket.error, KeyboardInterrupt) as msg:
            logger.warning(f'Server failed: {msg}')
            print(msg)
            server_socket.close()
            quit(2)
        else:
            logger.info(f'Server started on port {self.server_port}')
            print(f'Server started on port {self.server_port}')

        # wait for 1 client
        try:
            server_socket.listen(1)
            client_socket, _ = server_socket.accept()
        except (socket.error, KeyboardInterrupt) as msg:
            logger.warning(f'Client failed: {msg}')
            print(msg)
            client_socket.close()
            server_socket.close()
            quit(2)
        else:
            logger.info(f'Client {self.client_ip} connected to server')
            print(f'Client {self.client_ip} connected to server')
            # server_socket.settimeout(0.2)
            self.server_socket = server_socket
            self.client_socket = client_socket

    def menu(self):
        print('\n\nВыберите команду')
        print('\t0. Выйти')
        print('\t1. Выбрать видеофайл')
        print('\t2. Включить вентилятор')
        print('\t3. Выключить вентилятор')
        print('\t4. Изменить яркость')
        print('\t5. Очистить плейлист')
        print('\t6. Приостановить')
        print('\t7. Возобновить')
        print('\t8. Перейти к видео')
        print('\t9. Сохранить плейлист')
        print('\t10. Изменить угол поворота')
        print('\t11. Сдвиг по оси x')
        print('\t12. Изменить маску')
        print('\t13. Изменить цвет фона')
        print('\t14. Изменить размер внутреннего диаметра')
        print('\t15. Сброс настроек')
        print('\t16. Сменить плейлист')
        print('\t17. Изменить интервал между видео')
        print('\t18. Изменить скорость вентилятора')

        i = int(input('>>> '))
        match i:
            case 0:
                self.server_socket.close()
                self.client_socket.close()
                quit(0)
            case 1:
                file_name = input('Введите имя файла: ')
                file_path = os.path.join('..', 'media', file_name)
                # print(os.path.abspath(file_path))
                file = Video(os.path.abspath(file_path))
                self.send_file(file)
                return
            case 2:
                command = Command().fan_on()
            case 3:
                command = Command().fan_off()
            case 4:
                print('Введите яркость (от 0 до 15)')
                p = int(input('>>> '))
                command = Command().set_brightness(p)
            case 5:
                command = Command().clear_playlist()
            case 6:
                command = Command().pause_playlist()
            case 7:
                command = Command().resume_playlist()
            case 8:
                print('Введите номер видео')
                p = int(input('>>> '))
                command = Command().select_in_playlist()
            case 9:
                command = Command().save_playlist()
            case 10:
                print('Введите угол поворота (от 0 до 30)')
                p = int(input('>>> '))
                command = Command().set_angle(p)
            case 11:
                print('Введите сдвиг по оси x')
                p = int(input('>>> '))
                command = Command().offset_x(p)
            case 12:
                print('Выберите маску')
                print('\t0 - нет')
                print('\t1 - сверху')
                print('\t2 - снизу')
                print('\t3 - микс)')
                p = int(input('>>> '))
                command = Command().set_mask(p)
            case 13:
                print('Выберите цвет фона')
                print('\t0 - белый')
                print('\t1 - чёрный')
                p = int(input('>>> '))
                command = Command().set_bg_color(p)
            case 14:
                print('Введите размер внутреннего диаметра (от 0 до 255)')
                p = int(input('>>> '))
                command = Command().inner_diameter(p)
            case 15:
                command = Command().reset_settings()
            case 16:
                print('Введите номер плейлиста')
                p = int(input('>>> '))
                command = Command().change_playlist(p)
            case 17:
                print('Введите интервал (сек)')
                p = int(input('>>> '))
                command = Command().set_play_interval(p)
            case 18:
                print('Выберите скорость вращения')
                print('\t0 - обычная')
                print('\t1 - медленная')
                print('\t2 - быстрая')
                p = int(input('>>> '))
                command = Command().set_rotation_speed(p)
            case _:
                return

        self.send_command(command)

    def send_command(self, request: Command):
        self.client_socket.send(request.get_data())
        response = self.client_socket.recv(self.buff_size)  # wait for response
        logger.debug(response)

    def send_file(self, file: Video):
        self.is_binary_mode = True
        self.client_socket.send(b'\x01')  # binary mode
        data = file.get_data()
        packet_idx = 0
        while packet_idx * buff_size < len(data):
            self.client_socket.send(data[packet_idx * buff_size:
                                         (packet_idx+1) * buff_size])
            packet_idx += 1
        response = self.client_socket.recv(self.buff_size)  # wait for b'01'
        logger.debug(response)


if __name__ == '__main__':
    """Prepares launch parameters.

    This section parses command-line arguments to prepare for server start.

    Args/Vars:
        client_ip (str): Used to limit client's IP address for connection.
            If empty string, it uses all interfaces.
        client_port (int): Port number in range [1024, 65535]
        buff_size (int): Max data size in packet. Default (1460) as in DSEE-65H
    """
    # parsing command line args
    parser = ArgumentParser()
    parser.add_argument('-i', '--ipaddr', type=str, default='localhost')
    parser.add_argument('-p', '--port', type=int, default=6060)
    parser.add_argument('-b', '--buff', type=int, default=1460)
    params = parser.parse_args(sys.argv[1:])

    # assigning all parameters
    client_ip = params.ipaddr

    server_port = params.port
    if not 1024 <= server_port <= 65535:
        raise ArgumentTypeError('Invalid port number')
        quit(2)

    buff_size = params.buff
    if not 1024 <= buff_size <= 1600:
        raise ArgumentTypeError('Invalid buff size number')
        quit(2)

    server = Server(client_ip, server_port, buff_size)
    server.create_connection()
    while True:
        server.menu()
