import flet as ft


class BottomSheetService:
    __bottom_sheet = ft.BottomSheet(open=False)

    @classmethod
    def get_bs(cls):
        return cls.__bottom_sheet

    @classmethod
    def set_content(cls, content: ft.Control) -> None:
        cls.__bottom_sheet.content = content
        cls.__bottom_sheet.update()

    @classmethod
    def open(cls):
        cls.__bottom_sheet.open = True
        cls.__bottom_sheet.update()

    @classmethod
    def close(cls):
        cls.__bottom_sheet.open = False
        cls.__bottom_sheet.update()
