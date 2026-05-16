from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Term, Definition, Example, Source, Category, Status, TermCategory, RelationType, TermRelation
from config import Config
from sqlalchemy import or_

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к панели управления необходимо выполнить вход в систему.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)

    terms_query = Term.query.filter(Term.status.has(name='Опубликован'))

    if query:
        # Поиск без учёта регистра с использованием ilike - ищем в названии, происхождении и определениях
        search_pattern = f'%{query}%'
        terms_query = terms_query.join(Definition).filter(
            or_(
                Term.term_name.ilike(search_pattern),
                Term.origin_word.ilike(search_pattern),  # Новое поле origin_word
                Definition.definition_text.ilike(search_pattern)
            )
        )

    if category_id:
        terms_query = terms_query.join(TermCategory).filter(TermCategory.category_id == category_id)

    terms = terms_query.all()
    categories = Category.query.all()

    return render_template('index.html', terms=terms, categories=categories, query=query)

# Добавь эти функции в app.py после существующих маршрутов

@app.route('/alphabet/<letter>')
def alphabet_filter(letter):
    """Фильтрация терминов по первой букве"""
    query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)
    
    terms_query = Term.query.filter(Term.status.has(name='Опубликован'))
    
    # Фильтр по первой букве (регистронезависимый)
    letter = letter.upper()
    terms_query = terms_query.filter(
        Term.term_name.ilike(f'{letter}%')
    )
    
    if query:
        # Поиск без учёта регистра с использованием ilike
        search_pattern = f'%{query}%'
        terms_query = terms_query.join(Definition).filter(
            or_(
                Term.term_name.ilike(search_pattern),
                Term.origin_word.ilike(search_pattern),  # Новое поле origin_word
                Definition.definition_text.ilike(search_pattern)
            )
        )
    
    if category_id:
        terms_query = terms_query.join(TermCategory).filter(TermCategory.category_id == category_id)
    
    terms = terms_query.order_by(Term.term_name.asc()).all()
    categories = Category.query.all()
    
    return render_template('index.html', terms=terms, categories=categories, query=query, current_letter=letter)

@app.route('/random')
def random_term():
    """Случайный термин"""
    random_term = Term.query.filter(Term.status.has(name='Опубликован')).order_by(func.random()).first()
    if random_term:
        return redirect(url_for('term_detail', term_id=random_term.id))
    return redirect(url_for('index'))

@app.route('/api/suggestions')
def api_suggestions():
    """API для автодополнения поиска"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return []
    
    # Поиск без учёта регистра с использованием ilike
    terms = Term.query.filter(
        Term.status.has(name='Опубликован'),
        or_(
            Term.term_name.ilike(f'{query}%'),
            Term.origin_word.ilike(f'{query}%')
        )
    ).limit(10).all()
    
    return [term.term_name for term in terms]

@app.route('/term/<int:term_id>')
def term_detail(term_id):
    term = Term.query.get_or_404(term_id)
    return render_template('term.html', term=term)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))

    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('admin'))
        flash('Неверные учётные данные.', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    terms = Term.query.order_by(Term.created_at.desc()).all()
    return render_template('admin.html', terms=terms, editing=False)

@app.route('/admin/create', methods=['POST'])
@login_required
def create_term():
    term_name = request.form.get('term_name')
    origin = request.form.get('origin')
    transcription = request.form.get('transcription')
    grammar_notes = request.form.get('grammar_notes')
    origin_word = request.form.get('origin_word')
    etymology_note = request.form.get('etymology_note')
    year_fixed = request.form.get('year_fixed')
    source_name = request.form.get('source_name')
    
    # Get lists of definitions, examples, style notes
    definition_texts = request.form.getlist('definition_text[]')
    style_notes = request.form.getlist('style_note[]')
    example_texts = request.form.getlist('example_text[]')
    
    # Get semantic relations
    related_term_ids = request.form.getlist('related_term_id[]')
    relation_type_ids = request.form.getlist('relation_type_id[]')

    if term_name and any(definition_texts):
        published_status = Status.query.filter_by(name='Опубликован').first()

        source = None
        if source_name:
            source = Source.query.filter_by(resource_name=source_name).first()
            if not source:
                source = Source(resource_name=source_name, source_type='Указан администратором')
                db.session.add(source)
                db.session.flush()

        new_term = Term(
            term_name=term_name,
            origin=origin,
            transcription=transcription,
            grammar_notes=grammar_notes,
            origin_word=origin_word,
            etymology_note=etymology_note,
            year_fixed=year_fixed,
            user_id=current_user.id,
            status_id=published_status.id,
            source_id=source.id if source else None
        )
        db.session.add(new_term)
        db.session.flush()

        # Add multiple definitions
        for i, def_text in enumerate(definition_texts):
            if def_text.strip():
                new_def = Definition(
                    term_id=new_term.id, 
                    definition_text=def_text,
                    style_note=style_notes[i] if i < len(style_notes) and style_notes[i].strip() else None
                )
                db.session.add(new_def)
                db.session.flush()
                
                # Add example for this definition if provided
                if i < len(example_texts) and example_texts[i].strip():
                    db.session.add(Example(definition_id=new_def.id, example_text=example_texts[i]))

        # Add semantic relations
        for i, related_id in enumerate(related_term_ids):
            if related_id.strip() and i < len(relation_type_ids) and relation_type_ids[i].strip():
                db.session.add(TermRelation(
                    term_1_id=new_term.id,
                    term_2_id=int(related_id),
                    relation_type_id=int(relation_type_ids[i])
                ))

        db.session.commit()
        flash('Словарная статья успешно добавлена в реестр.', 'success')

    return redirect(url_for('admin'))

@app.route('/admin/edit/<int:term_id>', methods=['GET', 'POST'])
@login_required
def edit_term(term_id):
    term = Term.query.get_or_404(term_id)
    
    if request.method == 'POST':
        term.term_name = request.form.get('term_name')
        term.origin = request.form.get('origin')
        term.transcription = request.form.get('transcription')
        term.grammar_notes = request.form.get('grammar_notes')
        term.origin_word = request.form.get('origin_word')
        term.etymology_note = request.form.get('etymology_note')
        term.year_fixed = request.form.get('year_fixed')
        
        source_name = request.form.get('source_name')
        if source_name:
            source = Source.query.filter_by(resource_name=source_name).first()
            if not source:
                source = Source(resource_name=source_name, source_type='Указан администратором')
                db.session.add(source)
                db.session.flush()
            term.source_id = source.id
            
        status_name = request.form.get('status')
        if status_name:
            status = Status.query.filter_by(name=status_name).first()
            if status:
                term.status_id = status.id

        # Get lists of definitions, examples, style notes
        definition_texts = request.form.getlist('definition_text[]')
        style_notes = request.form.getlist('style_note[]')
        example_texts = request.form.getlist('example_text[]')
        
        # Delete existing definitions and create new ones
        for defn in term.definitions:
            db.session.delete(defn)
        db.session.flush()
        
        # Add new definitions
        for i, def_text in enumerate(definition_texts):
            if def_text.strip():
                new_def = Definition(
                    term_id=term.id, 
                    definition_text=def_text,
                    style_note=style_notes[i] if i < len(style_notes) and style_notes[i].strip() else None
                )
                db.session.add(new_def)
                db.session.flush()
                
                # Add example for this definition if provided
                if i < len(example_texts) and example_texts[i].strip():
                    db.session.add(Example(definition_id=new_def.id, example_text=example_texts[i]))

        # Delete existing relations and create new ones
        for rel in term.outgoing_relations:
            db.session.delete(rel)
        db.session.flush()
        
        # Add semantic relations
        related_term_ids = request.form.getlist('related_term_id[]')
        relation_type_ids = request.form.getlist('relation_type_id[]')
        for i, related_id in enumerate(related_term_ids):
            if related_id.strip() and i < len(relation_type_ids) and relation_type_ids[i].strip():
                db.session.add(TermRelation(
                    term_1_id=term.id,
                    term_2_id=int(related_id),
                    relation_type_id=int(relation_type_ids[i])
                ))

        db.session.commit()
        flash('Данные словарной статьи успешно обновлены.', 'success')
        return redirect(url_for('admin'))

    # Prepare data for edit form
    src_name = term.source.resource_name if term.source else ''
    status_name = term.status.name if term.status else 'Черновик'
    
    # Get all terms for relation dropdown (excluding current term)
    all_terms = Term.query.filter(Term.id != term.id).all()
    relation_types = RelationType.query.all()

    return render_template('admin.html', term=term, 
                           src_name=src_name, status_name=status_name, 
                           editing=True, all_terms=all_terms, relation_types=relation_types)

@app.route('/admin/delete/<int:term_id>')
@login_required
def delete_term(term_id):
    term = Term.query.get_or_404(term_id)
    db.session.delete(term)
    db.session.commit()
    flash('Запись удалена из реестра.', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)