"""Тесты чтения и проверки конфигурации."""

import os
import tempfile
import unittest

from depviz.config import Config, build_config, load_config, read_toml
from depviz.errors import ConfigError
from helpers import VALID_TOML, write_temp

VALID_RAW = {
    "package_name": "express",
    "repository": "https://registry.npmjs.org",
    "test_mode": False,
    "version": "4.18.2",
    "output_file": "graph.png",
}


class TestReadToml(unittest.TestCase):
    """Чтение TOML-файла."""

    def test_reads_valid_file(self):
        """Корректный файл читается в словарь."""
        path = write_temp(self, VALID_TOML)
        self.assertEqual(read_toml(path), VALID_RAW)

    def test_missing_file(self):
        """Отсутствующий файл дает ConfigError."""
        with self.assertRaises(ConfigError) as ctx:
            read_toml("/no/such/config.toml")
        self.assertIn("не найден", ctx.exception.problems[0])

    def test_directory_instead_of_file(self):
        """Каталог вместо файла дает ConfigError."""
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ConfigError):
                read_toml(directory)

    def test_broken_syntax(self):
        """Синтаксическая ошибка TOML дает ConfigError."""
        path = write_temp(self, 'package_name = "express\n')
        with self.assertRaises(ConfigError) as ctx:
            read_toml(path)
        self.assertIn("некорректный TOML", ctx.exception.problems[0])

    def test_binary_garbage(self):
        """Не-UTF-8 содержимое дает ConfigError."""
        handle = tempfile.NamedTemporaryFile(suffix=".toml", delete=False)
        with handle:
            handle.write(b"\xff\xfe\x00\x80")
        self.addCleanup(os.remove, handle.name)
        with self.assertRaises(ConfigError):
            read_toml(handle.name)


class TestBuildConfig(unittest.TestCase):
    """Проверка словаря параметров."""

    def test_valid_config(self):
        """Корректные данные дают объект Config."""
        config = build_config(dict(VALID_RAW))
        self.assertEqual(config, Config(**VALID_RAW))

    def test_as_pairs_order(self):
        """Параметры перечисляются в фиксированном порядке."""
        keys = [key for key, _ in build_config(dict(VALID_RAW)).as_pairs()]
        self.assertEqual(keys, list(VALID_RAW))

    def test_missing_keys_reported(self):
        """Отсутствующие параметры перечисляются все сразу."""
        with self.assertRaises(ConfigError) as ctx:
            build_config({})
        self.assertEqual(len(ctx.exception.problems), len(VALID_RAW))

    def test_unknown_key(self):
        """Неизвестный параметр считается ошибкой."""
        raw = dict(VALID_RAW, extra=1)
        with self.assertRaises(ConfigError) as ctx:
            build_config(raw)
        self.assertEqual(
            ctx.exception.problems, ["неизвестный параметр: extra"]
        )

    def test_all_errors_collected(self):
        """Ошибки нескольких параметров собираются вместе."""
        raw = dict(
            VALID_RAW,
            package_name="Bad Name",
            version="latest",
            output_file="a.jpg",
        )
        with self.assertRaises(ConfigError) as ctx:
            build_config(raw)
        self.assertEqual(len(ctx.exception.problems), 3)

    def test_invalid_mode_skips_dependent_checks(self):
        """Неверный test_mode не порождает ложных ошибок других полей."""
        raw = dict(VALID_RAW, test_mode="yes")
        with self.assertRaises(ConfigError) as ctx:
            build_config(raw)
        self.assertEqual(len(ctx.exception.problems), 1)
        self.assertTrue(ctx.exception.problems[0].startswith("test_mode"))

    def test_test_mode_config(self):
        """Тестовый режим требует существующий файл репозитория."""
        repo = write_temp(self, "A:\n", suffix=".txt")
        raw = dict(
            VALID_RAW, package_name="A", repository=repo, test_mode=True
        )
        self.assertTrue(build_config(raw).test_mode)

    def test_test_mode_missing_repo_file(self):
        """Отсутствующий файл тестового репозитория - ошибка."""
        raw = dict(
            VALID_RAW,
            package_name="A",
            repository="/no/such/repo.txt",
            test_mode=True,
        )
        with self.assertRaises(ConfigError) as ctx:
            build_config(raw)
        self.assertTrue(ctx.exception.problems[0].startswith("repository"))


class TestLoadConfig(unittest.TestCase):
    """Загрузка конфигурации целиком."""

    def test_load_valid(self):
        """Корректный файл загружается."""
        path = write_temp(self, VALID_TOML)
        self.assertEqual(load_config(path).package_name, "express")

    def test_load_invalid(self):
        """Некорректное значение дает ConfigError."""
        path = write_temp(self, VALID_TOML.replace("4.18.2", "x"))
        with self.assertRaises(ConfigError):
            load_config(path)


if __name__ == "__main__":
    unittest.main()
