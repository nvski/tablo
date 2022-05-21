import PIL.ImageFont as ImageFont
import typing as tp

from ..base import Widget


DEFAULT_FONT = 'fonts/OCRAStd.otf'


class Text_W(Widget):
    def __init__(self, size,
                 text_gen = None,
                 font_name: str = DEFAULT_FONT, font_color:str="#ffffff",
                 move:tp.Tuple[int,int]=(0,0),
                 alpha=False
                 ) -> None:
        super().__init__(size, alpha=alpha)
        self._text_gen = text_gen
        self.font_obj = ImageFont.truetype(font_name, self.h-2)
        self.font_color = font_color
        self.move = move

    async def text_gen(self):
        if isinstance(self._text_gen, tp.Callable):
            return self._text_gen()
        else:
            return 'text'

    async def update_frame(self) -> None:
        self.clear()
        text = await self.text_gen()
        if text is not None:
            self.draw.multiline_text(
                self.move, text, fill=self.font_color, font=self.font_obj)

