import flask
from flask import jsonify, make_response, request, render_template

from . import db_session
from .users import User

blueprint = flask.Blueprint(
    'user_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/users')
def get_users():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    return jsonify(
        {
            "users": [
                item.to_dict(only=(
                    'id',
                    'email',
                    'name',
                    'modified_date'
                )) for item in users
            ]
        }
    )
    # return render_template("base.html")

@blueprint.route('/api/users/<int:user_id>')
def get_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()

    if not user:
        return make_response(jsonify({'error': 'Not found'}), 404)

    return jsonify(
        {
            "user": [
                user.to_dict(only=(
                    'id',
                    'email',
                    'name',
                    'modified_date'
                ))
            ]
        }
    )


@blueprint.route('/api/users', methods=['POST'])
def create_user():
    if not request.json:
        return make_response(jsonify({'error': 'Empty request'}), 400)
    elif not all(key in request.json for key in
                 [
                    'id',
                    'email',
                    'name',
                    'modified_date'
                 ]):
        return make_response(jsonify({'error': 'Bad request'}), 400)
    db_sess = db_session.create_session()
    user = User(
        email=request.json.email,
        name=request.json.name,
    )
    db_sess.add(user)
    db_sess.commit()
    return jsonify({'id': user.id})

@blueprint.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return make_response(jsonify({'error': 'Not found'}), 400)
    db_sess.delete(user)
    db_sess.commit()
    return jsonify({'success': 'OK'})


@blueprint.route('/api/users/<int:user_id>', methods=['PUT'])
def change_user(user_id):
    if not request.json:
        return make_response(jsonify({'error': 'Empty request'}), 400)
    elif not all(key in request.json for key in
                 [
                     'id',
                    'email',
                    'name',
                    'modified_date'
                 ]):
        return make_response(jsonify({'error': 'Bad request'}), 400)
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return make_response(jsonify({'error': 'Not found'}), 400)
    user.name = request.json.name,
    user.email = request.json.email
    db_sess.commit()
    return jsonify({'success': 'OK'})
