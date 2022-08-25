import typing as tp
import PIL.Image as Image


from ..base import Widget


class Picture_W(Widget):
    def __init__(self, *args,
                 img_gen: tp.Optional[tp.Callable[[], Image.Image]]=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._img_gen = img_gen

    async def img_generator(self) -> tp.AsyncIterable[Image.Image]:
        if self._img_gen is not None:
            while True: yield self._img_gen()
        else:
            while True: yield Image.new("RGB", self.size, "white")

    async def image_generator(self):
        async for img in self.img_generator():
            if self.alpha and img.mode=='RGBA':
                mask=img
            else:
                mask=None
            if img is not None: self.image.paste(img, mask=mask)
            yield self.image