from app import app
from models import db, User, Status, Category, Source, Term, Definition, Example, TermCategory
from werkzeug.security import generate_password_hash

def seed_db():
    with app.app_context():
        db.create_all()
        if User.query.first():
            print("✅ База уже существует. Пропускаем.")
            return

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
            Category(name='Менеджмент', description='Project management')
        ]
        db.session.add_all(cats)
        
        # Источники (теперь создаем ОТДЕЛЬНО)
        sources = [
            Source(resource_name='Habr', source_type='Статья', url='https://habr.com'),
            Source(resource_name='Stack Overflow', source_type='Форум', url='https://stackoverflow.com'),
            Source(resource_name='VC.ru', source_type='Блог', url='https://vc.ru'),
            Source(resource_name='LinkedIn', source_type='Соцсеть', url='https://linkedin.com'),
            Source(resource_name='DevOps Handbook', source_type='Книга', url=None)
        ]
        db.session.add_all(sources)
        db.session.commit()  # Важно: commit чтобы получить ID источников
        
        # Админ
        admin = User(username='admin', password=generate_password_hash('admin123'), role='admin')
        db.session.add(admin)
        db.session.commit()
        
        published = Status.query.filter_by(name='Опубликован').first()
        habr = Source.query.filter_by(resource_name='Habr').first()
        stackoverflow = Source.query.filter_by(resource_name='Stack Overflow').first()
        vc = Source.query.filter_by(resource_name='VC.ru').first()
        
        print("📝 Загрузка терминов...")
        terms_data = [
            {'name': 'Костыль', 'origin': 'Метафора', 'def': 'Временное, некрасивое решение.', 'ex': 'Пришлось подпереть базу костылем.', 'cat': 'Разработка', 'src': habr},
            {'name': 'Дебажить', 'origin': 'Англ. Debug', 'def': 'Искать и исправлять ошибки.', 'ex': 'Буду дебажить весь вечер.', 'cat': 'Разработка', 'src': stackoverflow},
            {'name': 'Пилить', 'origin': 'Жаргон', 'def': 'Долго разрабатывать фичу.', 'ex': 'Пилим модуль уже неделю.', 'cat': 'Разработка', 'src': vc},
            {'name': 'Фича', 'origin': 'Англ. Feature', 'def': 'Полезная функция.', 'ex': 'Это не баг, это фича.', 'cat': 'Разработка', 'src': habr},
            {'name': 'Хардкодить', 'origin': 'Англ. Hardcode', 'def': 'Вписывать данные в код.', 'ex': 'Не хардкодь пароли.', 'cat': 'Разработка', 'src': stackoverflow},
            {'name': 'Джун', 'origin': 'Англ. Junior', 'def': 'Начинающий специалист.', 'ex': 'Взяли джуна на поддержку.', 'cat': 'Менеджмент', 'src': vc},
            {'name': 'Прод', 'origin': 'Англ. Production', 'def': 'Рабочий сервер.', 'ex': 'Не трогай прод!', 'cat': 'Инфраструктура', 'src': habr},
            {'name': 'Бэкап', 'origin': 'Англ. Backup', 'def': 'Резервная копия.', 'ex': 'Сделай бэкап базы.', 'cat': 'Инфраструктура', 'src': stackoverflow},
            {'name': 'Легаси', 'origin': 'Англ. Legacy', 'def': 'Старый код.', 'ex': 'Пришлось лезть в легаси.', 'cat': 'Разработка', 'src': vc},
            {'name': 'Мержить', 'origin': 'Англ. Merge', 'def': 'Объединять ветки.', 'ex': 'Замержил в master.', 'cat': 'Разработка', 'src': habr}
        ]

        for t_data in terms_data:
            cat = Category.query.filter_by(name=t_data['cat']).first()
            
            term = Term(
                term_name=t_data['name'],
                origin=t_data['origin'],
                user_id=admin.id,
                status_id=published.id,
                source_id=t_data['src'].id  # Привязываем источник
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
        print("✅ Готово! 10 терминов загружено.")

if __name__ == '__main__':
    seed_db()