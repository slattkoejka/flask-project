from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, BooleanField, DateField, SelectField
from wtforms.validators import DataRequired
import datetime
from data import db_session
from data.categories import Category


class TransactionAddForm(FlaskForm):
    amount = IntegerField('Сумма', validators=[DataRequired()])
    date = DateField("Дата", validators=[DataRequired()], default=datetime.datetime.today())
    type = BooleanField("Списание", default=True)
    category_id = SelectField('Категория', choices=[], coerce=int)
    submit = SubmitField('Завершить')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        db_sess = db_session.create_session()
        categories = db_sess.query(Category).all()

        self.category_id.choices = [(c.id, c.name) for c in categories]

