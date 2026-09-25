"""Locale coverage and HTTP language selection without database or Redis services."""

import json

from pathlib import Path
from string import Formatter
from typing import Annotated, Any

import pytest
import yaml

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, field_validator
from starlette_context.middleware import RawContextMiddleware

from backend.common.exception.exception_handler import register_exception
from backend.common.i18n import i18n, t
from backend.core.conf import settings
from backend.middleware.i18n_middleware import I18nMiddleware

LOCALES = Path(__file__).resolve().parents[1] / 'backend' / 'locale'


def flatten_messages(data: dict[str, Any], prefix: str = '') -> dict[str, str]:
    result = {}
    for key, value in data.items():
        path = f'{prefix}.{key}' if prefix else key
        if isinstance(value, dict):
            result.update(flatten_messages(value, path))
        else:
            result[path] = value
    return result


def test_farsi_locale_coverage_and_placeholders() -> None:
    chinese = flatten_messages(yaml.safe_load((LOCALES / 'zh-CN.yml').read_text(encoding='utf-8')))
    farsi = flatten_messages(yaml.safe_load((LOCALES / 'fa-IR.yml').read_text(encoding='utf-8')))
    english = flatten_messages(json.loads((LOCALES / 'en-US.json').read_text(encoding='utf-8')))
    assert farsi.keys() == chinese.keys()
    assert english.keys() <= farsi.keys()
    formatter = Formatter()
    for key, message in farsi.items():
        assert isinstance(message, str) and message.strip(), key
        fields = {field for _, field, _, _ in formatter.parse(message) if field is not None}
        expected = {field for _, field, _, _ in formatter.parse(chinese[key]) if field is not None}
        assert fields == expected, key
        message.format(**dict.fromkeys(fields, 'sample'))


class ValidationInput(BaseModel):
    name: Annotated[str, Field(min_length=3)]
    quantity: Annotated[int, Field(gt=0)]

    @field_validator('name')
    @classmethod
    def reject_reserved_name(cls, value: str) -> str:
        if value == 'reserved':
            raise ValueError('Reserved name')
        return value


@pytest.fixture
def locale_client() -> TestClient:
    app = FastAPI()
    app.add_middleware(I18nMiddleware)
    app.add_middleware(RawContextMiddleware)
    register_exception(app)

    @app.get('/message')
    def message() -> dict[str, str]:
        return {'message': t('response.success')}

    @app.post('/validate')
    def validate(payload: ValidationInput) -> ValidationInput:
        return payload

    return TestClient(app)


@pytest.mark.parametrize(
    'language, locale',
    [
        ('fa', 'fa-IR'),
        ('fa-IR', 'fa-IR'),
        ('FA-ir', 'fa-IR'),
        ('fa-IR, en-US;q=0.8', 'fa-IR'),
        ('en', 'en-US'),
        ('en-US', 'en-US'),
        ('zh', 'zh-CN'),
        ('zh-CN', 'zh-CN'),
        ('zh-Hans', 'zh-CN'),
    ],
)
def test_request_language_selection(locale_client: TestClient, language: str, locale: str) -> None:
    response = locale_client.get('/message', headers={'Accept-Language': language})
    assert response.status_code == 200
    assert response.json()['message'] == i18n.locales[locale]['response']['success']


@pytest.mark.parametrize('locale', ['fa-IR', 'zh-CN'])
@pytest.mark.parametrize(
    'payload, error_type, arguments',
    [
        ({'name': 'ab', 'quantity': 1}, 'string_too_short', {'min_length': 3}),
        ({'name': 'valid', 'quantity': 0}, 'greater_than', {'gt': 0}),
        ({'name': 'valid', 'quantity': 'invalid'}, 'int_parsing', {}),
        ({'quantity': 1}, 'missing', {}),
        ({'name': 'reserved', 'quantity': 1}, 'value_error', {'error': 'Reserved name'}),
    ],
)
def test_localized_validation(
    locale_client: TestClient,
    locale: str,
    payload: dict[str, Any],
    error_type: str,
    arguments: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, 'ENVIRONMENT', 'dev')
    response = locale_client.post('/validate', json=payload, headers={'Accept-Language': locale})
    assert response.status_code == 422
    error = response.json()['data']['errors'][0]
    assert error['type'] == error_type
    assert error['msg'] == i18n.locales[locale]['pydantic'][error_type].format(**arguments)


def test_language_does_not_leak_between_requests(locale_client: TestClient) -> None:
    locale_client.get('/message', headers={'Accept-Language': 'fa-IR'})
    response = locale_client.get('/message')
    assert response.json()['message'] == i18n.locales[settings.I18N_DEFAULT_LANGUAGE]['response']['success']


def test_english_validation_remains_native(locale_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, 'ENVIRONMENT', 'dev')
    response = locale_client.post('/validate', json={'name': 'ab', 'quantity': 1}, headers={'Accept-Language': 'en-US'})
    assert response.status_code == 422
    assert response.json()['data']['errors'][0]['msg'] == 'String should have at least 3 characters'
