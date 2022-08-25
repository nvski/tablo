import PIL.ImageFont as ImageFont
import PIL.Image as Image
import typing as tp

from ..base import Widget


DEFAULT_FONT = 'fonts/OCRAStd.otf'


class Text_W(Widget):
    def __init__(self, size,
                 text_func: tp.Optional[tp.Callable[[],str]] = None,
                 text:tp.Optional[str] = None,
                 text_iterable: tp.Optional[tp.Iterable[str]] = None,
                 font_name: str = DEFAULT_FONT, font_color:str="#ffffff",
                 move:tp.Tuple[int,int]=(0,0),
                 alpha=False
                 ) -> None:
        super().__init__(size, alpha=alpha)
        self._text_func = text_func
        self._text = text
        self._text_iterable = text_iterable
        self.font_obj = ImageFont.truetype(font_name, self.h-2)
        self.font_color = font_color
        self.move = move

    async def text_generator(self) -> tp.AsyncIterable[str]:
        if self._text_iterable is not None:
            for text in self._text_iterable:
                yield text
        elif self._text_func is not None:
            while True: yield self._text_func()
        elif self._text is not None:
            while True: yield self._text
        else:
            while True: yield "text"

    async def image_generator(self) -> tp.AsyncIterable[Image.Image]:
        async for text in self.text_generator():
            self.clear()
            if text is not None:
                self.draw.multiline_text(
                    self.move, text, fill=self.font_color, font=self.font_obj
                )
            yield self.image
    


