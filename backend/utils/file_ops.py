from anyio import open_file
from fastapi import UploadFile

from backend.common.exception import errors
from backend.common.log import log
from backend.core.conf import settings
from backend.core.path_conf import UPLOAD_DIR
from backend.utils.timezone import timezone


def build_filename(file: UploadFile) -> str:
    """
    Build filename

    :param file: FastAPI uploaded file object
    :return:
    """
    timestamp = int(timezone.now().timestamp())
    filename = file.filename
    file_ext = filename.split('.')[-1].lower()
    new_filename = f'{filename.replace(f".{file_ext}", f"_{timestamp}")}.{file_ext}'
    return new_filename


def upload_file_verify(file: UploadFile) -> None:
    """
    Validate file

    :param file: FastAPI uploaded file object
    :return:
    """
    filename = file.filename
    file_ext = filename.split('.')[-1].lower()
    if not file_ext:
        raise errors.RequestError(msg='Unknown file type')

    if file_ext in settings.UPLOAD_IMAGE_EXT_INCLUDE:
        if file.size > settings.UPLOAD_IMAGE_SIZE_MAX:
            raise errors.RequestError(msg='Image exceeds the size limit; select another image')
    elif file_ext in settings.UPLOAD_VIDEO_EXT_INCLUDE:
        if file.size > settings.UPLOAD_VIDEO_SIZE_MAX:
            raise errors.RequestError(msg='Video exceeds the size limit; select another video')
    else:
        raise errors.RequestError(msg=f'File format {file_ext} is not supported')


async def upload_file(file: UploadFile) -> str:
    """
    Upload file

    :param file: FastAPI uploaded file object
    :return:
    """
    filename = build_filename(file)
    try:
        async with await open_file(UPLOAD_DIR / filename, mode='wb') as fb:
            while True:
                content = await file.read(settings.UPLOAD_READ_SIZE)
                if not content:
                    break
                await fb.write(content)
    except Exception as e:
        log.error(f'Failed to upload file {filename}: {e!s}')
        raise errors.RequestError(msg='File upload failed')
    await file.close()
    return filename
