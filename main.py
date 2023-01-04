import flet as ft

from aiocronjob_ui.bottom_sheet_service import BottomSheetService
from aiocronjob_ui.controls.jobs_control import JobsControl
from aiocronjob_ui.jobs_service import jobs_service
from aiocronjob_ui.logs_container_service import LogsContainerService


def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.LIGHT
    page.overlay.append(BottomSheetService.get_bs())
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.icons.REFRESH,
        on_click=lambda e: jobs_service.refresh(),
        bgcolor=ft.colors.GREEN,
        mini=True,
        shape=ft.StadiumBorder(),
    )
    page.add(
        ft.Container(
            ft.Tabs(
                selected_index=0,
                expand=1,
                tabs=[
                    ft.Tab(
                        text="All",
                        content=ft.Container(
                            content=JobsControl(
                                filter_="all", jobs_service=jobs_service
                            ),
                            alignment=ft.alignment.center,
                        ),
                    ),
                    ft.Tab(
                        text="Running",
                        content=ft.Container(
                            content=JobsControl(
                                filter_="running", jobs_service=jobs_service
                            ),
                            alignment=ft.alignment.center,
                        ),
                    ),
                    ft.Tab(
                        text="Failed",
                        content=ft.Container(
                            content=JobsControl(
                                filter_="failed", jobs_service=jobs_service
                            ),
                            alignment=ft.alignment.center,
                        ),
                    ),
                    ft.Tab(
                        text="Logs",
                        icon=ft.icons.TERMINAL,
                        content=LogsContainerService.get_container(),
                    ),
                ],
            ),
            expand=True,
        )
    )
    jobs_service.consume_logs(LogsContainerService.append_log)


ft.app(target=main)
