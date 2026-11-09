"""Вспомогательные функции для тестов."""

import os
import tempfile

VALID_TOML = """\
package_name = "express"
repository = "https://registry.npmjs.org"
test_mode = false
version = "4.18.2"
output_file = "graph.png"
"""


def write_temp(testcase, text, suffix=".toml"):
    """Создает временный файл, удаляемый по окончании теста.

    Args:
        testcase: экземпляр ``unittest.TestCase``.
        text: содержимое файла.
        suffix: расширение файла.

    Returns:
        Путь к созданному файлу.
    """
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=suffix, delete=False, encoding="utf-8"
    )
    with handle:
        handle.write(text)
    testcase.addCleanup(os.remove, handle.name)
    return handle.name
