import asyncio
import time
import typing as tp
from PIL import Image, ImageDraw


from .. import Tablo


tablo = Tablo()


Widget = tp.TypeVar('Widget')


class Widget:
    running_set: tp.Set[Widget] = set()

    @staticmethod
    async def stop_all():
        for w in Widget.running_set.copy():
            await w.stop()

    def __init__(self, size: tp.Tuple[int, int], position=(0, 0), *, rr:float=5, alpha=False):
        self.w, self.h = self.size = size
        self.x, self.y = self.position = position
        self.rr = rr
        self.task: tp.Optional[asyncio.Task] = None

        self.alpha = alpha
        if alpha:
            self.image = Image.new("RGBA", self.size, '#00000000')
        else:
            self.image = Image.new("RGB", self.size, '#000000')
        self.draw = ImageDraw.Draw(self.image)

    async def clear(self) -> None:
        self.draw.rectangle((0, 0)+self.size, fill='#000000')
        # self.place()

    async def _place(self) -> None:
        if self.alpha:
            mask = self.image
        else:
            mask = None
        tablo.image.paste(self.image, box=self.position, mask=mask)
        tablo.update()

    async def update_frame(self):
        pass
        # to be defined in subclasses individually

    async def run(self) -> None:
        if self in Widget.running_set:
            raise Warning(
                "Trying to start smth already running. Nothing is done.")
            return
        Widget.running_set.add(self)
        while self in Widget.running_set:
            await self.update_frame()
            await self._place()
            await asyncio.sleep(self.rr - time.time() % self.rr)

    def start(self) -> None:
        self.task = asyncio.create_task(self.run(), name=self.__class__.__name__)

    def stop(self) -> None:
        Widget.running_set.remove(self)
