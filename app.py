from collections import Counter
from difflib import SequenceMatcher
from functools import wraps
from math import sqrt
import re

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import (
    Category,
    Definition,
    Example,
    RelationType,
    Source,
    Status,
    Term,
    TermCategory,
    TermRelation,
    User,
    db,
)


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Для доступа к панели управления необходимо войти в систему."

PUBLISHED_STATUS = "Опубликован"
DEFAULT_MODERATION_STATUS = "Новый"
SYMMETRIC_RELATION_TYPES = {"Синоним", "Антоним"}
STOP_WORDS = {
    "без", "более", "быть", "в", "для", "до", "его", "ее", "из", "или", "и",
    "как", "к", "на", "не", "но", "о", "об", "от", "по", "под", "при", "с",
    "со", "также", "у", "это", "является",
}


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            flash("Этот раздел доступен только администратору.", "error")
            return redirect(url_for("suggest_term"))
        return view(*args, **kwargs)

    return wrapped


def normalize_term_name(value):
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def similarity_ratio(left, right):
    return SequenceMatcher(None, normalize_term_name(left), normalize_term_name(right)).ratio()


def find_similar_terms(term_name, limit=8, include_unpublished=True, exclude_term_id=None):
    normalized = normalize_term_name(term_name)
    if len(normalized) < 2:
        return []

    query = Term.query
    if not include_unpublished:
        query = query.filter(Term.status.has(name=PUBLISHED_STATUS))

    matches = []
    for term in query.order_by(Term.term_name.asc()).all():
        if exclude_term_id and term.id == exclude_term_id:
            continue
        candidate = normalize_term_name(term.term_name)
        ratio = similarity_ratio(normalized, candidate)
        contains = normalized in candidate or candidate in normalized
        if ratio >= 0.58 or contains:
            matches.append(
                {
                    "term_id": term.id,
                    "term_name": term.term_name,
                    "status": term.status.name,
                    "score": round(max(ratio, 0.7 if contains else 0) * 100),
                }
            )
    return sorted(matches, key=lambda item: (-item["score"], item["term_name"]))[:limit]


def make_case_insensitive_search(field, pattern):
    """Build a LIKE expression that also works with Cyrillic text in SQLite."""
    clean_pattern = pattern.replace("%", "")
    if not clean_pattern:
        return field.like(pattern)

    has_prefix = pattern.startswith("%")
    has_suffix = pattern.endswith("%")

    def restore_wildcards(value):
        return f"{'%' if has_prefix else ''}{value}{'%' if has_suffix else ''}"

    variants = {
        restore_wildcards(clean_pattern),
        restore_wildcards(clean_pattern.lower()),
        restore_wildcards(clean_pattern.upper()),
        restore_wildcards(clean_pattern.capitalize()),
    }
    if len(clean_pattern) <= 3:
        for mask in range(2 ** len(clean_pattern)):
            value = "".join(
                char.upper() if (mask >> index) & 1 else char.lower()
                for index, char in enumerate(clean_pattern)
            )
            variants.add(restore_wildcards(value))

    return or_(*(field.like(variant) for variant in variants))


def tokenize(text):
    return [
        token
        for token in re.findall(r"[a-zа-яё0-9]+", (text or "").lower())
        if len(token) > 2 and token not in STOP_WORDS
    ]


def cosine_similarity(left_text, right_text):
    left = Counter(tokenize(left_text))
    right = Counter(tokenize(right_text))
    if not left or not right:
        return 0.0
    shared = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in shared)
    denominator = sqrt(sum(value * value for value in left.values())) * sqrt(
        sum(value * value for value in right.values())
    )
    return numerator / denominator if denominator else 0.0


def term_search_text(term):
    return " ".join(
        filter(
            None,
            [
                term.term_name,
                term.origin_word,
                term.etymology_note,
                *(definition.definition_text for definition in term.definitions),
            ],
        )
    )


def build_relation_recommendations(term_name, definitions, origin_word="", exclude_term_id=None):
    """Recommend links for moderator review based on definition similarity."""
    input_text = " ".join(filter(None, [term_name, origin_word, *definitions]))
    if len(tokenize(input_text)) < 2:
        return []

    terms = Term.query.order_by(Term.term_name.asc()).all()
    direct_scores = {}
    for term in terms:
        if term.id == exclude_term_id:
            continue
        score = cosine_similarity(input_text, term_search_text(term))
        if score >= 0.12:
            direct_scores[term.id] = score

    recommendations = {}

    def offer(term, relation_type, score, reason):
        if term.id == exclude_term_id or score < 0.12:
            return
        key = (term.id, relation_type)
        if key not in recommendations or recommendations[key]["score"] < score:
            recommendations[key] = {
                "term_id": term.id,
                "term_name": term.term_name,
                "relation_type": relation_type,
                "score": round(min(score, 1.0) * 100),
                "reason": reason,
            }

    for term in terms:
        score = direct_scores.get(term.id, 0)
        if score >= 0.26:
            offer(term, "Синоним", score, "Похожее определение")
        elif score >= 0.16:
            offer(term, "Родственное понятие", score, "Пересекаются ключевые слова")

        # If the input resembles one side of an approved antonym pair, the other
        # side is a useful antonym candidate for moderator review.
        if score >= 0.16:
            for relation in term.outgoing_relations:
                if relation.relation_type.type_name == "Антоним":
                    offer(
                        relation.term_2,
                        "Антоним",
                        score * 0.92,
                        f"Антоним близкого понятия «{term.term_name}»",
                    )

    ordered = sorted(
        recommendations.values(),
        key=lambda item: (-item["score"], item["relation_type"], item["term_name"]),
    )
    return ordered[:12]


def get_or_create_source(source_name, source_url=""):
    source_name = source_name.strip()
    source_url = source_url.strip()
    if not source_name and not source_url:
        return None
    if not source_name:
        source_name = "Источник по ссылке"
    source = Source.query.filter_by(resource_name=source_name, url=source_url or None).first()
    if not source:
        source = Source(
            resource_name=source_name,
            source_type="Указан модератором",
            url=source_url or None,
        )
        db.session.add(source)
        db.session.flush()
    return source


def replace_definitions(term, form):
    for definition in list(term.definitions):
        db.session.delete(definition)
    db.session.flush()

    texts = form.getlist("definition_text[]")
    style_notes = form.getlist("style_note[]")
    example_texts = form.getlist("example_text[]")
    for index, text in enumerate(texts):
        if not text.strip():
            continue
        definition = Definition(
            term_id=term.id,
            definition_text=text.strip(),
            style_note=style_notes[index].strip()
            if index < len(style_notes) and style_notes[index].strip()
            else None,
        )
        db.session.add(definition)
        db.session.flush()
        if index < len(example_texts) and example_texts[index].strip():
            db.session.add(
                Example(definition_id=definition.id, example_text=example_texts[index].strip())
            )


def add_relation(term_1_id, term_2_id, relation_type_id):
    if term_1_id == term_2_id:
        return
    exists = TermRelation.query.filter_by(
        term_1_id=term_1_id,
        term_2_id=term_2_id,
        relation_type_id=relation_type_id,
    ).first()
    if not exists:
        db.session.add(
            TermRelation(
                term_1_id=term_1_id,
                term_2_id=term_2_id,
                relation_type_id=relation_type_id,
            )
        )


def replace_relations(term, form):
    relation_ids = {relation.id for relation in term.outgoing_relations}
    for relation in list(term.outgoing_relations):
        if relation.relation_type.type_name in SYMMETRIC_RELATION_TYPES:
            reverse = TermRelation.query.filter_by(
                term_1_id=relation.term_2_id,
                term_2_id=term.id,
                relation_type_id=relation.relation_type_id,
            ).first()
            if reverse and reverse.id not in relation_ids:
                db.session.delete(reverse)
        db.session.delete(relation)
    db.session.flush()

    related_ids = form.getlist("related_term_id[]")
    type_ids = form.getlist("relation_type_id[]")
    relation_types = {item.id: item for item in RelationType.query.all()}
    for index, related_id in enumerate(related_ids):
        if not related_id or index >= len(type_ids) or not type_ids[index]:
            continue
        related_id = int(related_id)
        type_id = int(type_ids[index])
        relation_type = relation_types.get(type_id)
        if not relation_type:
            continue
        add_relation(term.id, related_id, type_id)
        if relation_type.type_name in SYMMETRIC_RELATION_TYPES:
            add_relation(related_id, term.id, type_id)


def fill_term_from_form(term, form):
    term.term_name = form.get("term_name", "").strip()
    term.origin = form.get("origin")
    term.transcription = form.get("transcription")
    term.grammar_notes = form.get("grammar_notes")
    term.origin_word = form.get("origin_word")
    term.etymology_note = form.get("etymology_note")
    term.year_fixed = form.get("year_fixed")
    last_year = form.get("last_year_fixed", "")
    term.last_year_fixed = int(last_year) if last_year.isdigit() else None
    source = get_or_create_source(
        form.get("source_name", ""),
        form.get("source_url", ""),
    )
    term.source_id = source.id if source else None


@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)
    terms_query = Term.query.filter(Term.status.has(name=PUBLISHED_STATUS))

    if query:
        pattern = f"%{query}%"
        terms_query = terms_query.join(Definition).filter(
            or_(
                make_case_insensitive_search(Term.term_name, pattern),
                make_case_insensitive_search(Term.origin_word, pattern),
                make_case_insensitive_search(Definition.definition_text, pattern),
            )
        )
    if category_id:
        terms_query = terms_query.join(TermCategory).filter(TermCategory.category_id == category_id)

    terms = terms_query.distinct().order_by(Term.term_name.asc()).all()
    return render_template("index.html", terms=terms, categories=Category.query.all(), query=query)


@app.route("/alphabet/<letter>")
def alphabet_filter(letter):
    query = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)
    terms_query = Term.query.filter(
        Term.status.has(name=PUBLISHED_STATUS),
        make_case_insensitive_search(Term.term_name, f"{letter}%"),
    )
    if query:
        pattern = f"%{query}%"
        terms_query = terms_query.join(Definition).filter(
            or_(
                make_case_insensitive_search(Term.term_name, pattern),
                make_case_insensitive_search(Term.origin_word, pattern),
                make_case_insensitive_search(Definition.definition_text, pattern),
            )
        )
    if category_id:
        terms_query = terms_query.join(TermCategory).filter(TermCategory.category_id == category_id)

    return render_template(
        "index.html",
        terms=terms_query.distinct().order_by(Term.term_name.asc()).all(),
        categories=Category.query.all(),
        query=query,
        current_letter=letter,
    )


@app.route("/api/suggestions")
def api_suggestions():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])
    terms = Term.query.filter(
        Term.status.has(name=PUBLISHED_STATUS),
        or_(
            make_case_insensitive_search(Term.term_name, f"{query}%"),
            make_case_insensitive_search(Term.origin_word, f"{query}%"),
        ),
    ).limit(10).all()
    return jsonify([term.term_name for term in terms])


@app.route("/api/relation-recommendations", methods=["POST"])
@admin_required
def api_relation_recommendations():
    payload = request.get_json(silent=True) or {}
    definitions = payload.get("definitions") or []
    recommendations = build_relation_recommendations(
        payload.get("term_name", ""),
        [text for text in definitions if isinstance(text, str)],
        payload.get("origin_word", ""),
        payload.get("exclude_term_id"),
    )
    return jsonify(recommendations)


@app.route("/api/term-matches")
@login_required
def api_term_matches():
    query = request.args.get("q", "").strip()
    exclude_term_id = request.args.get("exclude", type=int)
    return jsonify(find_similar_terms(query, exclude_term_id=exclude_term_id))


@app.route("/term/<int:term_id>")
def term_detail(term_id):
    term = Term.query.get_or_404(term_id)
    can_view_private = (
        current_user.is_authenticated
        and (current_user.role == "admin" or term.user_id == current_user.id)
    )
    if term.status.name != PUBLISHED_STATUS and not can_view_private:
        abort(404)
    return render_template("term.html", term=term)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin") if current_user.role == "admin" else url_for("suggest_term"))
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("admin") if user.role == "admin" else url_for("suggest_term"))
        flash("Неверные учетные данные.", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("admin") if current_user.role == "admin" else url_for("suggest_term"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_repeat = request.form.get("password_repeat", "")
        if len(username) < 3:
            flash("Логин должен быть не короче 3 символов.", "error")
        elif len(password) < 6:
            flash("Пароль должен быть не короче 6 символов.", "error")
        elif password != password_repeat:
            flash("Пароли не совпадают.", "error")
        elif User.query.filter_by(username=username).first():
            flash("Пользователь с таким логином уже существует.", "error")
        else:
            user = User(username=username, password=generate_password_hash(password), role="user")
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Аккаунт создан. Теперь можно предложить термин.", "success")
            return redirect(url_for("suggest_term"))
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin():
    query = request.args.get("q", "").strip()
    status_id = request.args.get("status", type=int)
    terms_query = Term.query
    if query:
        pattern = f"%{query}%"
        terms_query = terms_query.outerjoin(Definition).filter(
            or_(
                make_case_insensitive_search(Term.term_name, pattern),
                make_case_insensitive_search(Term.origin_word, pattern),
                make_case_insensitive_search(Definition.definition_text, pattern),
            )
        )
    if status_id:
        terms_query = terms_query.filter(Term.status_id == status_id)

    terms = terms_query.distinct().order_by(Term.created_at.desc()).all()
    return render_template(
        "admin.html",
        terms=terms,
        all_terms=Term.query.order_by(Term.term_name.asc()).all(),
        statuses=Status.query.order_by(Status.id).all(),
        relation_types=RelationType.query.order_by(RelationType.id).all(),
        editing=False,
        admin_query=query,
        admin_status_id=status_id,
    )


@app.route("/admin/create", methods=["POST"])
@admin_required
def create_term():
    name = request.form.get("term_name", "").strip()
    definitions = request.form.getlist("definition_text[]")
    if not name or not any(text.strip() for text in definitions):
        flash("Укажите название и хотя бы одно определение.", "error")
        return redirect(url_for("admin"))

    status = Status.query.filter_by(name=DEFAULT_MODERATION_STATUS).first()
    if not status:
        status = Status.query.filter_by(name=PUBLISHED_STATUS).first_or_404()
    term = Term(user_id=current_user.id, status_id=status.id, term_name=name)
    fill_term_from_form(term, request.form)
    db.session.add(term)
    db.session.flush()
    replace_definitions(term, request.form)
    replace_relations(term, request.form)
    db.session.commit()
    flash("Словарная статья добавлена и отправлена на модерацию.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/edit/<int:term_id>", methods=["GET", "POST"])
@admin_required
def edit_term(term_id):
    term = Term.query.get_or_404(term_id)
    if request.method == "POST":
        fill_term_from_form(term, request.form)
        status = Status.query.filter_by(name=request.form.get("status")).first()
        if status:
            term.status_id = status.id
        replace_definitions(term, request.form)
        replace_relations(term, request.form)
        db.session.commit()
        flash("Данные словарной статьи обновлены.", "success")
        return redirect(url_for("admin"))

    return render_template(
        "admin.html",
        term=term,
        src_name=term.source.resource_name if term.source else "",
        src_url=term.source.url if term.source and term.source.url else "",
        status_name=term.status.name,
        editing=True,
        all_terms=Term.query.filter(Term.id != term.id).order_by(Term.term_name.asc()).all(),
        statuses=Status.query.order_by(Status.id).all(),
        relation_types=RelationType.query.order_by(RelationType.id).all(),
    )


@app.route("/admin/delete/<int:term_id>", methods=["POST"])
@admin_required
def delete_term(term_id):
    term = Term.query.get_or_404(term_id)
    for relation in TermRelation.query.filter(
        or_(TermRelation.term_1_id == term.id, TermRelation.term_2_id == term.id)
    ).all():
        db.session.delete(relation)
    db.session.delete(term)
    db.session.commit()
    flash("Запись удалена из реестра.", "success")
    return redirect(url_for("admin"))


@app.route("/suggest", methods=["GET", "POST"])
@login_required
def suggest_term():
    if current_user.role == "admin":
        return redirect(url_for("admin"))

    if request.method == "POST":
        name = request.form.get("term_name", "").strip()
        definition = request.form.get("definition_text[]", "").strip()
        if not name or not definition:
            flash("Обязательные поля: название термина и краткое определение.", "error")
            return redirect(url_for("suggest_term"))

        status = Status.query.filter_by(name=DEFAULT_MODERATION_STATUS).first()
        if not status:
            status = Status.query.filter_by(name=PUBLISHED_STATUS).first_or_404()

        term = Term(
            term_name=name,
            user_id=current_user.id,
            status_id=status.id,
            origin_word=request.form.get("origin_word", "").strip() or None,
            etymology_note=request.form.get("etymology_note", "").strip() or None,
        )
        db.session.add(term)
        db.session.flush()
        new_definition = Definition(term_id=term.id, definition_text=definition)
        db.session.add(new_definition)
        example = request.form.get("example_text[]", "").strip()
        if example:
            db.session.flush()
            db.session.add(Example(definition_id=new_definition.id, example_text=example))
        db.session.commit()
        flash("Спасибо! Термин отправлен администратору на проверку.", "success")
        return redirect(url_for("suggest_term"))

    user_terms = Term.query.filter_by(user_id=current_user.id).order_by(Term.created_at.desc()).all()
    return render_template("suggest.html", user_terms=user_terms)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
