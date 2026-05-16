from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Term, Definition, Example, Source, Category, Status, TermCategory
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
        terms_query = terms_query.join(Definition).filter(
            or_(
                Term.term_name.ilike(f'%{query}%'),
                Term.origin.ilike(f'%{query}%'),
                Definition.definition_text.ilike(f'%{query}%')
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
        terms_query = terms_query.join(Definition).filter(
            or_(
                Term.term_name.ilike(f'%{query}%'),
                Term.origin.ilike(f'%{query}%'),
                Definition.definition_text.ilike(f'%{query}%')
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
    
    terms = Term.query.filter(
        Term.status.has(name='Опубликован'),
        Term.term_name.ilike(f'{query}%')
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
    definition_text = request.form.get('definition')
    example_text = request.form.get('example')
    source_name = request.form.get('source_name')

    if term_name and definition_text:
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
            user_id=current_user.id,
            status_id=published_status.id,
            source_id=source.id if source else None
        )
        db.session.add(new_term)
        db.session.flush()

        new_def = Definition(term_id=new_term.id, definition_text=definition_text)
        db.session.add(new_def)
        db.session.flush()

        if example_text:
            db.session.add(Example(definition_id=new_def.id, example_text=example_text))

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

        if term.definitions:
            definition = term.definitions[0]
            definition.definition_text = request.form.get('definition')
            example_text = request.form.get('example')
            if example_text:
                if definition.examples:
                    definition.examples[0].example_text = example_text
                else:
                    db.session.add(Example(definition_id=definition.id, example_text=example_text))

        db.session.commit()
        flash('Данные словарной статьи успешно обновлены.', 'success')
        return redirect(url_for('admin'))

    def_text = term.definitions[0].definition_text if term.definitions else ''
    ex_text = term.definitions[0].examples[0].example_text if (term.definitions and term.definitions[0].examples) else ''
    src_name = term.source.resource_name if term.source else ''
    status_name = term.status.name if term.status else 'Черновик'

    return render_template('admin.html', term=term, 
                           def_text=def_text, ex_text=ex_text, 
                           src_name=src_name, status_name=status_name, 
                           editing=True)

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