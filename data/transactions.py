import datetime
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase

class Transactions(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'transactions'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    amount = sqlalchemy.Column(sqlalchemy.Integer)
    date = sqlalchemy.Column(sqlalchemy.Date, default=datetime.datetime.today)

    type = sqlalchemy.Column(sqlalchemy.String)

    category_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('categories.id'))

    user = orm.relationship("User", back_populates="transactions")

    category = orm.relationship("Category", back_populates="transactions")

    def __repr__(self):
        return f'Финансовая операция {self.type} на сумму {self.amount} в категории {self.category_id}({self.date})'