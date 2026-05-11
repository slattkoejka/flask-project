from flask import jsonify, abort

from . import db_session
from .transactions import Transactions
from flask_restful import Resource

from .transactions_parser import parser
import datetime


def abort_if_transaction_not_found(transaction_id):
    session = db_session.create_session()
    transaction = session.query(Transactions).get(transaction_id)
    if not transaction:
        abort(404, message=f"Transactions {transaction_id} not found")


class TransactionsResource(Resource):
    def get(self, transaction_id):
        abort_if_transaction_not_found(transaction_id)
        session = db_session.create_session()
        transaction = session.get(Transactions, transaction_id)
        return jsonify(
            {
                "transactions": [
                    transaction.to_dict(only=(
                        'user_id',
                        'amount',
                        'date',
                        'type',
                        'category_id',
                    ))
                ]
            }
        )

    def delete(self, transaction_id):
        abort_if_transaction_not_found(transaction_id)
        session = db_session.create_session()
        transaction = session.get(Transactions, transaction_id)
        session.delete(transaction)
        session.commit()
        return jsonify({'success': 'OK'})


class TransactionsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        transactions = session.query(Transactions).all()
        return jsonify(
            {
                "transactions": [
                    transaction.to_dict(only=(
                        'user_id',
                        'amount',
                        'date',
                        'type',
                        'category_id',
                    )) for transaction in transactions
                ]
            }
        )

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        transaction = Transactions(
            user_id=args["user_id"],
            amount=args["amount"],
            date=datetime.datetime.strptime(
                args['date'],
                '%Y-%m-%d'
            ).date(),
            type=args['type'],
            category_id=args['category_id']
        )
        session.add(transaction)
        session.commit()
        return jsonify({'id': transaction.id})
