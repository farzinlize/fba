import time

from asyncio import Queue

from prometheus_client import Counter, Gauge, Histogram

from backend.core.conf import settings

_PROMETHEUS_QUEUE_SIZE_GAUGE = Gauge(
    name='fba_queue_size',
    documentation='Current length of the internal asynchronous queue',
    labelnames=['app_name', 'queue_name'],
)

_PROMETHEUS_QUEUE_BATCH_DEQUEUE_COST_TIME_HISTOGRAM = Histogram(
    name='fba_queue_batch_dequeue_cost_time',
    documentation='Internal asynchronous queue batch processing duration (ms)',
    labelnames=['app_name', 'queue_name'],
)

_PROMETHEUS_QUEUE_EXCEPTION_COUNTER = Counter(
    name='fba_queue_exception_total',
    documentation='Total internal asynchronous queue exceptions',
    labelnames=['app_name', 'queue_name'],
)


def observe_queue_size(queue: Queue, *, queue_name: str) -> None:
    """Record current queue length"""
    _PROMETHEUS_QUEUE_SIZE_GAUGE.labels(app_name=settings.GRAFANA_PROMETHEUS_APP_NAME, queue_name=queue_name).set(
        queue.qsize()
    )


def observe_batch_dequeue_cost(start_time: float, *, queue_name: str) -> None:
    """Record batch processing duration"""
    elapsed = round((time.perf_counter() - start_time) * 1000, 3)
    _PROMETHEUS_QUEUE_BATCH_DEQUEUE_COST_TIME_HISTOGRAM.labels(
        app_name=settings.GRAFANA_PROMETHEUS_APP_NAME, queue_name=queue_name
    ).observe(elapsed)


def inc_queue_exception(*, queue_name: str) -> None:
    """Record queue exception"""
    _PROMETHEUS_QUEUE_EXCEPTION_COUNTER.labels(
        app_name=settings.GRAFANA_PROMETHEUS_APP_NAME, queue_name=queue_name
    ).inc()
