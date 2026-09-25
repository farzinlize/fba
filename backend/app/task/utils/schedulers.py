from __future__ import annotations

import asyncio
import json
import math

from datetime import datetime, timedelta
from multiprocessing.util import Finalize
from typing import TYPE_CHECKING, Final

from celery import current_app, schedules
from celery.beat import ScheduleEntry, Scheduler
from celery.signals import beat_init
from celery.utils.log import get_logger
from sqlalchemy import select
from sqlalchemy.exc import DatabaseError, InterfaceError

from backend.app.task.enums import PeriodType, TaskSchedulerType
from backend.app.task.model.scheduler import TaskScheduler
from backend.app.task.schema.scheduler import CreateTaskSchedulerParam
from backend.app.task.utils.tzcrontab import TzAwareCrontab, crontab_verify
from backend.common.enums import StatusType
from backend.common.exception import errors
from backend.core.conf import settings
from backend.database.db import async_db_session
from backend.database.redis import redis_client
from backend.utils.async_helper import run_await
from backend.utils.serializers import select_as_dict
from backend.utils.timezone import timezone

if TYPE_CHECKING:
    from redis.asyncio.lock import Lock

# This scheduler must wake more often than the usual five minutes to account for external schedule changes
_DEFAULT_MAX_INTERVAL: Final = 5  # seconds

# Schedule lock duration to prevent duplicate creation
_DEFAULT_MAX_LOCK_TIMEOUT: Final = _DEFAULT_MAX_INTERVAL * 5  # seconds

logger = get_logger('fba.schedulers')


class ModelEntry(ScheduleEntry):
    """Task schedule entry"""

    def __init__(self, model: TaskScheduler, app=None) -> None:  # ruff:ignore[missing-type-function-argument, complex-structure]
        super().__init__(
            app=app or current_app._get_current_object(),
            name=model.name,
            task=model.task,
        )
        try:
            if (
                model.type == TaskSchedulerType.INTERVAL
                and model.interval_every is not None
                and model.interval_period is not None
            ):
                self.schedule = schedules.schedule(timedelta(**{model.interval_period: model.interval_every}))
            elif model.type == TaskSchedulerType.CRONTAB and model.crontab is not None:
                self.schedule = TzAwareCrontab.from_string(model.crontab)
            else:
                raise errors.NotFoundError(msg=f'Schedule for {self.name} is empty!')
            # logger.debug('Schedule: {}'.format(self.schedule))
        except Exception as e:
            logger.error(f'Disabling task {self.name} because its schedule is empty; details: {e}')
            asyncio.create_task(self._disable(model))

        try:
            self.args = json.loads(model.args) if model.args else None
            self.kwargs = json.loads(model.kwargs) if model.kwargs else None
        except ValueError as exc:
            logger.error(f'Disabling task {self.name} because its arguments are invalid; error: {exc!s}')
            asyncio.create_task(self._disable(model))

        self.options = {}
        for option in ['queue', 'exchange', 'routing_key']:
            value = getattr(model, option)
            if value is None:
                continue
            self.options[option] = value

        if model.expire_seconds is not None:
            self.options['expires'] = model.expire_seconds
        elif model.expire_time is not None:
            self.options['expires'] = timezone.from_datetime(model.expire_time)

        if not model.last_run_time:
            model.last_run_time = timezone.now()
            if model.start_time:
                model.last_run_time = timezone.from_datetime(model.start_time) - timedelta(days=365)

        self.last_run_at = timezone.from_datetime(model.last_run_time)
        self.options['periodic_task_name'] = model.name
        self.model = model
        self.enabled = model.status == StatusType.enable

    async def _disable(self, model: TaskScheduler) -> None:
        """Disable task"""
        model.no_changes = True
        self.model.status = model.status = StatusType.disable
        self.enabled = False
        async with async_db_session.begin() as db:
            stmt = select(TaskScheduler).where(TaskScheduler.id == model.id, TaskScheduler.deleted == 0)
            query = await db.execute(stmt)
            task = query.scalars().first()
            if task:
                task.no_changes = True
                task.status = StatusType.disable

    def is_due(self) -> tuple[bool, int | float | datetime]:
        """Task expiration status"""
        if self.model.status != StatusType.enable:
            # Delay five seconds when re-enabled
            return schedules.schedstate(is_due=False, next=5)

        # Run only after 'start_time'
        if self.model.start_time is not None:
            now = timezone.now()
            start_time = timezone.from_datetime(self.model.start_time)
            if now < start_time:
                delay = math.ceil((start_time - now).total_seconds())
                return schedules.schedstate(is_due=False, next=delay)

        # One-time task
        if self.model.one_off and self.model.status == StatusType.enable and self.model.total_run_count > 0:
            self.model.status = StatusType.disable
            self.model.total_run_count = 0
            self.model.no_changes = False
            save_fields = ('status',)
            run_await(self.save)(save_fields)
            return schedules.schedstate(is_due=False, next=1000000000)  # Long delay to avoid rechecking

        return self.schedule.is_due(self.last_run_at)

    def __next__(self):  # ruff:ignore[missing-return-type-special-method]
        self.model.last_run_time = timezone.now()
        self.model.total_run_count += 1
        self.model.no_changes = True
        return self.__class__(self.model)

    next = __next__

    async def save(self, fields: tuple = ()) -> None:
        """
        Save task state fields

        :param fields: Additional fields to save
        :return:
        """
        async with async_db_session.begin() as db:
            stmt = (
                select(TaskScheduler)
                .where(TaskScheduler.id == self.model.id, TaskScheduler.deleted == 0)
                .with_for_update()
            )
            query = await db.execute(stmt)
            task = query.scalars().first()
            if task:
                for field in ['last_run_time', 'total_run_count', 'no_changes']:
                    setattr(task, field, getattr(self.model, field))
                for field in fields:
                    setattr(task, field, getattr(self.model, field))
            else:
                logger.warning(f'Task {self.model.name} does not exist; skipping update')

    @classmethod
    async def from_entry(cls, name, app=None, **entry) -> ModelEntry:  # ruff:ignore[missing-type-function-argument]
        """Save or update local task schedule"""
        async with async_db_session.begin() as db:
            stmt = select(TaskScheduler).where(TaskScheduler.name == name, TaskScheduler.deleted == 0)
            query = await db.execute(stmt)
            task = query.scalars().first()
            temp = await cls._unpack_fields(name, **entry)
            if not task:
                task = TaskScheduler(**temp)
                db.add(task)
            else:
                for key, value in temp.items():
                    setattr(task, key, value)
            res = cls(task, app=app)
            return res

    @staticmethod
    async def to_model_schedule(name: str, task: str, schedule: schedules.schedule | TzAwareCrontab) -> TaskScheduler:
        schedule = schedules.maybe_schedule(schedule)

        async with async_db_session() as db:
            if isinstance(schedule, schedules.schedule):
                every = max(schedule.run_every.total_seconds(), 0)
                spec = {
                    'name': name,
                    'type': TaskSchedulerType.INTERVAL.value,
                    'interval_every': every,
                    'interval_period': PeriodType.SECONDS.value,
                }
                stmt = select(TaskScheduler).filter_by(**spec, deleted=0)
                query = await db.execute(stmt)
                obj = query.scalars().first()
                if not obj:
                    obj = TaskScheduler(**CreateTaskSchedulerParam(task=task, **spec).model_dump())
            elif isinstance(schedule, schedules.crontab):
                crontab = f'{schedule._orig_minute} {schedule._orig_hour} {schedule._orig_day_of_month} {schedule._orig_month_of_year} {schedule._orig_day_of_week}'  # ruff:ignore[line-too-long]
                crontab_verify(crontab)
                spec = {
                    'name': name,
                    'type': TaskSchedulerType.CRONTAB.value,
                    'crontab': crontab,
                }
                stmt = select(TaskScheduler).filter_by(**spec, deleted=0)
                query = await db.execute(stmt)
                obj = query.scalars().first()
                if not obj:
                    obj = TaskScheduler(**CreateTaskSchedulerParam(task=task, **spec).model_dump())
            else:
                raise errors.NotFoundError(msg=f'Unsupported schedule type: {schedule}')

            return obj

    @classmethod
    async def _unpack_fields(
        cls,
        name: str,
        task: str,
        schedule: schedules.schedule | TzAwareCrontab,
        args: tuple | None = None,
        kwargs: dict | None = None,
        options: dict | None = None,
        **entry,
    ) -> dict:
        model_schedule = await cls.to_model_schedule(name, task, schedule)
        model_dict = select_as_dict(model_schedule)
        for k in ['id', 'created_time', 'updated_time', 'deleted', 'deleted_time']:
            try:
                del model_dict[k]
            except KeyError:  # ruff:ignore[try-except-in-loop]
                continue
        model_dict.update(
            args=json.dumps(args, ensure_ascii=False) if args else None,
            kwargs=json.dumps(kwargs, ensure_ascii=False) if kwargs else None,
            **cls._unpack_options(**options or {}),
            **entry,
        )
        if 'enabled' in model_dict:
            enabled = model_dict.pop('enabled')
            model_dict['status'] = StatusType.enable if enabled else StatusType.disable
        return model_dict

    @classmethod
    def _unpack_options(
        cls,
        queue: str | None = None,
        exchange: str | None = None,
        routing_key: str | None = None,
        start_time: datetime | None = None,
        expires: datetime | None = None,
        expire_seconds: int | None = None,
        *,
        one_off: bool = False,
    ) -> dict:
        data = {
            'queue': queue,
            'exchange': exchange,
            'routing_key': routing_key,
            'start_time': start_time,
            'expire_time': None,
            'expire_seconds': expire_seconds,
            'one_off': one_off,
        }
        if expires:
            if isinstance(expires, int):
                data['expire_seconds'] = expires
            elif isinstance(expires, timedelta):
                data['expire_time'] = timezone.now() + expires
            elif isinstance(expires, datetime):
                data['expire_time'] = expires
        return data


class DatabaseScheduler(Scheduler):
    """Database scheduler"""

    Entry = ModelEntry

    _schedule = None
    _last_update = None
    _initial_read = True
    _heap_invalidated = False

    lock: Lock | None = None
    lock_key = f'{settings.CELERY_REDIS_PREFIX}:beat_lock'

    def __init__(self, *args, **kwargs) -> None:
        self.app = kwargs['app']
        self._dirty = set()
        super().__init__(*args, **kwargs)
        self._finalize = Finalize(self, self.sync, exitpriority=5)
        self.max_interval = kwargs.get('max_interval') or self.app.conf.beat_max_loop_interval or _DEFAULT_MAX_INTERVAL

    def schedules_equal(self, *args, **kwargs) -> bool:
        """Override parent method"""
        if self._heap_invalidated:
            self._heap_invalidated = False
            return False
        return super().schedules_equal(*args, **kwargs)

    def reserve(self, entry):  # ruff:ignore[missing-type-function-argument, missing-return-type-undocumented-public-function]
        """Override parent method"""
        new_entry = next(entry)
        # Store entries by name because the entries may change
        self._dirty.add(new_entry.name)
        return new_entry

    def setup_schedule(self) -> None:
        """Override parent method"""
        logger.info('setup_schedule')
        tasks = self.schedule
        self.install_default_entries(tasks)
        self.update_from_dict(self.app.conf.beat_schedule)

    def sync(self) -> None:
        """Override parent method"""
        tried = set()
        failed = set()
        try:
            while self._dirty:
                name = self._dirty.pop()
                try:
                    tasks = self.schedule
                    run_await(tasks[name].save)()
                    logger.debug(f'Saving latest state of task {name} to the database')
                    tried.add(name)
                except KeyError as e:
                    logger.error(f'Failed to save latest state of task {name}: {e} ')
                    failed.add(name)
        except DatabaseError:
            logger.exception('Database error during synchronization')
        except InterfaceError as e:
            logger.warning(f'DatabaseScheduler InterfaceError: {e!s}; will retry on the next call...')
        finally:
            # Retry later (failed entries only)
            self._dirty |= failed

    def tick(self, **kwargs) -> float:
        """Override parent method"""
        if self.lock:
            logger.debug('beat: Extending lock...')
            run_await(self.lock.extend)(_DEFAULT_MAX_LOCK_TIMEOUT, replace_ttl=True)

        return super().tick(**kwargs)

    def close(self) -> None:
        """Override parent method"""
        if self.lock:
            logger.info('beat: Releasing lock')
            if run_await(self.lock.owned)():
                run_await(self.lock.release)()
            self.lock = None

        super().close()

    def update_from_dict(self, beat_dict: dict) -> None:
        """Override parent method"""
        s = {}
        name = None
        try:
            for name, entry_fields in beat_dict.items():
                entry = run_await(self.Entry.from_entry)(name, app=self.app, **entry_fields)
                if entry.model.status == StatusType.enable:
                    s[name] = entry
        except Exception:
            logger.error(f'Failed to add task {name} to the database')
            raise

        tasks = self.schedule
        tasks.update(s)

    def schedule_changed(self) -> bool | None:
        """Task schedule change status"""
        now = timezone.now()
        last_update_key = f'{settings.CELERY_REDIS_PREFIX}:last_update'
        last_update = run_await(redis_client.get)(last_update_key)
        if not last_update:
            run_await(redis_client.set)(last_update_key, timezone.to_str(now))
            return False

        last, ts = self._last_update, timezone.from_str(last_update)
        try:
            if ts and ts > (last or ts):
                return True
        finally:
            self._last_update = now

    async def get_all_task_schedulers(self) -> dict:
        """Get all task schedules"""
        async with async_db_session() as db:
            logger.debug('DatabaseScheduler: Fetching database schedule')
            stmt = select(TaskScheduler).where(
                TaskScheduler.status == StatusType.enable,
                TaskScheduler.deleted == 0,
            )
            query = await db.execute(stmt)
            schedulers = query.scalars().all()
            s = {}
            for scheduler in schedulers:
                s[scheduler.name] = self.Entry(scheduler, app=self.app)
            return s

    @property
    def schedule(self) -> dict[str, ModelEntry]:
        """Get task schedule"""
        initial = update = False
        if self._initial_read:
            logger.debug('DatabaseScheduler: initial read')
            initial = update = True
            self._initial_read = False
        elif self.schedule_changed():
            logger.info('DatabaseScheduler: Schedule changed.')
            update = True

        if update:
            logger.debug('beat: Synchronizing schedule...')
            self.sync()
            self._schedule = run_await(self.get_all_task_schedulers)()
            # Schedule changed; invalidate the heap in Scheduler.tick
            if not initial:
                self._heap = []
                self._heap_invalidated = True
            logger.debug(
                'Current schedule:\n%s',
                '\n'.join(repr(entry) for entry in self._schedule.values()),
            )

        # logger.debug(self._schedule)
        return self._schedule


@beat_init.connect
def acquire_distributed_beat_lock(sender=None, **kwargs) -> None:  # ruff:ignore[missing-type-function-argument]
    """
    Try to acquire the lock at startup

    :param sender: Sender to which the receiver should respond
    :return:
    """
    scheduler = sender.scheduler
    if not scheduler.lock_key:
        return

    logger.debug('beat: Acquiring lock...')
    lock = redis_client.lock(
        scheduler.lock_key,
        timeout=_DEFAULT_MAX_LOCK_TIMEOUT,
        sleep=scheduler.max_interval,
    )

    run_await(lock.acquire)()
    logger.info('beat: Acquired lock')
    scheduler.lock = lock
