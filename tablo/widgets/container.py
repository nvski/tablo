import asyncio
import typing as tp
import logging

# import aiostream.stream as stream
from ..base import Layout, Widget


class Container_W(Widget):
    def __init__(self, size: tp.Tuple[int, int], /, layout:Layout, *, alpha=True):
        super().__init__(size, alpha=alpha)
        self.layout = layout

        if any(node.refresh_rate for node in layout.nodes()):
            logging.warn("Layout nodes' refresh rates are ignored in `Container_W`")

    async def image_generator(self):
        positions = [node.position for node in self.layout.nodes()]
        image_generators = [node.obj.image_generator() for node in self.layout.nodes()]


        async def azip(*async_iterables: tp.AsyncIterable):
            async_iterators = [a_it.__aiter__() for a_it in async_iterables]
            try:
                while True:
                    futures = [it.__anext__() for it in async_iterators]
                    results = await asyncio.gather(*futures)
                    yield results
            except StopAsyncIteration:
                pass


        async for images in azip(*image_generators):
            self.clear()
            for pos, im in zip(positions, images):
                if im.mode == "RGBA":
                    self.image.paste(im, mask=im, box=pos)
                else:
                    self.image.paste(im, box=pos)

            yield self.image
