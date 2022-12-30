import flet as ft


class FlutterLikeUserControl(ft.UserControl):
    def __init__(self):
        super().__init__()
        self._main_control = ft.Container(self.render(), expand=True)

    def render(self):
        raise NotImplementedError

    def update(self):
        self._main_control.content = self.render()
        super().update()

    def build(self):
        return self._main_control
