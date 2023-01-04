import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Protocol, Literal

import httpx
from .config import Settings


class Subscriber(Protocol):
    def __call__(self, jobs: list[dict] = None, exc: Exception = None) -> None:
        ...


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
        logging.debug("Notified %d subscribers", len(cls.__subscribers))

    @classmethod
    def fetch_logs(cls):
        with httpx.stream("GET", f"{Settings.api_url}/log-stream") as r:
            logging.debug("A log stream was started.")
            for line in r.iter_lines():
                if cls.__subscribers:
                    cls._notify_all(line)
                else:
                    break
        logging.debug("The log stream has ended.")


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
            logging.debug("Refreshing jobs...")
            self._fetch_jobs()
        else:
            logging.debug("Cannot refresh jobs as the service is already loading.")

    def do_job_action(self, job_name: str, action: Literal["cancel", "start"]):
        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(f"{Settings.api_url}/jobs/{job_name}/{action}")
                response.raise_for_status()
        except Exception as e:
            logging.error("Exception in do_job_action: %s", e)
            self._exc = e
            return
        self._fetch_jobs()

    @staticmethod
    def consume_logs(consumer):
        LogsService.subscribe(consumer)
        threading.Thread(target=LogsService.fetch_logs).start()

    def _fetch_jobs(self) -> None:
        self._lock.acquire()

        self._is_loading = True

        try:
            with httpx.Client(timeout=2) as client:
                response = client.get(f"{Settings.api_url}/jobs")
                response.raise_for_status()
                self._jobs = response.json()
        except Exception as e:
            logging.error("Exception in _fetch_jobs: %s", e)
            self._exc = e
            return
        finally:
            self._is_loading = False
            self._lock.release()
            self.notify_all()


jobs_service = JobsService()
