import json
import re
from datetime import datetime, timedelta
import hashlib, binascii
from secrets import token_hex
from flask import Flask, request
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

## FILE UPLOAD
import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/home/itha/Dev/ETNA/RTP-API/files'
# ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mkv'}
# ALLOWED_FORMATS = {1080, 720, 480, 360, 240}

## VIDEO LENGTH
import subprocess

def get_length(filename):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                            'format=duration', '-of',
                            'default=noprint_wrappers=1:nokey=1', filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return int(float(result.stdout)) + 1

## REGEX
wordRe = re.compile('[a-zA-Z0-9_-]{3,12}')
emailRe = re.compile('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$')

## APP
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user@localhost:3306/filesaving'
db = SQLAlchemy(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

## MODELS
class JsonableModel():
    def as_dict(self):
        return { c.name: getattr(self, c.name) for c in self.__table__.columns }


class User(db.Model, JsonableModel):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(45), unique=True, nullable=False)
    email = db.Column(db.String(45), unique=True, nullable=False)
    pseudo = db.Column(db.String(45), nullable=True)
    password = db.Column(db.String(45), nullable=False)
    created_at = db.Column(db.DateTime(), unique=False, nullable=False, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime(), unique=False, nullable=False, default=datetime.utcnow(), onupdate=datetime.utcnow())
    tokens = db.relationship('Token', cascade='all, delete-orphan')
    files = db.relationship('File', cascade='all, delete-orphan')

    def __repr__(self):
        return '<User %r>' % self.username


class Token(db.Model, JsonableModel):
    __tablename__ = 'token'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(45), unique=True, nullable=False)
    expired_at = db.Column(db.DateTime(), unique=False, nullable=False, default=datetime.utcnow() + timedelta(days=1))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
        nullable=False)
    user = db.relationship('User',
        backref=db.backref('owner_token', lazy=True))

    def __repr__(self):
        return '<user %r\'s token>' % self.user_id


class File(db.Model, JsonableModel):
    __tablename__ = 'file'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
        nullable=False)
    user = db.relationship('User',
        backref=db.backref('owner_files', lazy=True))
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(), unique=False, nullable=False, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime(), unique=False, nullable=False, default=datetime.utcnow(), onupdate=datetime.utcnow())
    private = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return '<File %r>' % self.source


def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        requestToken = request.headers.get('Authorization')
        tokenObj = Token.query.filter_by(code=requestToken).first()
        if not tokenObj:
            return {'message': 'Unauthorized'}, 401
        return f(*args, **kwargs)
    return decorated_function


def res_ownership_required(f):
    @wraps(f)
    def decorated_function(user_id, *args, **kwargs):
        requestToken = request.headers.get('Authorization')
        tokenObj = Token.query.filter_by(code=requestToken).first()
        if tokenObj:
            if tokenObj.user_id != user_id:
                return {'message': 'Forbidden'}, 403
        else:
            return {'message': 'Unauthorized'}, 401
        return f(user_id, *args, **kwargs)
    return decorated_function


def ownership(request, user_id):
    requestToken = request.headers.get('Authorization')
    tokenObj = Token.query.filter_by(code=requestToken).first()
    return tokenObj.user_id == user_id


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_error(message, code, data):
    return {
        'message': message,
        'code': code,
        'data': data
    }


def generate_pager_variables(item_list, page, perPage):
    length = len(item_list)
    total = int(length / perPage)
    total = total + 1 if length % perPage != 0 else total
    page = page if page <= total else total
    startIndex = perPage * (page - 1) if perPage * (page - 1) < length else length - perPage
    startIndex = startIndex if startIndex >= 0 else 0
    endIndex = startIndex + perPage
    return page, total, startIndex, endIndex


def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')


def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                provided_password.encode('utf-8'), 
                                salt.encode('ascii'), 
                                100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


@app.errorhandler(404)
def page_not_found(e):
    return {'message': 'Not Found'}, 404


@app.route('/user', methods=['POST'])
def post_user():
    if request.method == 'POST':
        if not request.json:
            return {'message': 'Bad Request', 'code': 10001, 'data': ['no json sent']}, 400
        username = request.json.get('username')
        email = request.json.get('email')
        pseudo = request.json.get('pseudo')
        password = request.json.get('password')
        if not username or not email or not password:
            error = 'missing either username, email or password'
        elif not wordRe.fullmatch(username) or not emailRe.fullmatch(email):
            error = 'either invalid username (3 to 12 chars, alphanumeric, dashes and underscores), or invalid email'
        elif (User.query.filter_by(username=username).first() is not None or
        User.query.filter_by(email=email).first() is not None):
            error = 'username or email already in use on another account'
        else:
            newUser = User(username=username,
                            email=email,
                            pseudo=pseudo,
                            password=hash_password(password))
            db.session.add(newUser)
            db.session.commit()
            return {'message': 'OK', 'data': newUser.as_dict()}, 201
        return {'message': 'Bad Request', 'code': 10001, 'data': [error]}, 400


@app.route('/auth', methods=['POST'])
def auth():
    if request.method == 'POST':
        if not request.json:
            return {'message': 'Bad Request', 'code': 10001, 'data': ['no json sent']}, 400
        login = request.json.get('login')
        password = request.json.get('password')
        error = None
        if not login or not password:
            error = 'missing either login, password or both'
        elif not isinstance(login, str) or not isinstance(password, str):
            error = 'login or password are not string, or both'
        if not error:
            relatedUser = User.query.filter_by(username=login).first()
            if relatedUser and verify_password(relatedUser.password, password):
                existingToken = Token.query.filter_by(user_id=relatedUser.id).first()
                if existingToken:
                    return {'message': 'OK', 'data': existingToken.as_dict()}, 200
                else:
                    newToken = Token(code=token_hex(16), user_id=relatedUser.id)
                    db.session.add(newToken)
                    db.session.commit()
                    return {'message': 'OK', 'data': newToken.as_dict()}, 201
            else:
                error = 'user referenced with this username and password does not exist'
        return {'message': 'Bad Request', 'code': 10001, 'data': [error]}, 400


@app.route('/user/<int:user_id>', methods=['DELETE', 'PUT', 'GET'])
@auth_required
def update_user(user_id):
    if request.method == 'DELETE':
        if ownership(request, user_id):
            userToDelete = User.query.filter_by(id=user_id).first()
            db.session.delete(userToDelete)
            db.session.commit()
            return {'message': 'OK'}, 204
        else:
            return {'message': 'Forbidden'}, 403

    if request.method == 'PUT':
        if ownership(request, user_id):
            if not request.json:
                return {'message': 'Bad Request', 'code': 10001, 'data': ['no json sent']}, 400
            username = request.json.get('username')
            email = request.json.get('email')
            pseudo = request.json.get('pseudo')
            password = request.json.get('password')
            if not username or not email or not password:
                error = 'missing either username, email or password'
            elif not wordRe.fullmatch(username) or not emailRe.fullmatch(email):
                error = 'either invalid username (3 to 12 chars, alphanumeric, dashes and underscores), or invalid email'
            elif (User.query.filter_by(username=username).first() and User.query.filter_by(username=username).first().id != user_id or
            User.query.filter_by(email=email).first() and User.query.filter_by(email=email).first().id != user_id):
                error = 'username or email already in use on another account'
            else:
                userToUpdate = User.query.filter_by(id=user_id).first()
                if userToUpdate:
                    userToUpdate.username = username
                    userToUpdate.email = email
                    userToUpdate.pseudo = pseudo
                    userToUpdate.password = hash_password(password)
                    db.session.commit()
                    return {'message': 'OK', 'data': userToUpdate.as_dict()}, 201
                else:
                    return {'message': 'Not Found'}, 404
            return {'message': 'Bad Request', 'code': 10001, 'data': [error]}, 400
        else:
            return {'message': 'Forbidden'}, 403

    if request.method == 'GET':
        user = User.query.filter_by(id=user_id).first()
        if user is not None:
            return {'message': 'OK', 'data': user.as_dict()}, 200
        else:
            return {'message': 'Not Found'}, 404


@app.route('/users', methods=['GET'])
def list_users():
    if request.method == 'GET':
        pseudo = None
        if request.json:
            pseudo = request.json.get('pseudo')
        page = request.args.get('page')
        perPage = request.args.get('perPage')
        try:
            if page:
                page = int(request.args.get('page'))
            page = 1 if page is None else page
            if perPage:
                perPage = int(request.args.get('perPage'))
            perPage = 5 if perPage is None else perPage
        except ValueError:
            return create_error('Bad Request', 400, ['either page, perPage or both of them are not integers']), 400

        if pseudo is not None:
            users = User.query.filter_by(pseudo=pseudo).order_by(text('id desc')).all()
        else:
            users = User.query.order_by(text('id desc')).all()
        page, total, startIndex, endIndex = generate_pager_variables(users, page, perPage)
        printableUsers = []
        for user in users:
            printableUsers.append(user.as_dict())
        if printableUsers:
            return { 'message': 'OK', 'data': printableUsers[startIndex:endIndex], 'pager': { 'current': page, 'total': total } }
        else:
            return create_error('Not Found', 404, ['No user was found']), 404


@app.route('/user/<int:user_id>/file', methods=['POST'])
@res_ownership_required
def upload_file(user_id):
    if request.method == 'POST':
        if not request.form:
            return {'message': 'Bad Request', 'code': 10001, 'data': ['no name sent']}, 400
        name = request.form.get('name')
        if 'file' not in request.files:
            return {'message': 'Bad Request', 'code': 10001, 'data': ['no file sent']}, 400
        file = request.files['file']
        if file.filename == '':
            return {'message': 'Bad Request', 'code': 10001, 'data': ['no selected file']}, 400
        if file:
            filename = secure_filename(name)
            i = 0
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], str(i) + '_' + filename)
            while (os.path.isfile(filepath)):
                i += 1
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], str(i) + '_' + filename)
            file.save(filepath)
            newFile = File(name=filename,
                            user_id=user_id,
                            path=str(i) + '_' + filename,
                            private=1)
            db.session.add(newFile)
            db.session.commit()
            return {'message': 'OK', 'data': newFile.as_dict()}
        else:
            return {'message': 'Bad Request', 'code': 10001, 'data': ['unknown error, check your request and try again later']}, 400


@app.route('/user/<int:user_id>/files', methods=['GET'])
def list_files_by_user(user_id):
    if request.method == 'GET':
        files = File.query.filter_by(user_id=user_id).order_by(text('id desc')).all()
        printableFiles = []
        for file in files:
            printableFiles.append(file.as_dict())
        if printableFiles:
            return {'message': 'OK', 'data': printableFiles}
        else:
            return {'message': 'Not Found'}, 404


@app.route('/file/<int:file_id>', methods=['PUT', 'DELETE'])
@auth_required
def update_file(file_id):
    if request.method == 'PUT':
        fileToUpdate = File.query.filter_by(id=file_id).first()
        if fileToUpdate:
            if ownership(request, fileToUpdate.user_id):
                name = None
                file = None
                # if not request.form:
                #     return {'message': 'Bad Request', 'code': 10001, 'data': ['no form sent']}, 400
                if request.form:
                    name = request.form.get('name')
                if request.files:
                    file = request.files['file']
                if not name and not file:
                    return {'message': 'Bad Request', 'code': 10001, 'data': ['no data sent']}, 400
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'],fileToUpdate.path))
                    i = 0
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], str(i) + '_' + filename)
                    while (os.path.isfile(filepath)):
                        i += 1
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], str(i) + '_' + filename)
                    try:
                        file.save(filepath)
                    except:
                        return {'message': 'Internal Server Error', 'data': ['could not save file to the server']}, 500
                    fileToUpdate.path = str(i) + '_' + filename
                if name:
                    fileToUpdate.name = secure_filename(name)
                db.session.commit()
                return {'message': 'OK', 'data': fileToUpdate.as_dict()}, 200
            else:
                return {'message': 'Forbidden'}, 403
        else:
            return {'message': 'Bad Request', 'code': 10001, 'data': ['resource does not exist']}, 400

    if request.method == 'DELETE':
        fileToDelete = File.query.filter_by(id=file_id).first()
        if fileToDelete:
            if ownership(request, fileToDelete.user_id):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'],fileToDelete.path))
                db.session.delete(fileToDelete)
                db.session.commit()
                return {'message': 'OK'}, 204
            else:
                return {'message': 'Forbidden'}, 403
        else:
            return {'message': 'Bad Request', 'code': 10001, 'data': ['resource does not exist']}, 400