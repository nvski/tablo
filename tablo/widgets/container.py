import typing as tp


from .base import Widget


class Container_W(Widget):
    def __init__(self, *args, widgets:tp.Sequence[Widget], alpha=True, **kwargs):
        kwargs['alpha'] = alpha
        super().__init__(*args, **kwargs)
        self.widgets = widgets
        assert all(w.rr == widgets[0].rr for w in widgets)
        self.rr = widgets[0].rr
        # container self.rr overwrites widgets' rr 

    async def update_frame(self):
        for w in self.widgets:
            await w.update_frame()
            im = w.image
            if im.mode == "RGBA":
                self.image.paste(im, mask=im, box=w.position)
            else:
                self.image.paste(im, box=w.position)
