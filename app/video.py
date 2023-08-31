import binascii
import logging
import os
from subprocess import check_output


# creating log file
log_file = os.path.join('..', 'video.log')
if not os.path.isfile(log_file) or \
        os.path.getsize(log_file) > 5120:
    open(log_file, 'w').close()
fh = logging.FileHandler(log_file, mode="a")
ftm = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(ftm)
logger = logging.getLogger('video')
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)

if os.sep == '/':  # unix-like:
    FFMPEG = '../ffmpeg/bin/ffmpeg'
    FFPROBE = '../ffmpeg/bin/ffprobe'
else:  # dos-like:
    FFMPEG = '..\\ffmpeg\\bin\\ffmpeg.exe'
    FFPROBE = '..\\ffmpeg\\bin\\ffprobe.exe'


class Video():
    def __init__(self, path: str) -> None:
        """Constructor for video file. Calculates various file info.

        Args:
            path (str): video file path
        """
        self.path = path
        self.folder = os.path.dirname(self.path)
        self.name = os.path.basename(self.path)
        logger.debug(f'{self.path = }')
        logger.debug(f'{self.folder = }')
        logger.debug(f'{self.name = }')

        if not os.path.isfile(self.path):
            print(f'File {self.path} not exists!')
            logger.warning(f'File {self.path} not exists!')
            open(path, 'a').close()  # create file

        self._packet = b''

        get_fps_command = (f'{FFPROBE} -v quiet -i {self.path} '
                           f'-show_entries stream=r_frame_rate -of csv=p=0')
        logger.debug(get_fps_command)
        self._fps = round(float(check_output(
            get_fps_command
        ).decode().split('/')[0]))
        logger.info(f'FPS: {self._fps}')

        self._file_size = os.path.getsize(self.path)
        logger.info(f'File size: {self._file_size}')

        self._name_len = len(self.name)
        logger.debug(f'File name length: {self._name_len}')

    def __str__(self):
        """Returns string representation of class.

        Usage:
            str(video_file)
            f'{video_file}'
        """
        result = f'{self.name}, {self._fps} FPS, '
        if self._file_size / 2**20 < 0.1:  # less than 0.1 MiB
            result += f'{self._file_size / 2**10:.2} kiB'
        else:
            result += f'{self._file_size / 2**20:.2} MiB'

    def encode(self):
        """Encodes video file using a preset FFMPEG command."""
        command = (
            f'{FFMPEG} -v quiet -y -i {self.path}'
            f'-c:v libx264 -sc_threshold 0 '
            f'-x264-params cabac=0:ref=1:mixed_ref=0:8x8dct=0:'
            f'threads=6:lookahead_threads=1:bframes=0:weightp=0:rc=cbr:'
            f'bitrate=1000:ratetol=1.0:vbv_maxrate=1000:vbv_bufsize=2000:'
            f'nal_hrd=none:filler=0 {self.path}'
        )
        os.system(command)

    def get_data(self) -> bytes:
        """Create raw data (`self._packet`) for further sending.

        Returns:
            bytes: raw packet data
        """
        self.encode()
        # create file header
        self._packet = binascii.unhexlify(f'{int(self._file_size):0>20x}')
        self._packet += binascii.unhexlify(b'0000000000')
        self._packet += binascii.unhexlify(f'{self._name_len:02x}')
        self._packet += self.name.encode('ascii', 'backslashreplace')
        with open(self.path, 'rb') as file:
            self._packet += file.read()
        return self._packet
