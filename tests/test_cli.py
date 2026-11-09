"""Тесты интерфейса командной строки."""

import contextlib
import io
import os
import subprocess
import sys
import unittest

from depviz import cli
from helpers import VALID_TOML, write_temp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_main(*argv):
    """Запускает ``cli.main`` и перехватывает вывод.

    Args:
        *argv: аргументы командной строки.

    Returns:
        Кортеж (код завершения, stdout, stderr).
    """
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class TestMain(unittest.TestCase):
    """Поведение функции main."""

    def test_prints_all_parameters(self):
        """Все параметры выводятся в формате ключ-значение."""
        path = write_temp(self, VALID_TOML)
        code, out, err = run_main("--config", path)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertEqual(err, "")
        self.assertEqual(
            out.splitlines(),
            [
                'package_name = "express"',
                'repository = "https://registry.npmjs.org"',
                "test_mode = false",
                'version = "4.18.2"',
                'output_file = "graph.png"',
            ],
        )

    def test_short_option(self):
        """Короткая опция -c работает так же, как --config."""
        path = write_temp(self, VALID_TOML)
        code, out, _ = run_main("-c", path)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("package_name", out)

    def test_config_error_exit_code(self):
        """Ошибка конфигурации: код 1, сообщение в stderr, stdout пуст."""
        path = write_temp(self, VALID_TOML.replace("4.18.2", "latest"))
        code, out, err = run_main("--config", path)
        self.assertEqual(code, cli.EXIT_CONFIG_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка конфигурации", err)
        self.assertIn("version", err)

    def test_missing_config_file(self):
        """Отсутствующий файл конфигурации обрабатывается без traceback."""
        code, _, err = run_main("--config", "/no/such/file.toml")
        self.assertEqual(code, cli.EXIT_CONFIG_ERROR)
        self.assertIn("не найден", err)
        self.assertNotIn("Traceback", err)

    def test_unknown_argument(self):
        """Неизвестный аргумент завершает разбор с кодом 2."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                cli.main(["--bogus"])
        self.assertEqual(ctx.exception.code, 2)


class TestFormatValue(unittest.TestCase):
    """Форматирование значений."""

    def test_formats(self):
        """Строки в кавычках, булевы в нижнем регистре."""
        self.assertEqual(cli.format_value("a"), '"a"')
        self.assertEqual(cli.format_value(True), "true")
        self.assertEqual(cli.format_value(False), "false")
        self.assertEqual(cli.format_value("ы"), '"ы"')


class TestEndToEnd(unittest.TestCase):
    """Запуск как отдельного процесса: python -m depviz."""

    def run_module(self, *args):
        """Запускает ``python -m depviz`` и возвращает результат.

        Args:
            *args: аргументы командной строки.

        Returns:
            Объект ``subprocess.CompletedProcess``.
        """
        env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))
        return subprocess.run(
            [sys.executable, "-m", "depviz", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            cwd=ROOT,
            check=False,
        )

    def test_default_config(self):
        """Конфигурация config.toml из корня репозитория валидна."""
        result = self.run_module()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('package_name = "express"', result.stdout)

    def test_test_mode_example(self):
        """Пример для тестового режима валиден."""
        result = self.run_module("-c", "examples/config_test_mode.toml")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("test_mode = true", result.stdout)

    def test_all_invalid_examples_fail(self):
        """Все примеры из examples/invalid завершаются ошибкой."""
        folder = os.path.join(ROOT, "examples", "invalid")
        names = sorted(os.listdir(folder))
        self.assertTrue(names)
        for name in names:
            with self.subTest(name=name):
                result = self.run_module("-c", f"examples/invalid/{name}")
                self.assertEqual(result.returncode, cli.EXIT_CONFIG_ERROR)
                self.assertIn("Ошибка конфигурации", result.stderr)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
