import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Protocol, Literal

import httpx


class Subscriber(Protocol):
    def __call__(self, jobs: list[dict] = None, exc: Exception = None) -> None:
        ...


API_URL = "http://localhost:8000/api"


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

    def do_job_action(self, job_name: str, action: Literal['cancel', 'start']):
        with httpx.Client() as client:
            try:
                response = client.get(f"{API_URL}/jobs/{job_name}/{action}")
                response.raise_for_status()
            except Exception as e:
                self._exc = e
                return
        self._fetch_jobs()

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
