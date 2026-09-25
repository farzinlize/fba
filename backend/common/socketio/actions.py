from backend.common.socketio.server import sio


async def task_notification(msg: str) -> None:
    """
    Task notification

    :param msg: Notification information
    :return:
    """
    await sio.emit('task_notification', {'msg': msg})
