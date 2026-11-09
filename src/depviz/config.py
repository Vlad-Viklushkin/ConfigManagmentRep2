"""Чтение и проверка конфигурационного файла в формате TOML."""

import tomllib
from dataclasses import dataclass

from depviz.errors import ConfigError
from depviz.validators import (
    validate_output_file,
    validate_package_name,
    validate_repository,
    validate_test_mode,
    validate_version,
)

PARAM_NAMES = (
    "package_name",
    "repository",
    "test_mode",
    "version",
    "output_file",
)


@dataclass(frozen=True)
class Config:
    """Параметры, настраиваемые пользователем.

    Attributes:
        package_name: имя анализируемого пакета.
        repository: URL репозитория или путь к файлу тестового репозитория.
        test_mode: ``True`` - работа с файловым тестовым репозиторием.
        version: версия пакета.
        output_file: имя файла с изображением графа.
    """

    package_name: str
    repository: str
    test_mode: bool
    version: str
    output_file: str

    def as_pairs(self):
        """Возвращает параметры как список пар (ключ, значение).

        Returns:
            Список пар в порядке, определенном ``PARAM_NAMES``.
        """
        return [(name, getattr(self, name)) for name in PARAM_NAMES]


def read_toml(path):
    """Читает TOML-файл и возвращает его содержимое.

    Args:
        path: путь к конфигурационному файлу.

    Returns:
        Словарь с данными файла.

    Raises:
        ConfigError: если файл недоступен или содержит некорректный TOML.
    """
    try:
        with open(path, "rb") as stream:
            return tomllib.load(stream)
    except FileNotFoundError:
        raise ConfigError([f"файл конфигурации не найден: {path}"])
    except OSError as exc:
        raise ConfigError([f"не удалось прочитать {path}: {exc.strerror}"])
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise ConfigError([f"некорректный TOML в {path}: {exc}"])


def _structure_problems(raw):
    """Находит лишние и отсутствующие ключи.

    Args:
        raw: словарь, прочитанный из TOML.

    Returns:
        Список текстовых описаний проблем.
    """
    problems = [
        f"неизвестный параметр: {key}"
        for key in raw
        if key not in PARAM_NAMES
    ]
    problems += [
        f"{name}: обязательный параметр не задан"
        for name in PARAM_NAMES
        if name not in raw
    ]
    return problems


def _check(problems, validator, raw, key, *extra):
    """Проверяет один параметр, запоминая найденную проблему.

    Args:
        problems: список, в который добавляется описание проблемы.
        validator: функция проверки значения.
        raw: словарь с данными конфигурации.
        key: имя проверяемого параметра.
        *extra: дополнительные аргументы для ``validator``.

    Returns:
        Проверенное значение или ``None``, если проверка не пройдена.
    """
    if key not in raw:
        return None
    try:
        return validator(raw[key], *extra)
    except ValueError as exc:
        problems.append(f"{key}: {exc}")
        return None


def build_config(raw):
    """Проверяет данные конфигурации и создает объект ``Config``.

    Args:
        raw: словарь, прочитанный из TOML.

    Returns:
        Объект ``Config`` с проверенными значениями.

    Raises:
        ConfigError: если найдена хотя бы одна проблема.
    """
    problems = _structure_problems(raw)
    mode = _check(problems, validate_test_mode, raw, "test_mode")
    values = {
        "package_name": _check(
            problems, validate_package_name, raw, "package_name", mode
        ),
        "repository": _check(
            problems, validate_repository, raw, "repository", mode
        ),
        "test_mode": mode,
        "version": _check(problems, validate_version, raw, "version"),
        "output_file": _check(
            problems, validate_output_file, raw, "output_file"
        ),
    }
    if problems:
        raise ConfigError(problems)
    return Config(**values)


def load_config(path):
    """Загружает и проверяет конфигурацию из TOML-файла.

    Args:
        path: путь к конфигурационному файлу.

    Returns:
        Объект ``Config``.

    Raises:
        ConfigError: при любой ошибке чтения или проверки.
    """
    return build_config(read_toml(path))
