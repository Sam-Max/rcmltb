"""A FIFO Asynchronous Queue """

from asyncio import (
    sleep,
    CancelledError,
    AbstractEventLoop,
    PriorityQueue,
    Task,
)
import dataclasses
import typing
import inspect
import sys
import uuid
from bot import LOGGER, PARALLEL_TASKS, bot_loop, bot


queue = None


async def queue_worker(name, queue):
    while not bot_loop.is_closed():
        while queue.empty():
            try:
                await sleep(0.1)
            except CancelledError:
                return
        try:
            queue_item = await queue.get()
            LOGGER.info(f"{name} is processing queue item: {queue_item}")
            resp = await safe_run(
                queue_item.task,
                queue_item.task_args,
                queue_item.exception_callback,
                queue_item.exception_callback_args,
                bot_loop,
            )
            if queue_item.done_callback:
                args = queue_item.done_callback_args or ()
                if resp and queue_item.pass_result_to_done_callback:
                    args = (resp,) + args
                await safe_run(
                    queue_item.done_callback,
                    args,
                    queue_item.exception_callback,
                    queue_item.exception_callback_args,
                    bot_loop,
                )
            queue.task_done()
        except RuntimeError as runtime_error:
            if bot_loop.is_closed():
                return
            raise runtime_error
        except CancelledError:
            return
        except GeneratorExit:
            return
        except KeyboardInterrupt:
            return
        except Exception as excp:
            LOGGER.error(excp, exc_info=True)


async def safe_run(
    task: typing.Any,
    task_args: typing.Any,
    exception_callback: typing.Any,
    exception_callback_args: typing.Any,
    loop: AbstractEventLoop,
):
    resp = None
    try:
        if inspect.iscoroutine(task):
            resp = await task
        elif inspect.iscoroutinefunction(task):
            resp = await task(*task_args or {})
        elif inspect.isfunction(task) or inspect.ismethod(task):
            resp = await loop.run_in_executor(None, task, *task_args or {})
        else:
            LOGGER.error("%s is not a coroutine or function", task, stack_info=True)
    # catching all exceptions is bad, but this is a background task
    except:
        _, exception, _ = sys.exc_info()
        if exception_callback:
            if inspect.iscoroutinefunction(exception_callback):
                await exception_callback(
                    exception,
                    *exception_callback_args or {},
                )
            elif inspect.isfunction(exception_callback) or inspect.ismethod(
                exception_callback
            ):
                await loop.run_in_executor(
                    None,
                    exception_callback,
                    exception,
                    *exception_callback_args or {},
                )
        else:
            LOGGER.error(exception, exc_info=True, stack_info=True)
    else:
        return resp


@dataclasses.dataclass(frozen=True, order=False)
class QueueItem:
    """A item on a `asyncio.Queue`"""

    priority: int
    task: typing.Callable | typing.Coroutine | typing.Awaitable
    task_args: typing.Optional[tuple] = dataclasses.field(default_factory=tuple)
    pass_result_to_done_callback: bool = dataclasses.field(default=False)

    done_callback: typing.Optional[
        typing.Callable | typing.Coroutine
    ] = dataclasses.field(default=None)

    done_callback_args: typing.Optional[tuple] = dataclasses.field(
        default_factory=tuple
    )

    exception_callback: typing.Optional[
        typing.Callable | typing.Awaitable
    ] = dataclasses.field(default=None)

    """ This function/awaitable must accept the exception as its first argument. """
    exception_callback_args: typing.Optional[tuple] = dataclasses.field(
        default_factory=tuple
    )

    # Make the QueueItem sortable (by priority)
    def __lt__(self, other: "QueueItem"):
        return self.priority < other.priority

    def __gt__(self, other: "QueueItem"):
        return self.priority > other.priority

    def __le__(self, other: "QueueItem"):
        return self.priority <= other.priority

    def __ge__(self, other: "QueueItem"):
        return self.priority >= other.priority


class QueueManager:
    slug_name: str
    queue: PriorityQueue[QueueItem]
    tasks: list[Task]
    len_workers: int
    _configured: bool

    def __init__(
        self,
        slug_name,
        queue=None,
        max_queue_size=0,
        num_workers=1,
        create_queue=True,
        configure_on_init=True,
    ) -> None:
        if create_queue or not queue:
            self.queue = PriorityQueue(maxsize=max_queue_size)
        else:
            self.queue = queue

        self.slug_name = slug_name or f"unspecified-core-{uuid.uuid4()}"
        self._configured = False
        self.workers = [
            (
                queue_worker(f"{self.slug_name}-worker-{i}", self.queue),
                f"{self.slug_name}-worker-{i}",
            )
            for i in range(1, num_workers + (1 if num_workers else 0), 1)
        ]
        self.worker_manager = None
        LOGGER.info(
            f"Initialized a new {self.slug_name} QueueManager",
        )
        if configure_on_init:
            self.configure()

    def configure(self):
        self.tasks = [
            bot_loop.create_task(coroutine, name=name)
            for coroutine, name in self.workers
        ]
        self._configured = True
        return True

    async def restart_worker(self, task: Task) -> None:
        worker_location = self.workers.index(task)
        self.workers[worker_location] = bot_loop.create_task(
            queue_worker(
                task.get_name(),
                self.queue,
            ),
            name=f"{self.slug_name}-worker-{len(self.workers)}",
        )

    async def auto_restart_workers(self):
        try:
            for task in self.tasks:
                if task.done() or task.cancelled():
                    await self.restart_worker(task)
            await sleep(5)
        except CancelledError:
            return

    async def put(self, item):
        await self.queue.put(item)

    def close(self) -> None:
        if not self._configured:
            return
        for task in self.tasks:
            task.cancel()


async def conditional_queue_add(message, func, *args, **kwargs):
    if PARALLEL_TASKS > 0:
        await add_to_queue(message, func, *args, **kwargs)
    else:
        await func(*args, **kwargs)


async def add_to_queue(message, task, *args, **kwargs):
    LOGGER.info(f"Adding {task} on the queue")
    if queue.queue.full():
        return await bot.send_message(
            message.chat.id,
            reply_to_message_id=message.id,
            text="Queue is full, wait for a slot to be available..",
        )
    await queue.put(
        QueueItem(priority=1, task=task(*args, **kwargs)),
    )


if PARALLEL_TASKS > 0:
    queue = QueueManager(
        slug_name="all-queue",
        create_queue=True,
        max_queue_size=PARALLEL_TASKS,
        num_workers=PARALLEL_TASKS,
        configure_on_init=True,
    )
