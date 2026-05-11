import flask
from flask import jsonify, make_response, request

from . import db_session
from .transactions import Transactions
import datetime

blueprint = flask.Blueprint(
    'transactions_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/transactions')
def get_transactions():
    db_sess = db_session.create_session()
    transactions = db_sess.query(Transactions).all()
    return jsonify(
        {
            "transactions": [
                item.to_dict(only=(
                    'id',
                    'user_id',
                    'amount',
                    'date',
                    'type',
                    'category_id',
                )) for item in transactions
            ]
        }
    )


@blueprint.route('/api/transactions/<int:transaction_id>')
def get_transaction(transaction_id):
    db_sess = db_session.create_session()
    transaction = db_sess.query(Transactions).filter(Transactions.id == transaction_id).first()

    if not transaction:
        return make_response(jsonify({'error': 'Not found'}), 404)

    return jsonify(
        {
            "transactions": [
                transaction.to_dict(only=(
                    'id',
                    'user_id',
                    'amount',
                    'date',
                    'type',
                    'category_id',
                ))
            ]
        }
    )


@blueprint.route('/api/transactions', methods=['POST'])
def create_transactions():
    if not request.json:
        return make_response(jsonify({'error': 'Empty request'}), 400)
    elif not all(key in request.json for key in
                 [
                     'user_id',
                    'amount',
                    'date',
                    'type',
                    'category_id',
                 ]):
        return make_response(jsonify({'error': 'Bad request'}), 400)
    db_sess = db_session.create_session()
    transactions = Transactions(
        user_id=request.json["user_id"],
        amount=request.json["amount"],
        date=datetime.datetime.strptime(request.json['date'], '%Y-%m-%d').date(),
        type=request.json['type'],
        category_id=request.json['category_id']
    )
    db_sess.add(transactions)
    db_sess.commit()
    return jsonify({'id': transactions.id})


@blueprint.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transactions(transaction_id):
    db_sess = db_session.create_session()
    transactions = db_sess.get(Transactions, transaction_id)
    if not transactions:
        return make_response(jsonify({'error': 'Not found'}), 400)
    db_sess.delete(transactions)
    db_sess.commit()
    return jsonify({'success': 'OK'})


@blueprint.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
def change_transactions(transaction_id):
    if not request.json:
        return make_response(jsonify({'error': 'Empty request'}), 400)
    elif not all(key in request.json for key in
                 [
                     'user_id',
                    'amount',
                    'date',
                    'type',
                    'category_id',
                 ]):
        return make_response(jsonify({'error': 'Bad request'}), 400)
    db_sess = db_session.create_session()
    transactions = db_sess.get(Transactions, transaction_id)
    if not transactions:
        return make_response(jsonify({'error': 'Not found'}), 400)
    transactions.user_id = request.json["user_id"]
    transactions.amount = request.json["amount"]
    transactions.date = request.json['date']
    transactions.type = request.json['type']
    transactions.category_id = request.json['category_id']
    db_sess.commit()
    return jsonify({'success': 'OK'})
