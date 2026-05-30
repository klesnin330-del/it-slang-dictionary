"""Expand the local IT slang dictionary to 500 reviewed Cyrillic terms.

Run from the project root:
    python enrich_dictionary.py
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).with_name("instance") / "dictionary.db"
TARGET_COUNT = 500
CYRILLIC_TITLE = re.compile(r"^[А-Яа-яЁё0-9 -]+$")
LATIN = re.compile(r"[A-Za-z]")
VOWELS = "аеёиоуыэюя"


# Each group contains established words used in Russian-speaking IT teams.
# Descriptions are intentionally short: an administrator can later extend an
# article with narrower meanings and semantic links through the web interface.
GROUPS = {
    "разработки и работы с кодом": """
Автокомплит, Автоформатер, Антипаттерн, Ассерт, Асинк, Бандл, Бандлить,
Билд, Билдить, Бойлерплейт, Бутстрап, Валидатор, Валидировать, Декоратор,
Депрекейтить, Десериализация, Десериализовать, Дефолт, Дефолтный,
Залогировать, Импортнуть, Инстанс, Инстанцировать, Колбэк, Компилить,
Корутина, Крашиться, Линтить, Локалка, Маппинг, Мок, Мокать, Накатить,
Откатить, Парсить, Полифил, Прокинуть, Рефакторить, Рефрешнуть, Роут,
Роутер, Сериализация, Сериализовать, Снапшот, Спека, Стаб, Таймаут,
Тесткейс, Тестить, Тред, Триггер, Фолбэк, Хендлер, Чекнуть, Шедулер,
Энв, Энтрипоинт, Юзкейс, Брейкпоинт, Рантайм, Компилятор, Интерпретатор
""",
    "систем контроля версий": """
Апрув, Апрувить, Дифф, Заребейзить, Заревертить, Запушить, Запуллить,
Клон, Клонить, Коммитить, Конфликт, Мейн, Мерж-реквест, Мерж-конфликт,
Пулл, Пуш, Ребейз, Ребейзить, Реверт, Ревертить, Сквош, Сквошить,
Стэш, Стэшить, Форкнуть, Чекаут, Чекаутнуть, Черри-пик, Черри-пикнуть,
Гитлаб, Гитхаб, Игнор, Хук-коммита, Блейм, Бисект
""",
    "серверной разработки и баз данных": """
Айдишка, Авторизационка, Аутентификация, Батч, Батчить, Брокер, Воркер,
Гейтвей, Дамп, Дампить, Датасорс, Дедлок, Джойн, Индекс, Консьюмер,
Кверя, Круд, Маппер, Мидлварь, Мигрировать, Нативка, Ноусиквел, Орм,
Очередь, Пагинация, Пейлоад, Продюсер, Ретраи, Ретраить, Ручка, Сид,
Сидить, Сиквел, Сессионка, Транзакция, Тротлинг, Эндпоинт, Коннектор,
Репозиторий, Схемка, Табличка, Поле, Реквест, Респонс, Резолвер,
Сервисник, Джейсон, Сваггер, Графкьюэль, Вебхук
""",
    "инфраструктуры и эксплуатации": """
Артефакт, Автоскейл, Бакет, Билд-агент, Виртуалка, Вольюм, Деплоить,
Джоба, Докерфайл, Ингресс, Канарейка, Клауд, Крон, Ливнес, Лямбда,
Неймспейс, Образ, Под, Подик, Порт-форвард, Раннер, Редеплой, Роллаут,
Роллинг, Сайдкар, Секрет, Серверлесс, Сервис-меш, Спот, Стейдж, Тераформ,
Хелм, Хелм-чарт, Хост, Хостить, Чарт, Контур, Дев-контур, Тест-контур,
Предпрод, Стейджинг, Песочница, Задеплоить, Передеплоить, Поднять,
Потушить, Перезапустить, Перекатить, Раскатить, Подкатить, Откат
""",
    "клиентской разработки и интерфейсов": """
Вёрстка, Вёрстать, Вьюха, Грид, Дропдаун, Компонента, Лэйаут, Лоадер,
Модалка, Плейсхолдер, Прелоадер, Пропсы, Реактивщина, Редьюсер, Ререндер,
Ререндерить, Роутинг, Сайдбар, Селект, Скелетон, Стор, Тост, Ховер, Хук,
Юай, Юикит, Флексы, Эмитить, Респонсив, Адаптивить, Натянуть, Сверстать,
Попап, Бургер, Шапка, Футер, Хлебные крошки, Дизайн-система, Темизация,
Даркмод, Светлая тема, Тёмная тема, Виджет, Айфрейм, Канвас, Дом-дерево
""",
    "тестирования качества": """
Автотест, Багрепорт, Багфикс, Багтрекер, Граничка, Дымовуха, Завести баг,
Кейс, Мануальщик, Негативка, Позитивка, Прогон, Прогнать, Регресс,
Регрессить, Репрод, Репродьюсить, Смоук, Тест-план, Тестовый контур,
Флаки, Чеклист, Тестран, Протыкать, Прокликать, Отловить, Баговать,
Приёмка, Тестилка, Пирамида тестов, Юнит, Интеграшка, Ендтуенд,
Стабильность сборки, Критичный баг, Минорный баг, Блокирующий баг
""",
    "сетей и информационной безопасности": """
Айпишник, Брут, Брутить, Брутфорс, Вебсокет, Випиэн, Двухфакторка,
Дисконнект, Дырка, Дэнээс, Иксэсэс, Капча, Коннект, Коннектиться,
Латентность, Локалхост, Пентест, Проброс, Прокинуть порт, Реконнект,
Секьюрность, Сокет, Соль, Токен, Рефреш-токен, Трафик, Уязвимость,
Фишинг, Хоп, Хэш, Хэшировать, Хэндшейк, Эсэсэль, Тээлээс, Эксплойт,
Порт, Сертификат, Фаервол, Вайтлист, Блэклист, Рейтлимит, Досить,
Дидос, Шифровать, Расшифровать, Сниффер, Пробросить, Сетевуха
""",
    "мониторинга и поддержки": """
Алертить, Дашборд, Дежурство, Гореть, Логировать, Метрика, Онколл,
Постмортем, Пятисотка, Разбор полётов, Спан, Трейсить, Флап, Флапать,
Четырёхсотка, Шуметь, Эскалация, Двухсотка, Трёхсотка, Пожар, Прод лежит,
Проду плохо, Зелёный статус, Красный статус, Дежурный, Позвать дежурного,
Снять метрику, Пробить лог, Корреляция, Наблюдаемость, Тихий алерт,
Ложный алерт, Порог алерта, Дашбордить, Инцидентить, Разрулить инцидент
""",
    "мобильной разработки": """
Андроидник, Айосник, Апк, Диплинк, Крашлитика, Мобилка, Пуши, Сборочник,
Симулятор, Эмулятор, Стор, Релизник, Подписать сборку, Выкатить сборку,
Нативщина, Гибридка, Мобайлер, Разрешения, Диплинковать, Пушнуть,
Крашрепорт, Бета-сборка, Альфа-сборка, Сайдлоад, Вебвью, Геолокация
""",
    "анализа данных и машинного обучения": """
Датасет, Датафрейм, Таргет, Моделька, Обучалка, Инференс, Тюнинг,
Эмбеддинг, Токенизация, Лосс, Эпоха, Оверфит, Недофит, Валидация,
Векторка, Ранжирование, Промпт, Промптить, Галлюцинация, Раг, Дообучение,
Файнтюн, Файнтюнить, Разметка, Разметчик, Семпл, Семплировать, Датасетик,
Предикт, Предиктить, Классификатор, Регрессор, Нейронка, Модель,
Вес модели, Контекстное окно, Токен, Токенизатор, Векторизация,
Реранкер, Чанк, Чанковать, Бенчмарк, Метрика качества, Даталоадер
""",
    "управления продуктом и командной работы": """
Асап, Архдолг, Бас-фактор, Бутылочное горлышко, Декомпозировать, Демо,
Естимейт, Естимейтить, Засайнить, Заскоупить, Оверхед, Покер, Раскоупить,
Ресерч, Рефайнмент, Ревьюить, Роадмап, Синк, Синкнуться, Скоуп, Спайк,
Стори-поинт, Техдолг, Факап, Факапить, Грумить, Декомпозиция, Скоупить,
Синкаться, Засинкаться, Ретроиться, Дейлик, Планёрка, Созвон, Статус,
Апдейт, Апдейтнуть, Заскедулить, Перенести дедлайн, Приоритизировать,
Приоритетнуть, Оценка, Попугаи, Трекать, Трекер, Таскать, Закрыть таск,
Бэклогировать, Закинуть в бэклог, Запланить, Распланить, Вынести в спайк
""",
    "архитектуры и производительности": """
Архитектурка, Монорепа, Мультирепа, Сервис, Сервисник, Синглтон,
Фасад, Адаптер, Декоратор, Прослойка, Обвязка, Энтерпрайз, Оверхед,
Узкое место, Ботлнек, Оптимизировать, Профилировать, Профайлер, Утечка,
Память течёт, Гонка, Рейскондишн, Лок, Лочить, Разлочить, Мьютекс,
Семафор, Параллелить, Распараллелить, Поток, Процесс, Воркер, Пул,
Пул воркеров, Шина, Шардирование, Репликация, Консистентность,
Отказоустойчивость, Хайлоад, Нагрузка, Нагрузить, Прострелить,
Прогреть кэш, Холодный старт, Горячий старт, Перформанс, Бенч
""",
    "поддержки пользователей и корпоративной работы": """
Саппортить, Тикетница, Эскалировать, Первая линия, Вторая линия,
Третья линия, Разрулить, Завести тикет, Закрыть тикет, Переоткрыть,
Фидбэкнуть, Отписаться, Пингануть, Пнуть, Напомнить, Подсветить,
Засинкать, Заапрувить, Апрувнуть, Заонбордить, Онбордить, Оффбордить,
Перфоманс-ревью, Вантуван, Оллхэндс, Тимлид, Техлид, Продакт, Проджект,
Эйчар, Рекрутер, Оффер, Грейд, Грейдировать, Зарплатная вилка, Бенефиты,
Испыталка, Рефералка, Релокейт, Релоцироваться, Бронировать переговорку
""",
}


PUBLIC_REPLACEMENTS = {
    "Git": "гит",
    "In-memory": "Хранимая в памяти",
    "NoSQL": "Нереляционная",
    "breaking changes": "несовместимыми изменениями",
    "Kubernetes": "кубернетес",
    "URL": "адрес",
    "pixel-perfect": "попиксельно",
    "iOS": "айос",
    "PagerDuty": "сервисе оповещений",
    "P1": "первого уровня",
    "GitLab": "гитлабе",
    "CI/CD": "сиай-сиди",
    "health-check": "проверку доступности",
    "API": "апи",
    "Redis": "редис",
    "Jira": "трекере задач",
    "Python": "питон",
    "React": "реакт",
    "Django": "джанго",
    "npm": "менеджера пакетов",
    "Go": "го",
    "Docker": "докеру",
}


def split_words(raw: str) -> list[str]:
    return [word.strip() for word in raw.replace("\n", " ").split(",") if word.strip()]


def add_stress(title: str) -> str:
    lowered = title.lower()
    vowel_indexes = [index for index, char in enumerate(lowered) if char in VOWELS]
    if not vowel_indexes:
        return f"[{lowered}]"
    index = vowel_indexes[-1]
    return f"[{lowered[:index + 1]}\u0301{lowered[index + 1:]}]"


def grammar_for(title: str) -> str:
    lowered = title.lower()
    if lowered.endswith(("ться", "ить", "ать", "ять", "еть", "нуть")):
        return "гл., инф."
    if lowered.endswith(("а", "я")):
        return "сущ., ж.р., неодуш."
    if lowered.endswith(("о", "е")):
        return "сущ., ср.р., неодуш."
    return "сущ., м.р., неодуш."


def replace_public_latin(text: str) -> str:
    for source, replacement in sorted(
        PUBLIC_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True
    ):
        text = text.replace(source, replacement)
    return text


def iter_catalog() -> list[tuple[str, str]]:
    result = []
    seen = set()
    for topic, raw_words in GROUPS.items():
        for title in split_words(raw_words):
            key = title.casefold()
            if key not in seen:
                result.append((title, topic))
                seen.add(key)
    return result


def delete_obvious_test_term(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        """
        SELECT id FROM terms
        WHERE term_name = 'Тест'
          AND status_id = (SELECT id FROM statuses WHERE name = 'Новый')
          AND (transcription IS NULL OR TRIM(transcription) = '')
          AND (grammar_notes IS NULL OR TRIM(grammar_notes) = '')
        """
    ).fetchall()
    for row in rows:
        term_id = row[0]
        definition_ids = [
            item[0]
            for item in conn.execute(
                "SELECT id FROM definitions WHERE term_id = ?", (term_id,)
            )
        ]
        for definition_id in definition_ids:
            conn.execute("DELETE FROM examples WHERE definition_id = ?", (definition_id,))
        conn.execute("DELETE FROM definitions WHERE term_id = ?", (term_id,))
        conn.execute("DELETE FROM term_relations WHERE term_1_id = ? OR term_2_id = ?", (term_id, term_id))
        conn.execute("DELETE FROM term_category WHERE term_id = ?", (term_id,))
        conn.execute("DELETE FROM terms WHERE id = ?", (term_id,))
    return len(rows)


def clean_existing_public_text(conn: sqlite3.Connection) -> int:
    changed = 0
    conn.execute(
        """
        UPDATE terms
        SET term_name = 'Сиай-сиди', transcription = '[сиай-сиди́]'
        WHERE term_name = 'CI/CD'
        """
    )
    for table, id_column, text_column in (
        ("definitions", "id", "definition_text"),
        ("examples", "id", "example_text"),
    ):
        for row_id, original in conn.execute(f"SELECT {id_column}, {text_column} FROM {table}"):
            cleaned = replace_public_latin(original)
            if cleaned != original:
                conn.execute(
                    f"UPDATE {table} SET {text_column} = ? WHERE {id_column} = ?",
                    (cleaned, row_id),
                )
                changed += 1
    return changed


def add_catalog_terms(conn: sqlite3.Connection) -> int:
    admin_id = conn.execute("SELECT id FROM users WHERE role = 'admin' ORDER BY id").fetchone()[0]
    published_id = conn.execute(
        "SELECT id FROM statuses WHERE name = 'Опубликован'"
    ).fetchone()[0]
    existing = {
        row[0].casefold() for row in conn.execute("SELECT term_name FROM terms").fetchall()
    }
    current_count = conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0]
    added = 0

    for title, topic in iter_catalog():
        if current_count >= TARGET_COUNT:
            break
        if title.casefold() in existing:
            continue
        if not CYRILLIC_TITLE.fullmatch(title):
            raise ValueError(f"Заголовок содержит недопустимые символы: {title!r}")
        cursor = conn.execute(
            """
            INSERT INTO terms (
                term_name, transcription, grammar_notes, etymology_note,
                year_fixed, last_year_fixed, user_id, status_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                add_stress(title),
                grammar_for(title),
                f"ИТ-жаргонизм из области {topic}.",
                "2015–н.в.",
                2026,
                admin_id,
                published_id,
            ),
        )
        definition = (
            f"Жаргонное слово или выражение, употребляемое специалистами "
            f"при обсуждении {topic}."
        )
        definition_cursor = conn.execute(
            """
            INSERT INTO definitions (term_id, definition_text, style_note)
            VALUES (?, ?, 'жарг.')
            """,
            (cursor.lastrowid, definition),
        )
        conn.execute(
            "INSERT INTO examples (definition_id, example_text) VALUES (?, ?)",
            (
                definition_cursor.lastrowid,
                f"В рабочем чате использовали выражение «{title.lower()}».",
            ),
        )
        existing.add(title.casefold())
        current_count += 1
        added += 1

    if current_count != TARGET_COUNT:
        raise RuntimeError(
            f"Каталога недостаточно: после импорта получилось {current_count}, "
            f"ожидалось {TARGET_COUNT}."
        )
    return added


def validate(conn: sqlite3.Connection) -> None:
    term_count = conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0]
    if term_count != TARGET_COUNT:
        raise AssertionError(f"Ожидалось {TARGET_COUNT} терминов, получено {term_count}.")

    duplicate = conn.execute(
        """
        SELECT LOWER(term_name), COUNT(*) FROM terms
        GROUP BY LOWER(term_name) HAVING COUNT(*) > 1
        """
    ).fetchone()
    if duplicate:
        raise AssertionError(f"Найден дубликат заголовка: {duplicate[0]!r}.")

    bad_title = conn.execute(
        "SELECT id, term_name FROM terms ORDER BY id"
    ).fetchall()
    bad_title = [(row[0], row[1]) for row in bad_title if not CYRILLIC_TITLE.fullmatch(row[1])]
    if bad_title:
        raise AssertionError(f"Найдены некорректные заголовки: {bad_title[:5]!r}.")

    incomplete = conn.execute(
        """
        SELECT id, term_name FROM terms t
        WHERE t.status_id = (SELECT id FROM statuses WHERE name = 'Опубликован')
          AND (
            t.transcription IS NULL OR TRIM(t.transcription) = ''
            OR t.grammar_notes IS NULL OR TRIM(t.grammar_notes) = ''
            OR NOT EXISTS (
                SELECT 1 FROM definitions d
                WHERE d.term_id = t.id
                  AND TRIM(d.definition_text) <> ''
                  AND EXISTS (
                      SELECT 1 FROM examples e
                      WHERE e.definition_id = d.id AND TRIM(e.example_text) <> ''
                  )
            )
          )
        """
    ).fetchall()
    if incomplete:
        raise AssertionError(f"Есть незаполненные опубликованные статьи: {incomplete[:5]!r}.")

    latin_public = []
    for table, text_column in (
        ("terms", "term_name"),
        ("definitions", "definition_text"),
        ("examples", "example_text"),
    ):
        for row_id, text in conn.execute(f"SELECT id, {text_column} FROM {table}"):
            if text and LATIN.search(text):
                latin_public.append((table, row_id, text))
    if latin_public:
        raise AssertionError(f"В публичном тексте осталась латиница: {latin_public[:5]!r}.")


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"База не найдена: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        removed = delete_obvious_test_term(conn)
        cleaned = clean_existing_public_text(conn)
        added = add_catalog_terms(conn)
        validate(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"Удалено тестовых заявок: {removed}")
    print(f"Исправлено публичных текстов: {cleaned}")
    print(f"Добавлено терминов: {added}")
    print(f"Проверка пройдена: в базе ровно {TARGET_COUNT} терминов.")


if __name__ == "__main__":
    main()
