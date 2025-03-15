import asyncio
import datetime
import logging
import time
import typing as tp
from dataclasses import dataclass, field, replace
from PIL import Image, ImageDraw
import aiohttp
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from .brightness import BrightnessScheduler


logging.basicConfig(level=logging.INFO)
T = tp.TypeVar("T", "Widget", "Layout")


class Widget:
    def __init__(self, size: tp.Tuple[int, int], /, *, alpha=False):
        self.w, self.h = self.size = size

        self.alpha = alpha
        if alpha:
            self.image = Image.new("RGBA", self.size, '#00000000')
        else:
            self.image = Image.new("RGB", self.size, '#000000')
        self.draw = ImageDraw.Draw(self.image)

    def clear(self) -> None:
        self.draw.rectangle((0, 0)+self.size, fill='#000000')

    async def image_generator(self) -> tp.AsyncIterable[Image.Image]:
        while True:
            await self.update_frame()
            yield self.image

    async def update_frame(self) -> Image.Image:
        "Should not be called directly"
        raise NotImplementedError(f"One of `image_generator` "
                   f"or `update_image` should be implemented, but "
                   f"they are not in {type(self)}")


@dataclass
class Node(tp.Generic[T]):
    obj: T
    position: tp.Tuple[int, int] = (0,0)
    refresh_rate: tp.Optional[float] = None


@dataclass
class Layout:
    layout: tp.Sequence[Node[tp.Any]] = field(default_factory=list)

    def nodes(self, anchor_pos: tp.Tuple[int,int]=(0,0)) -> tp.Iterator[Node[Widget]]:
        for node in self.layout:
            x, y = node.position
            node = replace(node, position=(x+anchor_pos[0], y+anchor_pos[1]))
            if isinstance(node.obj, Layout):
                yield from node.obj.nodes(anchor_pos=node.position)
            else:
                yield node
    
    def flatten(self) -> "tp.List[Node[Widget]]":
        return list(self.nodes((0,0)))


# class Singleton(object):
#     _instance = None
#     def __new__(cls, *args, **kwargs):
#         if cls._instance is None:
#             self = cls._instance = object.__new__(cls)
#             self.__init__(*args, **kwargs)
#         return cls._instance

# class Tablo(Singleton):
class Tablo():
    def __init__(self, initial_brightness:int=40) -> None:
        options = RGBMatrixOptions()
        options.drop_privileges = False
        options.rows = 64
        options.cols = 128
        options.chain_length = 1
        options.led_rgb_sequence = 'RBG'
        options.panel_type = 'FM6126A'
        options.hardware_mapping = 'regular'
        options.gpio_slowdown = 2
        options.pwm_bits = 14  # needs recompiling with `kBitPlanes = 14; kDefaultBitPlanes = 14;` in framebuffer-internal.h
        options.pwm_dither_bits = 1
        options.pwm_lsb_nanoseconds = 50
        # options.scan_mode = 1

        self.image = Image.new('RGB', (options.cols*options.chain_length, options.rows), 'black')
        self.matrix: RGBMatrix = None
        self.options = options
        self.init_matrix(initial_brightness)

    def init_matrix(self, brightness=30):
        if self.matrix is not None:
            del self.matrix
            time.sleep(.1)

        self.matrix = RGBMatrix(options=self.options)
        self.matrix.brightness = brightness
        self.update()

    def update(self, brightness: tp.Optional[int] = None) -> None:
        if brightness is not None:
            self.matrix.brightness = brightness
        self.matrix.SetImage(self.image)

    def clear(self) -> None:
        self.image = Image.new('RGB', (128, 64), 'black')
        self.update()

    async def run(self, layout: Layout, brightness_scheduler:tp.Optional[BrightnessScheduler]=None) -> tp.NoReturn:
        tasks = [self.run_node(node) for node in layout.nodes()]
        if brightness_scheduler is not None:
            tasks.append(self.run_brightness_scheduler(brightness_scheduler))
        returns = await asyncio.gather(*tasks)
        raise RuntimeError(f"All tasks finished unexpectedly:\n{returns}")

    async def run_node(self, node:Node[Widget]) -> tp.NoReturn:
        async for image in node.obj.image_generator():
            if node.obj.alpha:
                mask = image
            else:
                mask = None
            self.image.paste(image, box=node.position, mask=mask)
            self.update()
            assert isinstance(node.refresh_rate, (int, float)), f"refresh rate is {type(node.refresh_rate)}, should be numerical"
            assert node.refresh_rate > 0
            await asyncio.sleep(node.refresh_rate - time.time() % node.refresh_rate)
        raise RuntimeError(f"Infinite generator ended in {node}")

    async def run_brightness_scheduler(self, brightness_scheduler:BrightnessScheduler) -> tp.NoReturn:
        async for new_brightness in brightness_scheduler.brightness_generator():
            self.update(new_brightness)
            await asyncio.sleep(brightness_scheduler.refresh_rate - time.time() % brightness_scheduler.refresh_rate)
        raise RuntimeError("Infinite generator ended")

Data_T = tp.TypeVar("Data_T")
class BaseDataProvider(tp.Generic[Data_T]):
    data: tp.Optional[Data_T]
    def __init__(self, session:tp.Optional[aiohttp.ClientSession]=None):
        self.session = session
        self.timeout = datetime.timedelta(minutes=2)
        self.data = None


    @property
    def last_update(self) -> tp.Optional[datetime.datetime]:
        raise NotImplementedError
    
    def _timed_out(self):
        return self.last_update is None or \
            datetime.datetime.now().astimezone() > self.last_update + self.timeout

    async def update_data(self) -> None:
        raise NotImplementedError()

    async def data_generator(self) -> tp.AsyncIterable[tp.Optional[Data_T]]:
        while True:
            if self._timed_out():
                await self.update_data()
            yield self.data
   
