"""Тесты проверок отдельных параметров."""

import os
import tempfile
import unittest

from depviz import validators


class TestTestMode(unittest.TestCase):
    """Проверка параметра test_mode."""

    def test_accepts_bool(self):
        """Булевы значения принимаются."""
        self.assertTrue(validators.validate_test_mode(True))
        self.assertFalse(validators.validate_test_mode(False))

    def test_rejects_other_types(self):
        """Строки и числа отклоняются."""
        for value in ("true", 1, 0, None, []):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validators.validate_test_mode(value)


class TestPackageName(unittest.TestCase):
    """Проверка параметра package_name."""

    def test_valid_npm_names(self):
        """Корректные npm-имена принимаются."""
        for name in ("express", "left-pad", "@babel/core", "a.b_c"):
            with self.subTest(name=name):
                self.assertEqual(
                    validators.validate_package_name(name, False), name
                )

    def test_invalid_npm_names(self):
        """Некорректные npm-имена отклоняются."""
        for name in ("Bad", "a b", "_x", ".x", "@scope", "x/y", "é"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validators.validate_package_name(name, False)

    def test_too_long_name(self):
        """Слишком длинное имя отклоняется."""
        name = "a" * (validators.MAX_NPM_NAME_LENGTH + 1)
        with self.assertRaises(ValueError):
            validators.validate_package_name(name, False)

    def test_test_mode_names(self):
        """В тестовом режиме допустимы только большие латинские буквы."""
        self.assertEqual(validators.validate_package_name("A", True), "A")
        for name in ("a", "A1", "express", "A B"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validators.validate_package_name(name, True)

    def test_empty_and_wrong_type(self):
        """Пустые и нестроковые значения отклоняются."""
        for value in ("", "   ", 5, None, True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validators.validate_package_name(value, False)

    def test_unknown_mode_checks_only_type(self):
        """Если режим неизвестен, формат имени не проверяется."""
        self.assertEqual(validators.validate_package_name("Any", None), "Any")


class TestRepository(unittest.TestCase):
    """Проверка параметра repository."""

    def test_valid_urls(self):
        """http и https адреса принимаются."""
        for url in ("https://registry.npmjs.org", "http://localhost:4873"):
            with self.subTest(url=url):
                self.assertEqual(
                    validators.validate_repository(url, False), url
                )

    def test_invalid_urls(self):
        """Не-URL и чужие схемы отклоняются."""
        for url in ("ftp://x.org", "registry.npmjs.org", "https://", "/tmp"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validators.validate_repository(url, False)

    def test_existing_file_in_test_mode(self):
        """Существующий файл принимается в тестовом режиме."""
        with tempfile.NamedTemporaryFile() as handle:
            self.assertEqual(
                validators.validate_repository(handle.name, True),
                handle.name,
            )

    def test_missing_file_in_test_mode(self):
        """Несуществующий файл отклоняется в тестовом режиме."""
        with self.assertRaises(ValueError):
            validators.validate_repository("/no/such/file.txt", True)

    def test_directory_is_not_file(self):
        """Каталог не считается файлом тестового репозитория."""
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                validators.validate_repository(directory, True)

    def test_url_is_not_file_in_test_mode(self):
        """URL не принимается в тестовом режиме."""
        with self.assertRaises(ValueError):
            validators.validate_repository("https://registry.npmjs.org", True)


class TestVersion(unittest.TestCase):
    """Проверка параметра version."""

    def test_valid_versions(self):
        """Корректные SemVer-версии принимаются."""
        for version in ("1.2.3", "0.0.1", "1.0.0-beta.1", "2.0.0+build.5"):
            with self.subTest(version=version):
                self.assertEqual(validators.validate_version(version), version)

    def test_invalid_versions(self):
        """Некорректные версии отклоняются."""
        for version in ("1.2", "latest", "01.2.3", "1.2.3.4", "v1.2.3", ""):
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    validators.validate_version(version)

    def test_wrong_type(self):
        """Число вместо строки отклоняется."""
        with self.assertRaises(ValueError):
            validators.validate_version(1.2)


class TestOutputFile(unittest.TestCase):
    """Проверка параметра output_file."""

    def test_valid_names(self):
        """Имена с расширением .png принимаются."""
        with tempfile.TemporaryDirectory() as directory:
            nested = os.path.join(directory, "g.png")
            for name in ("graph.png", "GRAPH.PNG", nested):
                with self.subTest(name=name):
                    self.assertEqual(
                        validators.validate_output_file(name), name
                    )

    def test_wrong_extension(self):
        """Другие расширения отклоняются."""
        for name in ("graph.jpg", "graph", "graph.png.txt"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validators.validate_output_file(name)

    def test_empty_basename(self):
        """Имя без основной части отклоняется."""
        for name in (".png", "dir/.png"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validators.validate_output_file(name)

    def test_missing_directory(self):
        """Несуществующий каталог отклоняется."""
        with self.assertRaises(ValueError):
            validators.validate_output_file("no_such_dir/graph.png")


if __name__ == "__main__":
    unittest.main()
