"""Интерфейс командной строки."""

import argparse
import json
import sys

from depviz import __version__
from depviz.config import load_config
from depviz.errors import ConfigError

DEFAULT_CONFIG = "config.toml"
EXIT_OK = 0
EXIT_CONFIG_ERROR = 1


def build_parser():
    """Создает разборщик аргументов командной строки.

    Returns:
        Настроенный ``argparse.ArgumentParser``.
    """
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Визуализатор графа зависимостей npm-пакетов.",
    )
    parser.add_argument(
        "-c",
        "--config",
        default=DEFAULT_CONFIG,
        help=f"путь к TOML-конфигурации (по умолчанию {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def format_value(value):
    """Форматирует значение параметра в TOML-стиле.

    Args:
        value: строка или булево значение.

    Returns:
        Строковое представление: строки в кавычках, булевы в нижнем
        регистре.
    """
    return json.dumps(value, ensure_ascii=False)


def print_config(config, stream):
    """Выводит все параметры в формате ключ-значение.

    Args:
        config: объект ``Config``.
        stream: поток вывода.
    """
    for key, value in config.as_pairs():
        print(f"{key} = {format_value(value)}", file=stream)


def print_errors(problems, stream):
    """Выводит список ошибок конфигурации.

    Args:
        problems: список текстовых описаний проблем.
        stream: поток вывода.
    """
    print("Ошибка конфигурации:", file=stream)
    for problem in problems:
        print(f"  - {problem}", file=stream)


def main(argv=None):
    """Запускает приложение.

    Args:
        argv: список аргументов; по умолчанию берется из ``sys.argv``.

    Returns:
        Код завершения процесса.
    """
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print_errors(exc.problems, sys.stderr)
        return EXIT_CONFIG_ERROR
    print_config(config, sys.stdout)
    return EXIT_OK
