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
login_manager.login_message = 'Для доступа к панели администратора необходимо войти в систему.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)

    # Показываем только опубликованные термины
    terms_query = Term.query.filter(Term.status.has(name='Опубликован'))

    if query:
        terms_query = terms_query.filter(
            or_(
                Term.term_name.ilike(f'%{query}%'),
                Term.origin.ilike(f'%{query}%')
            )
        )

    if category_id:
        terms_query = terms_query.join(TermCategory).filter(TermCategory.category_id == category_id)

    terms = terms_query.all()
    categories = Category.query.all()

    return render_template('index.html', terms=terms, categories=categories, query=query)

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
        flash('Неверный логин или пароль', 'error')

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
    return render_template('admin.html', terms=terms)

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

        # Работа с источником (1 источник -> много терминов)
        source = None
        if source_name:
            source = Source.query.filter_by(resource_name=source_name).first()
            if not source:
                source = Source(resource_name=source_name, source_type='Пользовательский')
                db.session.add(source)
                db.session.flush()

        # Создание термина
        new_term = Term(
            term_name=term_name,
            origin=origin,
            user_id=current_user.id,
            status_id=published_status.id,
            source_id=source.id if source else None
        )
        db.session.add(new_term)
        db.session.flush()

        # Создание значения
        new_def = Definition(term_id=new_term.id, definition_text=definition_text)
        db.session.add(new_def)
        db.session.flush()

        # Создание примера (опционально)
        if example_text:
            db.session.add(Example(definition_id=new_def.id, example_text=example_text))

        db.session.commit()
        flash('Термин успешно добавлен в базу', 'success')

    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:term_id>')
@login_required
def delete_term(term_id):
    term = Term.query.get_or_404(term_id)
    db.session.delete(term)
    db.session.commit()
    flash('Термин удален', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)