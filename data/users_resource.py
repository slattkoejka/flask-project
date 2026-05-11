from flask import jsonify, abort

from . import db_session
from .users import User
from flask_restful import Resource

from .users_parser import parser


def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f"User {user_id} not found")


class UserResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.get(User, user_id)
        return jsonify(
            {
                "user": [
                    user.to_dict(only=(
                        'id',
                        'name',
                        'email'
                    ))
                ]
            }
        )

    def delete(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.get(User, user_id)
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})


class UserListResource(Resource):
    def get(self):
        session = db_session.create_session()
        users = session.query(User).all()
        return jsonify(
            {
                "users": [
                    item.to_dict(only=(
                        'id',
                        'name',
                        'email'
                    )) for item in users
                ]
            }
        )

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        user = User(
            name=args['name'],
            email=args['email']
        )
        session.add(user)
        session.commit()
        return jsonify({'id': user.id})
