from flask_restful import Resource, reqparse


parser = reqparse.RequestParser()
parser.add_argument('user_id', required=True, type=int)
parser.add_argument('amount', required=True, type=int)
parser.add_argument('date', required=True)
parser.add_argument('type', required=True)
parser.add_argument('category_id', required=False, type=int)