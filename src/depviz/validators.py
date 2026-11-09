"""Проверки значений отдельных параметров конфигурации.

Каждая функция возвращает проверенное значение либо выбрасывает
``ValueError`` с понятным пользователю описанием проблемы.
"""

import os
import re
from urllib.parse import urlparse

MAX_NPM_NAME_LENGTH = 214
URL_SCHEMES = ("http", "https")
OUTPUT_EXTENSION = ".png"

NPM_NAME_RE = re.compile(
    r"(@[a-z0-9-~][a-z0-9-._~]*/)?[a-z0-9-~][a-z0-9-._~]*"
)
TEST_NAME_RE = re.compile(r"[A-Z]+")
SEMVER_RE = re.compile(
    r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?"
    r"(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?"
)


def _require_text(value):
    """Проверяет, что значение - непустая строка.

    Args:
        value: проверяемое значение.

    Returns:
        Исходная строка.

    Raises:
        ValueError: если значение не строка или строка пустая.
    """
    if not isinstance(value, str):
        raise ValueError("ожидается строка")
    if not value.strip():
        raise ValueError("значение не должно быть пустым")
    return value


def validate_test_mode(value):
    """Проверяет флаг режима тестового репозитория.

    Args:
        value: значение из конфигурации.

    Returns:
        Булево значение.

    Raises:
        ValueError: если значение не булево (true/false).
    """
    if not isinstance(value, bool):
        raise ValueError("ожидается логическое значение true или false")
    return value


def validate_package_name(value, test_mode=None):
    """Проверяет имя анализируемого пакета.

    Args:
        value: значение из конфигурации.
        test_mode: режим работы; ``None``, если режим не определен.

    Returns:
        Имя пакета.

    Raises:
        ValueError: если имя не соответствует выбранному режиму.
    """
    _require_text(value)
    if test_mode is None:
        return value
    if test_mode:
        if not TEST_NAME_RE.fullmatch(value):
            raise ValueError(
                "в тестовом режиме имя пакета - большие латинские буквы"
            )
        return value
    if len(value) > MAX_NPM_NAME_LENGTH:
        raise ValueError(
            f"имя npm-пакета длиннее {MAX_NPM_NAME_LENGTH} символов"
        )
    if not NPM_NAME_RE.fullmatch(value):
        raise ValueError("недопустимое имя npm-пакета")
    return value


def _is_http_url(value):
    """Проверяет, что строка - абсолютный http(s)-адрес.

    Args:
        value: проверяемая строка.

    Returns:
        ``True``, если строка является http или https URL с хостом.
    """
    parsed = urlparse(value)
    return parsed.scheme in URL_SCHEMES and bool(parsed.netloc)


def validate_repository(value, test_mode=None):
    """Проверяет URL репозитория или путь к файлу тестового репозитория.

    Args:
        value: значение из конфигурации.
        test_mode: режим работы; ``None``, если режим не определен.

    Returns:
        URL или путь к файлу.

    Raises:
        ValueError: если значение не подходит выбранному режиму.
    """
    _require_text(value)
    if test_mode is None:
        return value
    if test_mode:
        if not os.path.isfile(value):
            raise ValueError(f"файл тестового репозитория не найден: {value}")
        return value
    if not _is_http_url(value):
        raise ValueError("ожидается URL вида http://... или https://...")
    return value


def validate_version(value):
    """Проверяет версию пакета (формат SemVer, например 1.2.3).

    Args:
        value: значение из конфигурации.

    Returns:
        Строка версии.

    Raises:
        ValueError: если версия не соответствует SemVer.
    """
    _require_text(value)
    if not SEMVER_RE.fullmatch(value):
        raise ValueError("ожидается версия в формате SemVer, например 1.2.3")
    return value


def validate_output_file(value):
    """Проверяет имя файла с изображением графа.

    Args:
        value: значение из конфигурации.

    Returns:
        Имя файла.

    Raises:
        ValueError: если расширение не .png, имя пустое или
            каталог назначения не существует.
    """
    _require_text(value)
    if not value.lower().endswith(OUTPUT_EXTENSION):
        raise ValueError(f"файл должен иметь расширение {OUTPUT_EXTENSION}")
    name = os.path.basename(value)
    if len(name) == len(OUTPUT_EXTENSION):
        raise ValueError("не указано имя файла перед расширением")
    directory = os.path.dirname(value)
    if directory and not os.path.isdir(directory):
        raise ValueError(f"каталог не существует: {directory}")
    return value
