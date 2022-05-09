import typing as tp
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions


class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            self = cls._instance = object.__new__(cls)
            self.__init__(*args, **kwargs)
        return cls._instance


class Tablo(Singleton):
    def __init__(self,
            # root_widget:Widget,
            brightness:int=40,
            matrix:bool=True, bs=None) -> None:
        options = RGBMatrixOptions()
        options.drop_privileges = False
        options.rows = 64
        options.cols = 128
        options.chain_length = 2
        options.led_rgb_sequence = 'RBG'
        options.panel_type = 'FM6126A'
        options.hardware_mapping = 'regular'
        options.gpio_slowdown = 2
        options.pwm_bits = 14
        options.pwm_dither_bits = 1
        options.pwm_lsb_nanoseconds = 50
        # options.scan_mode = 1

        self.image = Image.new('RGB', (options.cols*options.chain_length, options.rows), 'black')

        self.has_matrix = matrix
        self.matrix = None
        self.options = options
        if self.has_matrix:
            self.start_matrix(options, brightness)
        # match bs:
        #     case False:
        #         self.bs = None
        #         self.has_bs = False
        #     case None:
        #         self.bs = BrightnessScheduler()
        #         self.has_bs = True
        #     case _:
        #         self.bs = bs
        #         self.has_bs = True
        
        # self.root_widget = root_widget

    def start_matrix(self, options=None, brightness=30):
        if options is None:
            options = self.options
        if self.matrix is not None:
            del self.matrix
            # time.sleep(.5)
        self.matrix = RGBMatrix(options=options)
        self.matrix.brightness = brightness
        self.update()

    def update(self, brightness: tp.Optional[int] = None) -> None:
        if brightness is not None:
            self.matrix.brightness = brightness
        self.matrix.SetImage(self.image)

    def clear(self) -> None:
        self.image = Image.new('RGB', (128, 64), 'black')
        self.update()
