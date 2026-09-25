from pathlib import Path

# Project root directory
BASE_PATH = Path(__file__).resolve().parent.parent

# Environment variables file
ENV_FILE_PATH = BASE_PATH / '.env'

# Example environment variables file
ENV_EXAMPLE_FILE_PATH = BASE_PATH / '.env.example'

# Alembic migration directory
ALEMBIC_VERSION_DIR = BASE_PATH / 'alembic' / 'versions'

# Log file path
LOG_DIR = BASE_PATH / 'log'

# Static resource directory
STATIC_DIR = BASE_PATH / 'static'

# Upload directory
UPLOAD_DIR = STATIC_DIR / 'upload'

# Plugin directory
PLUGIN_DIR = BASE_PATH / 'plugin'

# Locale file directory
LOCALE_DIR = BASE_PATH / 'locale'

# MySQL script directory
MYSQL_SCRIPT_DIR = BASE_PATH / 'sql' / 'mysql'

# PostgreSQL script directory
POSTGRESQL_SCRIPT_DIR = BASE_PATH / 'sql' / 'postgresql'

# Hot reload lock file
RELOAD_LOCK_FILE = BASE_PATH / '.reload.lock'
