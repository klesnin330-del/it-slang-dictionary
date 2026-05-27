from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ==========================================
# СПРАВОЧНЫЕ И СЛУЖЕБНЫЕ ТАБЛИЦЫ
# ==========================================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='moderator')

class Status(db.Model):
    __tablename__ = 'statuses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(300))
    # Связь M:N с терминами через промежуточную таблицу
    terms = db.relationship('Term', secondary='term_category', backref='categories', lazy='dynamic')

class Source(db.Model):
    __tablename__ = 'sources'
    id = db.Column(db.Integer, primary_key=True)
    resource_name = db.Column(db.String(100), nullable=False)
    source_type = db.Column(db.String(50))
    url = db.Column(db.String(500))
    
    # ВАЖНО: Один источник может быть связан с МНОГИМИ терминами
    terms = db.relationship('Term', backref='source', lazy=True)

class RelationType(db.Model):
    __tablename__ = 'relation_types'
    id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(50), unique=True, nullable=False)

# ==========================================
# ОСНОВНЫЕ СЛОВАРНЫЕ ТАБЛИЦЫ
# ==========================================

class Term(db.Model):
    __tablename__ = 'terms'
    id = db.Column(db.Integer, primary_key=True)
    term_name = db.Column(db.String(200), nullable=False, index=True)
    transcription = db.Column(db.String(100))  # Транскрипция произношения
    grammar_notes = db.Column(db.String(100))  # Грамматические пометы
    origin_word = db.Column(db.String(300))  # Исходное слово / заимствование
    etymology_note = db.Column(db.Text)  # Этимологическая справка
    year_fixed = db.Column(db.String(50))  # Годы фиксации термина (диапазон)
    last_year_fixed = db.Column(db.Integer)  # Последний год фиксации жаргонного слова
    origin = db.Column(db.String(300))  # Старое поле, оставляем для совместимости
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Внешние ключи
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'), nullable=False)
    status = db.relationship('Status', backref='terms')
    
    source_id = db.Column(db.Integer, db.ForeignKey('sources.id'), nullable=True)
    definitions = db.relationship('Definition', backref='term', lazy=True, cascade='all, delete-orphan')
    outgoing_relations = db.relationship('TermRelation', 
                                         foreign_keys='TermRelation.term_1_id', 
                                         backref='term_1', 
                                         lazy=True)

class Definition(db.Model):
    __tablename__ = 'definitions'
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey('terms.id'), nullable=False)
    definition_text = db.Column(db.Text, nullable=False)
    style_note = db.Column(db.String(50))
    
    examples = db.relationship('Example', backref='definition', lazy=True, cascade='all, delete-orphan')

class Example(db.Model):
    __tablename__ = 'examples'
    id = db.Column(db.Integer, primary_key=True)
    definition_id = db.Column(db.Integer, db.ForeignKey('definitions.id'), nullable=False)
    example_text = db.Column(db.Text, nullable=False)

# ==========================================
# ПРОМЕЖУТОЧНЫЕ ТАБЛИЦЫ
# ==========================================

class TermCategory(db.Model):
    __tablename__ = 'term_category'
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey('terms.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

class TermRelation(db.Model):
    __tablename__ = 'term_relations'
    id = db.Column(db.Integer, primary_key=True)
    term_1_id = db.Column(db.Integer, db.ForeignKey('terms.id'), nullable=False)
    term_2_id = db.Column(db.Integer, db.ForeignKey('terms.id'), nullable=False)
    relation_type_id = db.Column(db.Integer, db.ForeignKey('relation_types.id'), nullable=False)
    
    # Явное указание внешних ключей для рекурсивной связи
    term_2 = db.relationship('Term', foreign_keys=[term_2_id], backref='incoming_relations')
    relation_type = db.relationship('RelationType', backref='relations')