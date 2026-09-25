import glob
import json

from pathlib import Path
from typing import Any

import yaml

from starlette_context.errors import ContextDoesNotExistError

from backend.common.context import ctx
from backend.core.conf import settings
from backend.core.path_conf import LOCALE_DIR


class I18n:
    """Internationalization manager"""

    def __init__(self) -> None:
        self.locales: dict[str, dict[str, Any]] = {}
        self.load_locales()

    @property
    def current_language(self) -> str:
        """Get the language of the current request"""
        try:
            return ctx.language
        except (AttributeError, LookupError, ContextDoesNotExistError):
            return settings.I18N_DEFAULT_LANGUAGE

    @current_language.setter
    def current_language(self, language: str) -> None:
        """Set the language of the current request"""
        ctx.language = language

    def load_locales(self) -> None:
        """Load locale texts"""
        patterns = [
            LOCALE_DIR / '*.json',
            LOCALE_DIR / '*.yaml',
            LOCALE_DIR / '*.yml',
        ]

        lang_files = []

        for pattern in patterns:
            lang_files.extend(glob.glob(str(pattern)))

        for lang_file in lang_files:
            with open(lang_file, encoding='utf-8') as f:
                lang = Path(lang_file).stem
                file_type = Path(lang_file).suffix[1:]
                match file_type:
                    case 'json':
                        self.locales[lang] = json.loads(f.read())
                    case 'yaml' | 'yml':
                        self.locales[lang] = yaml.safe_load(f.read())

    def t(self, key: str, default: Any | None = None, **kwargs) -> str:
        """
        Translation function

        :param key: Target text key; supports dot notation, such as 'response.success'
        :param default: Default text when the target translation is missing
        :param kwargs: Variable arguments in the target text
        :return:
        """
        keys = key.split('.')

        try:
            translation = self.locales[self.current_language]
        except KeyError:
            keys = 'error.language_not_found'.split('.')
            translation = self.locales[settings.I18N_DEFAULT_LANGUAGE]

        for k in keys:
            if isinstance(translation, dict) and k in list(translation.keys()):
                translation = translation[k]
            else:
                # Pydantic compatibility
                translation = None if keys[0] == 'pydantic' else key
                break

        if translation and kwargs:
            translation = translation.format(**kwargs)

        return translation or default


# Create the i18n singleton
i18n = I18n()

# Create the translation function alias
t = i18n.t
