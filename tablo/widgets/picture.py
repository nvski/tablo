import typing as tp
import PIL.Image as Image


from ..base import Widget


class Picture_W(Widget):
    def __init__(self, *args,
                 img_gen: tp.Optional[tp.Callable[[], Image.Image]]=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._img_gen = img_gen

    async def img_gen(self):
        if isinstance(self._img_gen, tp.Callable):
            return self._img_gen()
        else:
            return Image.new("RGB", self.size, "white")

    async def update_frame(self):
        img = await self.img_gen()
        if self.alpha and img.mode=='RGBA':
            mask=img
        else:
            mask=None
        self.image.paste(img, mask=mask)