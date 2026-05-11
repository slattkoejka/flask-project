from datetime import datetime
from os.path import isfile
from flask import Flask, render_template, request, abort, make_response, jsonify, url_for, redirect, Response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import redirect, secure_filename
from data.users import User
from data.transactions import Transactions
from data.categories import Category
from forms.login import LoginForm
from forms.register import RegisterForm
from forms.transaction import TransactionAddForm
from data import db_session, users_resource, user_api, transactions_resource, transactions_api
import requests
import os
import uuid
import csv
import io
from flask_restful import reqparse, abort, Api, Resource

"""type='1' - expense
type='0' - income"""

EXCHANGE_API_KEY = '2fc0909dda73d4b28379a2d1'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
api = Api(app)
api.add_resource(users_resource.UserResource, '/api/users/<int:user_id>')
api.add_resource(users_resource.UserListResource, '/api/users')
api.add_resource(transactions_resource.TransactionsResource, '/api/transactions/<int:transaction_id>')
api.add_resource(transactions_resource.TransactionsListResource, '/api/transactions')

app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

UPLOAD_FOLDER = 'static/img'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

login_manager = LoginManager()
login_manager.init_app(app)


def get_income_expenses(transactions):
    total_income = 0
    total_expense = 0
    for t in transactions:
        if t.type == '1':
            total_expense += t.amount
        else:
            total_income += t.amount
    return total_income, total_expense


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route("/")
def index():
    income, expense, transactions = None, None, None
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        user_data = db_sess.get(User, current_user.id)
        income, expense = get_income_expenses(user_data.transactions)
        transactions = user_data.transactions
    return render_template("main_page.html",
                           income=income,
                           expense=expense,
                           transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect('/dashboard')
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/dashboard")
        return render_template("login.html", message="Неверный логин или пароль", form=form)
    return render_template("login.html", form=form, title="Authorization")


@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegisterForm()
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        return redirect('/dashboard')
    if form.validate_on_submit():
        if db_sess.query(User).filter(User.name == form.name.data).first():
            form.name.errors.append("Это имя уже занято")
            return render_template("register.html", form=form)
        db_sess = db_session.create_session()
        new_user = User()
        new_user.name = form.name.data
        new_user.email = form.email.data
        new_user.set_password(form.password.data)
        db_sess.add(new_user)
        db_sess.commit()
        login_user(new_user, remember=form.remember_me.data)
        return redirect("/dashboard")
    return render_template("register.html", form=form)


@app.route('/account')
def account():
    if current_user.is_authenticated:
        income, expense = get_income_expenses(current_user.transactions)
        return render_template('account.html', title='Мой аккаунт', income=income, expense=expense)
    else:
        return redirect('/dashboard')


@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    file = request.files.get('avatar')

    if not file or file.filename == '':
        return redirect(url_for('account'))

    if allowed_file(file.filename):

        ext = file.filename.rsplit('.', 1)[1].lower()

        filename = f"user_{current_user.id}_{uuid.uuid4().hex}.{ext}"

        filepath = os.path.join(
            'static',
            'img',
            'avatars',
            filename
        )

        file.save(filepath)

        if current_user.avatar and current_user.avatar != 'default.png':
            old_path = os.path.join(
                'static',
                'avatars',
                current_user.avatar
            )

            if os.path.exists(old_path):
                os.remove(old_path)

        db_sess = db_session.create_session()

        user = db_sess.get(User, current_user.id)
        user.avatar = filename

        db_sess.commit()

    return redirect(url_for('account'))


@login_required
@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect("/")


@app.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('dashboard_login'))

    db_sess = db_session.create_session()

    sort = request.args.get('sort', 'date')
    order = request.args.get('order', 'desc')
    selected_categories = request.args.getlist('categories')

    query = db_sess.query(Transactions).filter(
        Transactions.user_id == current_user.id
    )

    if selected_categories:
        selected_categories = list(map(int, selected_categories))
        query = query.filter(Transactions.category_id.in_(selected_categories))

    all_categories = db_sess.query(Category).all()

    if sort == 'amount':
        if order == 'asc':
            query = query.order_by(Transactions.amount.asc())
        else:
            query = query.order_by(Transactions.amount.desc())
    else:
        if order == 'asc':
            query = query.order_by(Transactions.date.asc())
        else:
            query = query.order_by(Transactions.date.desc())

    transactions = query.all()

    total = sum(
        t.amount if t.type != '1' else -t.amount
        for t in transactions
    )

    return render_template(
        'dashboard.html',
        transactions=transactions,
        total=total,
        categories=all_categories,
        selected_categories=selected_categories
    )


@app.route('/dashboard_login')
def dashboard_login():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    else:
        return render_template('dashboard_login.html')


@app.route('/rates', methods=['GET', 'POST'])
def rates():
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest/RUB"

    response = requests.get(url)
    data = response.json()

    rates = data["conversion_rates"]
    res = {}
    res['Китайский юань CNY'] = round(1 / rates['CNY'], 2)
    res['Американский доллар USD'] = round(1 / rates["USD"], 2)
    res['Европейское евро EUR'] = round(1 / rates["EUR"], 2)
    res['Британский фунт стерлингов GBP'] = round(1 / rates['GBP'], 2)
    res['Кувейтский динар KWD'] = round(1 / rates['KWD'], 2)

    result = None

    if request.method == "POST":
        amount = float(request.form["amount"])
        to_currency = request.form["currency"]

        result = f'{amount}{to_currency} = {amount * res[to_currency]}RUB'

    return render_template("rates.html", rates=res, result=result)


@app.route('/export_csv')
def export_csv():
    db_sess = db_session.create_session()

    transactions = db_sess.query(Transactions).filter(
        Transactions.user_id == current_user.id
    ).all()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')

    writer.writerow(["ID", "Дата", "Тип", "Сумма", "Категория"])

    for t in transactions:
        writer.writerow([
            t.id,
            t.date,
            "Расход" if t.type == "1" else "Доход",
            t.amount,
            t.category.name if t.category else ""
        ])

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=transactions{datetime.now()}.csv"}
    )


@login_required
@app.route("/add_transaction", methods=["POST", "GET"])
def add_transaction():
    form = TransactionAddForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        new_transaction = Transactions()
        new_transaction.user_id = current_user.id
        new_transaction.amount = form.amount.data
        new_transaction.type = form.type.data
        new_transaction.date = form.date.data
        new_transaction.category_id = form.category_id.data
        db_sess.add(new_transaction)
        db_sess.commit()
        return redirect("/dashboard")
    return render_template("add_transaction.html", form=form)


@login_required
@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    db_sess = db_session.create_session()
    transaction = db_sess.get(Transactions, transaction_id)

    if transaction:
        db_sess.delete(transaction)
        db_sess.commit()

    return redirect(url_for('dashboard'))


@login_required
@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    db_sess = db_session.create_session()
    transaction = db_sess.get(Transactions, transaction_id)

    if transaction.user_id != current_user.id:
        abort(403)

    form = TransactionAddForm(obj=transaction)

    if form.validate_on_submit():
        transaction.amount = form.amount.data
        transaction.date = form.date.data
        transaction.type = form.type.data
        transaction.category_id = form.category_id.data

        db_sess.commit()
        return redirect(url_for('dashboard'))

    return render_template('edit_transaction.html', form=form)


@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


@app.errorhandler(404)
def page_not_found(_):
    return make_response(jsonify({'error': 'Page not found'}), 404)


@app.errorhandler(403)
def forbidden(_):
    return make_response(jsonify({'error': 'Forbidden'}), 403)


if __name__ == "__main__":
    db_session.global_init("db/budget.db")
    app.run()
