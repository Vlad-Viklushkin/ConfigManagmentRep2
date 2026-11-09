"""Исключения приложения."""


class ConfigError(Exception):
    """Ошибка чтения или проверки конфигурации.

    Хранит список всех найденных проблем, чтобы пользователь мог
    исправить их за один раз.
    """

    def __init__(self, problems):
        """Создает исключение.

        Args:
            problems: итерируемый набор текстовых описаний проблем.
        """
        self.problems = list(problems)
        super().__init__("; ".join(self.problems))
