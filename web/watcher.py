"""Watchdog-based file watcher for auto-adding new video files to Excel."""

import os
import threading
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from web.shared import _load_config, get_excel, invalidate_excel_cache

VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.wmv', '.mov', '.flv', '.ts', '.m2ts', '.iso', '.rmvb'}


class _VideoHandler(FileSystemEventHandler):
    """Handles new video file events in the watched directory."""

    def __init__(self, watcher):
        self._watcher = watcher

    def on_created(self, event):
        if event.is_directory:
            return
        ext = os.path.splitext(event.src_path)[1].lower()
        if ext not in VIDEO_EXTENSIONS:
            return
        self._watcher._handle_new_file(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        ext = os.path.splitext(event.dest_path)[1].lower()
        if ext not in VIDEO_EXTENSIONS:
            return
        self._watcher._handle_new_file(event.dest_path)


class FileWatcher:
    """Background watchdog that monitors download_dir for new video files."""

    def __init__(self):
        self._observer: Observer | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._last_event = ''
        self._files_added = 0
        self._lock = threading.Lock()

    def start(self):
        config = _load_config()
        download_dir = config.get('path_config', {}).get('download_dir', '')
        if not download_dir or not os.path.isdir(download_dir):
            return

        self._observer = Observer()
        self._observer.schedule(_VideoHandler(self), download_dir, recursive=True)
        self._thread = threading.Thread(target=self._observer.start, daemon=True)
        self._thread.start()
        self._running = True

    def stop(self):
        if self._observer:
            self._observer.stop()
        self._running = False

    def _handle_new_file(self, file_path: str):
        try:
            time.sleep(1)  # wait for file to finish writing
            excel = get_excel()
            invalidate_excel_cache()
            excel.add_or_update_movie(file_path)
            excel.save()
            invalidate_excel_cache()  # refresh cache after save
            with self._lock:
                self._files_added += 1
                self._last_event = f'Added {os.path.basename(file_path)}'
            from web.server_state import get_state
            get_state().invalidate()
        except Exception as e:
            with self._lock:
                self._last_event = f'Error on {os.path.basename(file_path)}: {e}'

    @property
    def running(self) -> bool:
        return self._running

    @property
    def last_event(self) -> str:
        with self._lock:
            return self._last_event

    @property
    def files_added(self) -> int:
        with self._lock:
            return self._files_added


# Module-level singleton
_watcher = FileWatcher()


def get_watcher() -> FileWatcher:
    return _watcher
