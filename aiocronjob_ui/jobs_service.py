import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Protocol, Literal

import httpx


class Subscriber(Protocol):
    def __call__(self, jobs: list[dict] = None, exc: Exception = None) -> None:
        ...


API_URL = "http://localhost:8000/api"


class LogsService:
    __subscribers = set()

    @classmethod
    def subscribe(cls, subscriber: Subscriber):
        cls.__subscribers.add(subscriber)

    @classmethod
    def unsubscribe(cls, subscriber: Subscriber):
        cls.__subscribers.remove(subscriber)

    @classmethod
    def _notify_all(cls, log):
        for subscriber in cls.__subscribers:
            subscriber(log)

    @classmethod
    def fetch_logs(cls):
        with httpx.stream("GET", f"{API_URL}/log-stream") as r:
            for line in r.iter_lines():
                if cls.__subscribers:
                    cls._notify_all(line)
                else:
                    break


class JobsService:
    _lock = threading.Lock()

    def __init__(self):
        self._is_loading: bool = True
        self._jobs: Optional[list[dict]] = None
        self._exc: Optional[Exception] = None
        self._subscribers: set[Subscriber] = set()
        self._fetch_jobs()

    def subscribe(self, subscriber: Subscriber):
        self._subscribers.add(subscriber)
        if not self._is_loading:
            self.notify(subscriber)

    def unsubscribe(self, subscriber: Subscriber):
        self._subscribers.remove(subscriber)

    def notify(self, subscriber: Subscriber):
        subscriber(jobs=self._jobs, exc=self._exc)

    def notify_all(self):
        with ThreadPoolExecutor(max_workers=20) as executor:
            for subscriber in self._subscribers:
                executor.submit(self.notify, subscriber)

    @property
    def is_loading(self):
        return self._is_loading

    def refresh(self):
        # drop a new operation if there is one in progress
        if not self._is_loading:
            self._fetch_jobs()

    def do_job_action(self, job_name: str, action: Literal["cancel", "start"]):
        with httpx.Client() as client:
            try:
                response = client.get(f"{API_URL}/jobs/{job_name}/{action}")
                response.raise_for_status()
            except Exception as e:
                self._exc = e
                return
        self._fetch_jobs()

    def consume_logs(self, consumer):
        LogsService.subscribe(consumer)
        threading.Thread(target=LogsService.fetch_logs).start()

    def _fetch_jobs(self) -> None:
        self._lock.acquire()

        self._is_loading = True

        try:
            with httpx.Client() as client:
                try:
                    response = client.get(f"{API_URL}/jobs")
                    response.raise_for_status()
                    self._jobs = response.json()
                except Exception as e:
                    self._exc = e
                    return
        finally:
            self._is_loading = False
            self._lock.release()
            self.notify_all()


jobs_service = JobsService()
