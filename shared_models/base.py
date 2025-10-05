from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей.
    Все ORM-модели должны наследоваться от него.
    """
    pass
