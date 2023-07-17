"""Small Todo API with User management"""
import os

import bson
from flask import Flask, abort, request
from pymongo import MongoClient

import hashlib

import unittest
from unittest.mock import patch, MagicMock


app = Flask(__name__)
client = MongoClient('db', 27017)
db = client.appdb


@app.route('/', methods=['GET'])
def get_root():
    """Return hypermedia entry point links"""
    base_url = request.base_url
    if base_url[-1] == '/':
        base_url = base_url[:-1]
    response = {
        'links': {
            'todos': '/'.join([base_url, 'todos']),
            'users': '/'.join([base_url, 'users']),
        }
    }
    return response, 200


@app.route('/todos', methods=['GET'])
def get_todos():
    """Return a list of links to all Todo objects"""
    todo_ids = db.todos.find().distinct('_id')
    todo_links = [
        '/'.join([request.base_url, str(todo_id)]) for todo_id in todo_ids
    ]
    response = {
        'items': todo_links,
        'links': {
            'self': request.base_url,
        },
    }
    return response, 200


@app.route('/todos', methods=['POST'])
def create_todo():
    """Create a new Todo object with title and optional description"""
    if 'title' not in request.json:
        abort(422)
    todo = {
        'title': request.json['title'],
        'description': request.json.get('description', ''),
    }
    response = todo.copy()
    todo_id = db.todos.insert_one(todo).inserted_id
    response['links'] = {
        'self': '/'.join([request.base_url, str(todo_id)]),
    }
    return response, 201


@app.route('/todos/<todo_id>', methods=['GET'])
def get_todo_by_id(todo_id):
    """Return a specific Todo object by id"""
    try:
        object_id = bson.objectid.ObjectId(todo_id)
    except bson.errors.InvalidId:
        abort(404)
    todo = db.todos.find_one({'_id': object_id})
    if not todo:
        abort(404)
    response = {
        'title': todo['title'].title(),
        'description': todo['description'],
        'links': {
            'self': request.base_url,
        },
    }
    return response, 200


@app.route('/todos/<todo_id>', methods=['PATCH'])
def edit_todo_by_id(todo_id):
    """Edit a specific Todo object by id"""
    try:
        object_id = bson.objectid.ObjectId(todo_id)
    except bson.errors.InvalidId:
        abort(404)
    todo = db.todos.find_one({'_id': object_id})
    if not todo:
        abort(404)
    else:
        description = request.json.get('description', '')

        if not description.isalnum():
            abort(422)
        else:
            todo = {
                'title': todo['title'].title(),
                'description': request.json.get('description', ''),
            }
            db.todos.update_one({'_id': object_id}, {"$set": {'description': description}}, upsert=False)

    response = {
        'title': todo['title'].title(),
        'description': todo['description'],
        'links': {
            'self': request.base_url,
        },
    }

    return response, 200


@app.route('/todos/<todo_id>', methods=['DELETE'])
def delete_todo_by_id(todo_id):
    """Delete a specific Todo object by id"""
    try:
        object_id = bson.objectid.ObjectId(todo_id)
    except bson.errors.InvalidId:
        abort(404)
    todo = db.todos.find_one({'_id': object_id})
    if not todo:
        abort(404)
    else:
        db.todos.delete_one(todo)
    response = {
        'title': todo['title'].title(),
        'description': todo['description'],
        'links': {
            'self': request.base_url,
        },
    }
    return response, 204


@app.route('/users', methods=['GET'])
def get_users():
    """Return a list of links to all User objects"""
    user_ids = db.users.find().distinct('_id')
    user_links = [
        '/'.join([request.base_url, str(user_id)]) for user_id in user_ids
    ]
    response = {
        'items': user_links,
        'links': {
            'self': request.base_url,
        },
    }
    return response, 200


@app.route('/users', methods=['POST'])
def create_user():
    """Create a new User object with email and optional name
    password must be secure
    Emails should be unique.
    """
    if 'email' not in request.json:
        abort(422)

    # encrypt password using SHA-512
    password = request.json['password']

    hashed_password = hashlib.sha512(password.encode('utf-8')).hexdigest()
    user = {
        'email': request.json['email'],
        'password': hashed_password,
        'name': request.json.get('name', ''),
    }

    response = user.copy()
    user_id = db.users.insert_one(user).inserted_id
    response['links'] = {
        'self': '/'.join([request.base_url, str(user_id)]),
    }
    return response, 201


@app.route('/users/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """Return a specific User object by id"""
    try:
        object_id = bson.objectid.ObjectId(user_id)
    except bson.errors.InvalidId:
        abort(404)
    user = db.users.find_one({'_id': object_id})
    if not user:
        abort(404)
    response = {
        'email': user['email'],
        'name': user['name'],
        'password': user['password'],
        'links': {
            'self': request.base_url,
        },
    }
    return response, 200


class TestGetTodoById(unittest.TestCase):
    def setUp(self):
        # Set up a Flask test client
        self.app = Flask(__name__)
        self.client = self.app.test_client()

    def tearDown(self):
        # Clean up after each test case
        pass

    @patch('app.bson.objectid.ObjectId')
    @patch('app.db.todos.find_one')
    def test_get_todo_by_valid_id(self, mock_find_one, mock_object_id):
        # Mock the dependencies
        mock_object_id.return_value = 'valid_id'
        mock_find_one.return_value = {
            '_id': 'valid_id',
            'title': 'Test Todo',
            'description': 'Test description'
        }

        # Set up any necessary request context
        with self.app.test_request_context():
            request.base_url = 'http://localhost:5000'

            # Call the function
            response, status_code = get_todo_by_id('valid_id')

            # Assert the results
            self.assertEqual(status_code, 200)
            self.assertEqual(response['title'], 'Test Todo')
            self.assertEqual(response['description'], 'Test description')
            self.assertEqual(response['links']['self'], 'http://localhost:5000')

    @patch('your_module.bson.objectid.ObjectId')
    def test_get_todo_by_invalid_id(self, mock_object_id):
        # Mock the dependencies
        mock_object_id.side_effect = abort(404)

        # Call the function
        with self.app.test_request_context():
            with self.assertRaises(abort):
                get_todo_by_id('invalid_id')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
    #unittest.main()
