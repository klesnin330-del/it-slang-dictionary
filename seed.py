from app import app
from models import db, User, Status, Category, Source, Term, Definition, Example, TermCategory, RelationType
from werkzeug.security import generate_password_hash

def seed_db():
    with app.app_context():
        # Удаляем старую базу и создаём новую
        db.drop_all()
        db.create_all()
        
        print("🌱 Создание справочников...")
        
        # Статусы
        draft = Status(name='Черновик', description='На модерации')
        pub = Status(name='Опубликован', description='Видно пользователям')
        db.session.add_all([draft, pub])
        
        # Категории
        cats = [
            Category(name='Разработка', description='Программирование'),
            Category(name='Инфраструктура', description='Серверы, DevOps'),
            Category(name='Тестирование', description='QA, баги'),
            Category(name='Менеджмент', description='Project management'),
            Category(name='DevOps', description='Непрерывная интеграция и доставка'),
            Category(name='AI/ML', description='Искусственный интеллект и машинное обучение'),
            Category(name='Безопасность', description='Информационная безопасность'),
            Category(name='Данные', description='Базы данных, аналитика')
        ]
        db.session.add_all(cats)
        
        # Типы связей
        relation_types = [
            RelationType(type_name='Синоним'),
            RelationType(type_name='Антоним'),
            RelationType(type_name='Родственное понятие')
        ]
        db.session.add_all(relation_types)
        
        # Источники
        sources = [
            Source(resource_name='Habr', source_type='Статья', url='https://habr.com'),
            Source(resource_name='Stack Overflow', source_type='Форум', url='https://stackoverflow.com'),
            Source(resource_name='VC.ru', source_type='Блог', url='https://vc.ru'),
            Source(resource_name='LinkedIn', source_type='Соцсеть', url='https://linkedin.com'),
            Source(resource_name='DevOps Handbook', source_type='Книга', url=None),
            Source(resource_name='GitHub', source_type='Репозиторий', url='https://github.com'),
            Source(resource_name='Medium', source_type='Блог', url='https://medium.com'),
            Source(resource_name='Reddit', source_type='Форум', url='https://reddit.com')
        ]
        db.session.add_all(sources)
        db.session.commit()
        
        # Админ
        admin = User(username='admin', password=generate_password_hash('admin123'), role='admin')
        db.session.add(admin)
        db.session.commit()
        
        published = Status.query.filter_by(name='Опубликован').first()
        habr = Source.query.filter_by(resource_name='Habr').first()
        stackoverflow = Source.query.filter_by(resource_name='Stack Overflow').first()
        vc = Source.query.filter_by(resource_name='VC.ru').first()
        github = Source.query.filter_by(resource_name='GitHub').first()
        devops = Source.query.filter_by(resource_name='DevOps Handbook').first()
        linkedin = Source.query.filter_by(resource_name='LinkedIn').first()
        medium = Source.query.filter_by(resource_name='Medium').first()
        
        print("📝 Загрузка терминов...")
        terms_data = [
            # Разработка
            {'name': 'Костыль', 'transcription': '[ка-сыл]', 'grammar': 'сущ., м.р.', 'origin_word': 'Crutch (метафора)', 'year': '2000–н.в.', 'def': 'Временное, некрасивое решение проблемы в коде.', 'ex': 'Пришлось подпереть базу костылём, потом переделаем.', 'cat': 'Разработка', 'src': habr},
            {'name': 'Дебажить', 'transcription': '[ди-ба-жыт]', 'grammar': 'гл., несов. вид', 'origin_word': 'Debug', 'year': '1990–н.в.', 'def': 'Искать и исправлять ошибки в коде.', 'ex': 'Буду дебажить этот модуль до ночи.', 'cat': 'Разработка', 'src': stackoverflow},
            {'name': 'Пилить', 'transcription': '[пи-лит]', 'grammar': 'гл., несов. вид', 'origin_word': 'Жаргон', 'year': '2005–н.в.', 'def': 'Долго и упорно разрабатывать фичу или проект.', 'ex': 'Пилим новый модуль уже третью неделю.', 'cat': 'Разработка', 'src': vc},
            {'name': 'Фича', 'transcription': '[фи-ча]', 'grammar': 'сущ., ж.р.', 'origin_word': 'Feature', 'year': '2000–н.в.', 'def': 'Полезная функция или возможность продукта.', 'ex': 'Это не баг, это фича!', 'cat': 'Разработка', 'src': habr},
            {'name': 'Хардкодить', 'transcription': '[хар-ко-дыт]', 'grammar': 'гл., несов. вид', 'origin_word': 'Hardcode', 'year': '1995–н.в.', 'def': 'Вписывать данные напрямую в код, вместо использования конфигов.', 'ex': 'Не хардкодь пароли в исходниках!', 'cat': 'Разработка', 'src': stackoverflow},
            {'name': 'Джун', 'transcription': '[джун]', 'grammar': 'сущ., м.р.', 'origin_word': 'Junior', 'year': '2010–н.в.', 'def': 'Начинающий специалист, разработчик без опыта.', 'ex': 'Взяли джуна на поддержку, пусть учится.', 'cat': 'Менеджмент', 'src': vc},
            {'name': 'Прод', 'transcription': '[прот]', 'grammar': 'сущ., м.р.', 'origin_word': 'Production', 'year': '2000–н.в.', 'def': 'Рабочий сервер, боевая среда.', 'ex': 'Не трогай прод без согласования!', 'cat': 'Инфраструктура', 'src': habr},
            {'name': 'Бэкап', 'transcription': '[бэ-кап]', 'grammar': 'сущ., м.р.', 'origin_word': 'Backup', 'year': '1980–н.в.', 'def': 'Резервная копия данных или системы.', 'ex': 'Сделай бэкап базы перед обновлением.', 'cat': 'Инфраструктура', 'src': stackoverflow},
            {'name': 'Легаси', 'transcription': '[ли-га-сы]', 'grammar': 'сущ., ср.р., нескл.', 'origin_word': 'Legacy', 'year': '2000–н.в.', 'def': 'Старый код или система, которые всё ещё используются.', 'ex': 'Пришлось лезть в легаси, чтобы понять логику.', 'cat': 'Разработка', 'src': vc},
            {'name': 'Мержить', 'transcription': '[мэр-жыт]', 'grammar': 'гл., несов. вид', 'origin_word': 'Merge', 'year': '2005–н.в.', 'def': 'Объединять ветки в системе контроля версий.', 'ex': 'Замержил свою ветку в master.', 'cat': 'Разработка', 'src': github},
            
            # DevOps и Инфраструктура
            {'name': 'Деплой', 'transcription': '[ди-плой]', 'grammar': 'сущ., м.р.', 'origin_word': 'Deploy', 'year': '2000–н.в.', 'def': 'Развёртывание приложения на сервере.', 'ex': 'Деплой запланирован на ночь.', 'cat': 'DevOps', 'src': devops},
            {'name': 'Контейнер', 'transcription': '[кан-тэй-нэр]', 'grammar': 'сущ., м.р.', 'origin_word': 'Container', 'year': '2013–н.в.', 'def': 'Изолированная среда для запуска приложений.', 'ex': 'Упаковали сервис в контейнер Docker.', 'cat': 'DevOps', 'src': github},
            {'name': 'Оркестрация', 'transcription': '[ар-кэ-стра-цы-я]', 'grammar': 'сущ., ж.р.', 'origin_word': 'Orchestration', 'year': '2014–н.в.', 'def': 'Автоматизация управления контейнерами.', 'ex': 'Kubernetes используется для оркестрации контейнеров.', 'cat': 'DevOps', 'src': devops},
            {'name': 'Си-Ай-Си-Ди', 'transcription': '[си-ай-си-ди]', 'grammar': 'аббр.', 'origin_word': 'Continuous Integration/Continuous Delivery', 'year': '2010–н.в.', 'def': 'Непрерывная интеграция и непрерывная доставка.', 'ex': 'Настроили CI/CD пайплайн для автоматического деплоя.', 'cat': 'DevOps', 'src': github},
            {'name': 'Мониторинг', 'transcription': '[ма-ни-то-рынк]', 'grammar': 'сущ., м.р.', 'origin_word': 'Monitoring', 'year': '2000–н.в.', 'def': 'Система наблюдения за состоянием сервисов.', 'ex': 'Настроили мониторинг всех микросервисов.', 'cat': 'Инфраструктура', 'src': habr},
            
            # Тестирование
            {'name': 'Баг', 'transcription': '[бак]', 'grammar': 'сущ., м.р.', 'origin_word': 'Bug', 'year': '1947–н.в.', 'def': 'Ошибка в программе или системе.', 'ex': 'Нашёл критический баг в продакшене.', 'cat': 'Тестирование', 'src': stackoverflow},
            {'name': 'Краш', 'transcription': '[краш]', 'grammar': 'сущ., м.р.', 'origin_word': 'Crash', 'year': '1990–н.в.', 'def': 'Аварийное завершение программы.', 'ex': 'Приложение крашится при вводе специальных символов.', 'cat': 'Тестирование', 'src': github},
            {'name': 'Фикс', 'transcription': '[фикс]', 'grammar': 'сущ., м.р.', 'origin_word': 'Fix', 'year': '1995–н.в.', 'def': 'Исправление ошибки.', 'ex': 'Выкатили фикс для бага с авторизацией.', 'cat': 'Тестирование', 'src': stackoverflow},
            {'name': 'Регрессия', 'transcription': '[рэ-грэ-сы-я]', 'grammar': 'сущ., ж.р.', 'origin_word': 'Regression', 'year': '2000–н.в.', 'def': 'Появление старой ошибки после изменений в коде.', 'ex': 'После рефакторинга случилась регрессия.', 'cat': 'Тестирование', 'src': habr},
            {'name': 'Юнит-тест', 'transcription': '[ю-нит тэст]', 'grammar': 'сущ., м.р.', 'origin_word': 'Unit test', 'year': '2000–н.в.', 'def': 'Тест для проверки отдельного модуля кода.', 'ex': 'Написал юнит-тесты для нового сервиса.', 'cat': 'Тестирование', 'src': github},
            
            # Менеджмент
            {'name': 'Сеньор', 'transcription': '[сэ-ньор]', 'grammar': 'сущ., м.р.', 'origin_word': 'Senior', 'year': '2005–н.в.', 'def': 'Опытный специалист, старший разработчик.', 'ex': 'Сеньор должен менторить джунов.', 'cat': 'Менеджмент', 'src': vc},
            {'name': 'Мидл', 'transcription': '[мидл]', 'grammar': 'сущ., м.р.', 'origin_word': 'Middle', 'year': '2010–н.в.', 'def': 'Специалист среднего уровня.', 'ex': 'Ищем мидла на Python.', 'cat': 'Менеджмент', 'src': linkedin},
            {'name': 'Техлид', 'transcription': '[тэх-лит]', 'grammar': 'сущ., м.р.', 'origin_word': 'Tech lead', 'year': '2010–н.в.', 'def': 'Технический лидер команды.', 'ex': 'Техлид отвечает за архитектурные решения.', 'cat': 'Менеджмент', 'src': linkedin},
            {'name': 'Дэдлайн', 'transcription': '[дэд-лайн]', 'grammar': 'сущ., м.р.', 'origin_word': 'Deadline', 'year': '2000–н.в.', 'def': 'Крайний срок выполнения задачи.', 'ex': 'Горит дэдлайн, нужно срочно доделывать.', 'cat': 'Менеджмент', 'src': vc},
            {'name': 'Роадмап', 'transcription': '[роуд-мэп]', 'grammar': 'сущ., м.р.', 'origin_word': 'Roadmap', 'year': '2015–н.в.', 'def': 'План развития продукта или проекта.', 'ex': 'Обновили роадмап на следующий квартал.', 'cat': 'Менеджмент', 'src': medium},
            
            # AI/ML
            {'name': 'Нейронка', 'transcription': '[нэ-рон-ка]', 'grammar': 'сущ., ж.р.', 'origin_word': 'Neural network (жарг.)', 'year': '2015–н.в.', 'def': 'Нейронная сеть, модель машинного обучения.', 'ex': 'Обучили нейронку распознавать изображения.', 'cat': 'AI/ML', 'src': medium},
            {'name': 'Дата-сэт', 'transcription': '[да-та сэт]', 'grammar': 'сущ., м.р.', 'origin_word': 'Dataset', 'year': '2010–н.в.', 'def': 'Набор данных для обучения модели.', 'ex': 'Собрали дата-сэт из миллиона изображений.', 'cat': 'AI/ML', 'src': github},
            {'name': 'Тренировать', 'transcription': '[трэ-ни-ра-ват]', 'grammar': 'гл., несов. вид', 'origin_word': 'Train', 'year': '2010–н.в.', 'def': 'Обучать модель машинного обучения.', 'ex': 'Тренируем модель уже третьи сутки.', 'cat': 'AI/ML', 'src': medium},
            {'name': 'Предикт', 'transcription': '[прэ-дикт]', 'grammar': 'сущ., м.р.', 'origin_word': 'Predict', 'year': '2015–н.в.', 'def': 'Предсказание модели, результат работы алгоритма.', 'ex': 'Модель выдала предикт с точностью 95%.', 'cat': 'AI/ML', 'src': medium},
            {'name': 'Оверфит', 'transcription': '[о-вэр-фит]', 'grammar': 'сущ., м.р.', 'origin_word': 'Overfitting', 'year': '2010–н.в.', 'def': 'Переобучение модели, когда она запоминает данные вместо обучения.', 'ex': 'Модель словила оверфит, нужно добавить регуляризацию.', 'cat': 'AI/ML', 'src': github},
            
            # Безопасность
            {'name': 'Эксплойт', 'transcription': '[экс-плойт]', 'grammar': 'сущ., м.р.', 'origin_word': 'Exploit', 'year': '2000–н.в.', 'def': 'Код или техника для использования уязвимости.', 'ex': 'Злоумышленники использовали эксплойт нулевого дня.', 'cat': 'Безопасность', 'src': habr},
            {'name': 'Пентест', 'transcription': '[пэн-тэст]', 'grammar': 'сущ., м.р.', 'origin_word': 'Penetration test', 'year': '2005–н.в.', 'def': 'Тестирование на проникновение, проверка безопасности.', 'ex': 'Заказали пентест у внешней компании.', 'cat': 'Безопасность', 'src': habr},
            {'name': 'Фишинг', 'transcription': '[фи-шынк]', 'grammar': 'сущ., м.р.', 'origin_word': 'Phishing', 'year': '1995–н.в.', 'def': 'Мошенничество для получения конфиденциальных данных.', 'ex': 'Пользователь попался на фишинг и отдал пароль.', 'cat': 'Безопасность', 'src': vc},
            {'name': 'Зеро-дей', 'transcription': '[зэ-ро дэй]', 'grammar': 'сущ., м.р.', 'origin_word': 'Zero-day vulnerability', 'year': '2000–н.в.', 'def': 'Уязвимость, о которой неизвестно производителю.', 'ex': 'Обнаружили зеро-дей уязвимость в браузере.', 'cat': 'Безопасность', 'src': github},
            {'name': 'Шифрование', 'transcription': '[шы-фра-ва-нэ]', 'grammar': 'сущ., ср.р.', 'origin_word': 'Encryption', 'year': '1970–н.в.', 'def': 'Преобразование данных в защищённый формат.', 'ex': 'Все данные хранятся с шифрованием.', 'cat': 'Безопасность', 'src': habr},
            
            # Данные
            {'name': 'Датапайплайн', 'transcription': '[да-та пайп-лайн]', 'grammar': 'сущ., м.р.', 'origin_word': 'Data pipeline', 'year': '2015–н.в.', 'def': 'Конвейер обработки данных.', 'ex': 'Построили датапайплайн для аналитики.', 'cat': 'Данные', 'src': medium},
            {'name': 'И-Ти-Эл', 'transcription': '[и-ти-эл]', 'grammar': 'аббр.', 'origin_word': 'Extract, Transform, Load', 'year': '1990–н.в.', 'def': 'Процесс извлечения, преобразования и загрузки данных.', 'ex': 'Настроили ETL-процесс для миграции данных.', 'cat': 'Данные', 'src': habr},
            {'name': 'Дашборд', 'transcription': '[дэш-борд]', 'grammar': 'сущ., м.р.', 'origin_word': 'Dashboard', 'year': '2005–н.в.', 'def': 'Интерактивная панель визуализации данных.', 'ex': 'Сделали дашборд для мониторинга метрик.', 'cat': 'Данные', 'src': vc},
            {'name': 'Алерт', 'transcription': '[а-лэрт]', 'grammar': 'сущ., м.р.', 'origin_word': 'Alert', 'year': '2000–н.в.', 'def': 'Уведомление о событии или проблеме.', 'ex': 'Пришёл алерт о падении сервиса.', 'cat': 'Инфраструктура', 'src': github},
            {'name': 'Миграция', 'transcription': '[ми-гра-цы-я]', 'grammar': 'сущ., ж.р.', 'origin_word': 'Migration', 'year': '2000–н.в.', 'def': 'Перенос данных или системы на новую платформу.', 'ex': 'Запланировали миграцию базы на PostgreSQL.', 'cat': 'Данные', 'src': stackoverflow},
            
            # Дополнительные термины
            {'name': 'Абишка', 'transcription': '[а-биш-ка]', 'grammar': 'сущ., ж.р.', 'origin_word': 'API (жарг.)', 'year': '2010–н.в.', 'def': 'Программный интерфейс приложения (жаргонное).', 'ex': 'Документируем нашу абишку для партнёров.', 'cat': 'Разработка', 'src': habr},
            {'name': 'Бэкенд', 'transcription': '[бэк-энд]', 'grammar': 'сущ., м.р.', 'origin_word': 'Backend', 'year': '2000–н.в.', 'def': 'Серверная часть приложения.', 'ex': 'Бэкенд написан на Python.', 'cat': 'Разработка', 'src': stackoverflow},
            {'name': 'Фронтенд', 'transcription': '[фронт-энд]', 'grammar': 'сущ., м.р.', 'origin_word': 'Frontend', 'year': '2000–н.в.', 'def': 'Клиентская часть приложения, интерфейс.', 'ex': 'Фронтенд делаем на React.', 'cat': 'Разработка', 'src': github},
            {'name': 'Фуллстек', 'transcription': '[фулл-стэк]', 'grammar': 'сущ., м.р.', 'origin_word': 'Fullstack', 'year': '2010–н.в.', 'def': 'Разработчик, работающий и с фронтендом, и с бэкендом.', 'ex': 'Нам нужен фуллстек на JavaScript.', 'cat': 'Разработка', 'src': linkedin},
            {'name': 'Рефакторинг', 'transcription': '[ри-фак-то-рынк]', 'grammar': 'сущ., м.р.', 'origin_word': 'Refactoring', 'year': '2000–н.в.', 'def': 'Улучшение структуры кода без изменения функциональности.', 'ex': 'Сделали рефакторинг старого модуля.', 'cat': 'Разработка', 'src': habr},
            {'name': 'Депрекитед', 'transcription': '[дэ-при-кэй-тэд]', 'grammar': 'прил.', 'origin_word': 'Deprecated', 'year': '2000–н.в.', 'def': 'Устаревший, не рекомендуемый к использованию.', 'ex': 'Этот метод помечен как депрекитед.', 'cat': 'Разработка', 'src': stackoverflow},
            {'name': 'Хардкод', 'transcription': '[хар-код]', 'grammar': 'сущ., м.р.', 'origin_word': 'Hardcode', 'year': '1995–н.в.', 'def': 'Данные, вшитые прямо в код.', 'ex': 'В конфиге был хардкод, пришлось выносить.', 'cat': 'Разработка', 'src': github},
            {'name': 'Воркфлоу', 'transcription': '[ворк-флоу]', 'grammar': 'сущ., м.р.', 'origin_word': 'Workflow', 'year': '2010–н.в.', 'def': 'Рабочий процесс, последовательность действий.', 'ex': 'Оптимизировали воркфлоу разработки.', 'cat': 'Менеджмент', 'src': medium},
            {'name': 'Апрув', 'transcription': '[а-прув]', 'grammar': 'сущ., м.р.', 'origin_word': 'Approve', 'year': '2010–н.в.', 'def': 'Одобрение, утверждение.', 'ex': 'Ждём апрув от тимлида на мерж.', 'cat': 'Менеджмент', 'src': github},
            {'name': 'Блокер', 'transcription': '[бло-кер]', 'grammar': 'сущ., м.р.', 'origin_word': 'Blocker', 'year': '2005–н.в.', 'def': 'Проблема, блокирующая работу.', 'ex': 'Этот баг — блокер для релиза.', 'cat': 'Менеджмент', 'src': vc}
        ]

        for t_data in terms_data:
            cat = Category.query.filter_by(name=t_data['cat']).first()
            
            term = Term(
                term_name=t_data['name'],
                transcription=t_data.get('transcription'),
                grammar_notes=t_data.get('grammar'),
                origin_word=t_data.get('origin_word'),
                year_fixed=t_data.get('year'),
                user_id=admin.id,
                status_id=published.id,
                source_id=t_data['src'].id if t_data['src'] else None
            )
            db.session.add(term)
            db.session.flush()

            definition = Definition(term_id=term.id, definition_text=t_data['def'])
            db.session.add(definition)
            db.session.flush()

            db.session.add(Example(definition_id=definition.id, example_text=t_data['ex']))
            
            if cat:
                db.session.add(TermCategory(term_id=term.id, category_id=cat.id))

        db.session.commit()
        print(f"✅ Готово! {len(terms_data)} терминов загружено.")

if __name__ == '__main__':
    seed_db()