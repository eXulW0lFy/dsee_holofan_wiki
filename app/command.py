import binascii
import logging
import os


log_file = os.path.join('..', 'command.log')
if not os.path.isfile(log_file) or \
        os.path.getsize(log_file) > 5120:
    open(log_file, 'w').close()
fh = logging.FileHandler(log_file, mode="a")
ftm = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(ftm)
logger = logging.getLogger('command')
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)


class Command():
    operations = {
        'fan_on': 1,
        'fan_off': 2,
        'set_brightness': 3,
        'clear_playlist': 5,
        'pause_playlist': 6,
        'resume_playlist': 7,
        'select_in_playlist': 8,
        'save_playlist': 12,
        'set_angle': 17,
        'offset_x': 32,
        'set_mask': 34,
        'set_bg_color': 35,
        'inner_diameter': 36,
        'reset_settings': 46,
        'change_playlist': 53,
        'set_play_interval': 54,
        'set_rotation_speed': 55
    }

    def __init__(self) -> None:
        """General class for every type of command."""
        self._packet = b''
        self.op_code = 0
        self.parameters = 0

    @staticmethod
    def get_op_code(op_name: str) -> int:
        op_code = Command.operations.get(op_name, None)
        if op_code is None:
            raise KeyError('Unknown operator name')
        return op_code

    def get_data(self) -> str:
        if self.is_request is True:
            self._packet += binascii.unhexlify('05')  # mode
        self._packet += binascii.unhexlify('35a4')  # unknown (id?)
        if self.is_request is True:
            # operation code, hex (only for request)
            self._packet += binascii.unhexlify(f'{self.op_code:02x}')
        self._packet += binascii.unhexlify(f'{self.parameters:04x}')  # param
        return self._packet

    @staticmethod
    def describe(data: str) -> str:
        op_code = int(data[6:8], 16)
        op_name = 'unknown'
        for key, value in Command.operations.items():
            if value == op_code:
                op_name = key
                break
        return op_name

    def fan_on(self, is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('fan_on')
        self.is_request = is_request
        return self

    def fan_off(self, is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('fan_off')
        self.is_request = is_request
        return self

    def set_brightness(self,
                       parameters: int,
                       is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('set_brightness')
        if not 0 <= parameters <= 15:
            raise ValueError('Brightness value must be between 0 and 15')
        self.parameters = parameters
        self.is_request = is_request
        return self

    def clear_playlist(self, is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('clear_playlist')
        self.is_request = is_request
        return self

    def pause_playlist(self, is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('pause_playlist')
        self.is_request = is_request
        return self

    def resume_playlist(self, is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('resume_playlist')
        self.is_request = is_request
        return self

    def select_in_playlist(self,
                           parameters: int,
                           is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('select_in_playlist')
        if not parameters >= 0:
            raise ValueError('Video # value must be more than 0')
        self.parameters = parameters
        self.is_request = is_request
        return self

    def save_playlist(self, is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('save_playlist')
        self.is_request = is_request
        return self

    def set_angle(self,
                  parameters: int,
                  is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('set_angle')
        if not 0 <= parameters <= 30:
            raise ValueError('Angle value must be between 0 and 30')
        self.parameters = parameters
        self.is_request = is_request
        return self

    def offset_x(self,
                 parameters: int,
                 is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('offset_x')
        if not -128 <= parameters <= 127:
            raise ValueError('Offset value must be between -128 and 127')
        # -128 must be 0x00, 0 must be 0x80, 127 must be 0xff
        # so we should add 128 (0x80)
        parameters += 128
        self.parameters = parameters
        self.is_request = is_request
        return self

    def set_mask(self,
                 parameters: int,
                 is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('set_mask')
        if parameters not in (0, 1, 2, 3):
            raise ValueError('Mask type must be 0, 1, 2 or 3')
        self.parameters = parameters
        self.is_request = is_request
        return self

    def set_bg_color(self,
                     parameters: int,
                     is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('set_bg_color')
        if parameters not in (0, 1):
            raise ValueError('Bg color must be 0 or 1')
        self.parameters = parameters
        self.is_request = is_request
        return self

    def inner_diameter(self,
                       parameters: int,
                       is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('set_angle')
        if not 0 <= parameters <= 255:
            raise ValueError('Inner diameter value must be between 0 and 255')
        self.parameters = parameters
        self.is_request = is_request
        return self

    def reset_settings(self, is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('reset_settings')
        self.is_request = is_request
        return self

    def change_playlist(self,
                        parameters: int,
                        is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('select_in_playlist')
        if not parameters >= 0:
            raise ValueError('Playlist # must be more than 0')
        self.parameters = parameters
        self.is_request = is_request
        return self

    def set_play_interval(self,
                          parameters: float,
                          is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('set_play_interval')
        if not 0 <= parameters <= 255:
            raise ValueError('Play interval value must be between 0 and 255')
        # 0.5 сек = 0x00, 2.0 сек = 0x03, 9.5 сек = 0x24
        parameters = round(parameters * 2 - 1)
        self.parameters = parameters
        self.is_request = is_request
        return self

    def set_rotation_speed(self,
                           parameters: int,
                           is_request: bool = True) -> "Command":
        self.op_code = Command.get_op_code('set_rotation_speed')
        if parameters not in (0, 1, 2):
            raise ValueError('Speed type must be 0, 1 or 2')
        self.parameters = parameters
        self.is_request = is_request
        return self
