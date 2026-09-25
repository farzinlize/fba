import granian

from backend.cli import CustomReloadFilter

if __name__ == '__main__':
    # DEBUG:
    # To debug in an IDE, run this file directly from the IDE
    # For print-based debugging, start the service using the FBA CLI

    # Warning:
    # When starting this file with the python command, follow these steps:
    # 1. Install dependencies using uv as described in the official documentation
    # 2. Run the command from the backend directory
    granian.Granian(
        target='main:app',
        interface='asgi',
        address='127.0.0.1',
        port=8000,
        reload=True,
        reload_filter=CustomReloadFilter,
    ).serve()
