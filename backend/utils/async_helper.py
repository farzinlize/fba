import asyncio
import atexit
import threading
import weakref

from collections.abc import Awaitable, Callable, Coroutine
from functools import wraps
from typing import Any, TypeVar

T = TypeVar('T')


class _TaskRunner:
    """Task runner executing an asyncio event loop in a background thread"""

    def __init__(self) -> None:
        self.__loop: asyncio.AbstractEventLoop | None = None
        self.__thread: threading.Thread | None = None
        self.__lock = threading.Lock()
        atexit.register(self.close)

    def close(self) -> None:
        """Close the event loop and clean up"""
        with self.__lock:
            if self.__loop:
                self.__loop.call_soon_threadsafe(self.__loop.stop)
            if self.__thread and self.__thread.is_alive():
                self.__thread.join()
            self.__loop = None
            self.__thread = None
            name = f'TaskRunner-{threading.get_ident()}'
            _runner_map.pop(name, None)

    def _target(self) -> None:
        """Target function for the background thread"""
        try:
            self.__loop.run_forever()
        finally:
            self.__loop.close()

    def run(self, coro: Awaitable[T]) -> T:
        """Run a coroutine on the background event loop and return its result"""
        with self.__lock:
            name = f'TaskRunner-{threading.get_ident()}'
            if self.__loop is None:
                self.__loop = asyncio.new_event_loop()
                self.__thread = threading.Thread(target=self._target, daemon=True, name=name)
                self.__thread.start()
            future = asyncio.run_coroutine_threadsafe(coro, self.__loop)
            return future.result()


_runner_map = weakref.WeakValueDictionary()


def run_await(coro: Callable[..., Awaitable[T]] | Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., T]:
    """Wrap a coroutine in a function that waits for it to complete"""

    @wraps(coro)
    def wrapped(*args, **kwargs):  # ruff:ignore[missing-return-type-private-function]
        inner = coro(*args, **kwargs)
        if not asyncio.iscoroutine(inner) and not asyncio.isfuture(inner):
            raise TypeError(f'Expected coroutine or future, got {type(inner)}')

        try:
            # Use task submission if the event loop is running
            asyncio.get_running_loop()
            name = f'TaskRunner-{threading.get_ident()}'
            if name not in _runner_map:
                _runner_map[name] = _TaskRunner()
            return _runner_map[name].run(inner)
        except RuntimeError:
            # Otherwise create a new event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(inner)

    wrapped.__doc__ = coro.__doc__
    return wrapped
