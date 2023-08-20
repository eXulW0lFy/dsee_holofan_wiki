import binascii
import logging
import os
from subprocess import check_output


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
        self.path = path
        logger.debug(f'{self.path = }')
        self.folder = os.path.dirname(self.path)
        logger.debug(f'{self.folder = }')
        self.name = os.path.basename(self.path)
        logger.debug(f'{self.name = }')

        if not os.path.isfile(self.path):
            print(f'File {self.path} not exists!')
            open(path, 'a').close()  # create file

        self._packet = b''

        command = (f'{FFPROBE} -v quiet -i {self.folder + os.sep + self.name} '
                   f'-show_entries stream=r_frame_rate -of csv=p=0')
        logger.info(command)

        self._fps = round(float(check_output(
            f'{FFPROBE} -v quiet -i {self.folder + os.sep + self.name} '
            f'-show_entries stream=r_frame_rate -of csv=p=0'.split()
        ).decode().split('/')[0]))

        self._file_len = os.path.getsize(self.path)

        self._name_len = len(self.name)

    def encode(self):
        command = (
            f'{FFMPEG} -v quiet -y -i {self.path}'
            f'-c:v libx264 -sc_threshold 0 '
            f'-x264-params cabac=0:ref=1:mixed_ref=0:8x8dct=0:'
            f'threads=6:lookahead_threads=1:bframes=0:weightp=0:rc=cbr:'
            f'bitrate=1000:ratetol=1.0:vbv_maxrate=1000:vbv_bufsize=2000:'
            f'nal_hrd=none:filler=0 {self.path}'
        )
        os.system(command)

    def get_data(self):
        self.encode()
        # create file header
        self._packet = binascii.unhexlify(f'{int(self._file_len):0>20x}')
        self._packet += binascii.unhexlify(b'0000000000')
        self._packet += binascii.unhexlify(f'{self._name_len:02x}')
        self._packet += self.name.encode('ascii', 'backslashreplace')
        with open(self.path, 'rb') as file:
            self._packet += file.read()
        return self._packet
