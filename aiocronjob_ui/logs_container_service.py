import datetime
import json

import flet as ft


class LogsContainerService:
    __container = ft.Column([], scroll=ft.ScrollMode.ADAPTIVE)

    @classmethod
    def append_log(cls, log_entry: str):
        fmt_log, color = LogsContainerService.format_log_entry(log_entry)
        cls.__container.controls.append(ft.Text(fmt_log, color=color))
        cls.__container.update()

    @staticmethod
    def format_log_entry(log_entry: str) -> tuple[str, str]:
        log_as_dict = json.loads(log_entry)
        log_datetime = datetime.datetime.fromtimestamp(
            log_as_dict["timestamp"]
        ).replace(microsecond=0)

        match log_as_dict["event_type"]:
            case "job_failed":
                color = ft.colors.RED
            case "job_finished":
                color = ft.colors.GREEN
            case _:
                color = ft.colors.BLACK

        return (
            f"{log_datetime.isoformat()} "
            f"{log_as_dict['job_name']} -> {log_as_dict['event_type']}",
            color,
        )

    @classmethod
    def get_container(cls):
        return cls.__container
