from typing import Final

import anyio

from anyio import open_file
from sqlparse import split

from backend.common.exception import errors

# SQL statement prefixes allowed in initialization scripts
_INIT_SQL_PREFIXES: Final = frozenset({'select', 'insert', 'set', 'do'})

# SQL statement prefixes allowed in teardown scripts
_DESTROY_SQL_PREFIXES: Final = _INIT_SQL_PREFIXES | {'drop', 'delete', 'alter'}


async def parse_sql_script(filepath: str, *, is_destroy: bool = False) -> list[str]:
    """
    Parse SQL script

    :param filepath: Script file path
    :param is_destroy: Whether this is a teardown script allowing destructive operations
    :return:
    """
    path = anyio.Path(filepath)
    if not await path.exists():
        raise errors.NotFoundError(msg='SQL script file does not exist')

    async with await open_file(filepath, encoding='utf-8') as f:
        contents = await f.read(1024)
        while additional_contents := await f.read(1024):
            contents += additional_contents

    statements = [stmt for stmt in split(contents) if stmt.strip()]
    allowed_prefixes = _DESTROY_SQL_PREFIXES if is_destroy else _INIT_SQL_PREFIXES
    for statement in statements:
        if not any(statement.strip().lower().startswith(prefix) for prefix in allowed_prefixes):
            raise errors.RequestError(
                msg=(
                    f'SQL script {filepath} contains a disallowed operation; only these are allowed: '
                    f'{", ".join(item.upper() for item in sorted(allowed_prefixes))}'
                )
            )

    return statements
