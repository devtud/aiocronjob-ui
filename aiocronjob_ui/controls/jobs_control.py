from typing import Literal, Optional

import flet as ft
from aiocronjob_ui.bottom_sheet_service import BottomSheetService
from aiocronjob_ui.jobs_service import JobsService
from .generic_control import FlutterLikeUserControl


class JobsControl(FlutterLikeUserControl):
    def __init__(
        self, filter_: Literal["all", "running", "failed"], jobs_service: JobsService
    ):
        self._filter = filter_
        self._jobs: Optional[list[dict]] = None
        self._exc: Optional[Exception] = None
        self._jobs_service = jobs_service

        super().__init__()

    def _on_jobs_fetched(self, jobs=None, exc=None):
        self._jobs = jobs
        self._exc = exc
        self.update()

    def did_mount(self):
        self._jobs_service.subscribe(self._on_jobs_fetched)

    def will_unmount(self):
        self._jobs_service.unsubscribe(self._on_jobs_fetched)

    def _open_bottom_sheet(self, event: ft.ControlEvent):
        job = event.control.data
        if job["status"] == "running":

            def on_click(event: ft.ControlEvent):
                job_ = event.control.data
                BottomSheetService.close()
                self._jobs_service.do_job_action(job_["definition"]["name"], "cancel")

            action_button = ft.ElevatedButton("Stop job", on_click=on_click, data=job)
        else:

            def on_click(event: ft.ControlEvent):
                job_ = event.control.data
                BottomSheetService.close()
                self._jobs_service.do_job_action(job_["definition"]["name"], "start")

            action_button = ft.ElevatedButton("Start job", on_click=on_click, data=job)

        BottomSheetService.set_content(
            ft.Container(
                ft.Column(
                    [
                        ft.Text(job["definition"]["name"]),
                        action_button,
                        ft.Divider(height=9, thickness=3),
                        ft.TextButton(
                            "Cancel",
                            on_click=lambda e: BottomSheetService.close(),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
                padding=10,
            ),
        )
        BottomSheetService.open()

    def render(self):
        if not self._jobs and not self._exc:
            content = ft.ProgressRing()
        elif self._exc:
            content = ft.Text(f"Hopaaa {self._exc}")
        else:
            content = ft.Column(
                [
                    ft.ListTile(
                        title=ft.Text(job["definition"]["name"]),
                        trailing=ft.Text(job["status"]),
                        on_click=self._open_bottom_sheet,
                        data=job,
                    )
                    for job in self._jobs
                    if self._filter == "all" or self._filter == job["status"]
                ],
                expand=True,
            )
        return content
