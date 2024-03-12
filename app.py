from flask import Flask, request, json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import database_exists, create_database
import csv
import uuid
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["20 per minute"],
    storage_uri="memory://",
)

app.app_context().push()


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Pranove*2@localhost:3306/api_rate_limiter'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
appHeaders = {'access-control-allow-credentials': 'true', 'access-control-allow-headers': 'X-Requested-With,Content-Type,Accept,Origin', 'access-control-allow-methods': '*', 'access-control-allow-origin': '*', 'cache-control': 'no-cache', 'content-enconding': 'gzip', 'content-type': 'application/json;charset=utf-8', 'etag' : 'W/"a9-N/X4JXf/69QQSQ1CLHMNPzj473I"', 'expires': '-1'} 
appHeadersHealthZ = {'cache-control': 'no-cache, no-store, must-revalidate'}
app.app_context().push()

db = SQLAlchemy(app)

if not database_exists(db.engine.url):
    create_database(db.engine.url)

class Users(db.Model):
    username = db.Column("username", db.String(100), nullable=False)
    api_key = db.Column("api_key", db.String(100), primary_key=True, default=uuid.uuid4, nullable=False)
    rate_limit = db.Column("rate_limit", db.Integer, nullable=False, default=100)
    request_count = db.Column("request_count", db.Integer, nullable=False, default=0)
    date_created = db.Column("date_created", db.DateTime, server_default=db.func.now(), nullable=False)

    def __init__(self, username, api_key, rate_limit, date_created):
        self.username = username
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.date_created = date_created
    
@app.errorhandler(404)
def notFound(error):
    response = app.response_class(status = 404, headers = appHeaders)
    return response

@app.errorhandler(405)
def methodNotAllowed(error):
    response = app.response_class(status = 405, headers = appHeaders)
    return response

@app.after_request
def handle405(response):
    if request.endpoint != 'healthz' and response.status_code == 404 and request.method != 'GET':
        response = app.response_class(status = 405, headers = appHeaders)
    return response  

def checkUser(username, api_key):
    user = Users.query.filter_by(username=username, api_key=api_key).first()
    if user != None:
        return True
    else:
        return False

@app.route('/healthcheck', methods=['GET'])
def healthz():
    if request.method == 'GET':
        if request.args or request.data:
            response = app.response_class(status=400, headers=appHeadersHealthZ)
            return response
        else:
            try:
                connection = db.engine.connect()
                if connection:
                    response = app.response_class(status=200, headers=appHeadersHealthZ)
                    connection.close()
                    return response
            except:
                response = app.response_class(status=503, headers=appHeadersHealthZ)
                return response
            response = app.response_class(status=200, headers=appHeadersHealthZ)
            return response


@app.route('/v1/users', methods=['POST'])
def onboard_user():
    if request.method == 'POST':
        if request.args:
            response = app.response_class(status=400, headers=appHeaders)
            return response
        else:
            username = request.json.get('username')
            existing_user = Users.query.filter_by(username=username).first()
            if existing_user is None:
                user = Users(username=username, api_key=uuid.uuid4(), rate_limit=20, date_created=datetime.now())
                db.session.add(user)
                db.session.commit()
                responseData = [{
                    "username": user.username,
                    "api_key": user.api_key,
                    "rate_limit": user.rate_limit,
                    "date_created": user.date_created.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                }]
                response = app.response_class(status=201, headers=appHeaders, response=json.dumps(responseData))
                return response
            else:
                response = app.response_class(status=409, headers=appHeaders)
                return response
    

@app.route('/v1/users/<username>', methods=['GET', 'DELETE'])
def get_or_delete_api_key(username):
    if request.method == 'GET':
        if request.args or request.data:
            response = app.response_class(status=400, headers=appHeaders)
            return response
        else:
            user = Users.query.filter_by(username=username).first()
            if user != None:
                responseData = [{
                    "username": user.username,
                    "api_key": user.api_key,
                    "rate_limit": user.rate_limit,
                    "date_created": user.date_created.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                }]
                response = app.response_class(status=200, headers=appHeaders, response=json.dumps(responseData))
                return response
            else:
                response = app.response_class(status=404, headers=appHeaders)
                return response
    
    if request.method == 'DELETE':
        if request.args or request.data:
            response = app.response_class(status=400, headers=appHeaders)
            return response
        else:
            user = Users.query.filter_by(username=username).first()
            print(user)
            if user != None:
                db.session.delete(user)
                db.session.commit()
                response = app.response_class(status=204, headers=appHeaders)
                return response
            else:
                print("here")
                response = app.response_class(status=404, headers=appHeaders)
                return response
    

@app.route('/v1/users/validate', methods=['POST'])
def validate_user():
    if request.method == 'POST':
        if request.args:
            response = app.response_class(status=400, headers=appHeaders)
            return response
        else:
            username = request.authorization.username
            api_key = request.headers.get('X-API-KEY')
            print(username, api_key)
            if checkUser(username, api_key):
                response = app.response_class(status=200, headers=appHeaders)
                return response
            else:
                response = app.response_class(status=401, headers=appHeaders)
                return response


def get_rate_limit(username, api_key):
    if checkUser(username, api_key):
        user = Users.query.filter_by(username=username, api_key=api_key).first()
        return user.rate_limit, user.request_count
    else:
        return 0
    
def can_request(rate_limit):
    if rate_limit > 0:
        return True
    else:
        return False
    
    
def increment_request_count(username, api_key):
    if checkUser(username, api_key):
        user = Users.query.filter_by(username=username, api_key=api_key).first()
        user.request_count += 1
        db.session.commit()
        return user.request_count
    else:
        return 0
    
# an api to print data from calling https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&hourly=temperature_2m and return the response. Rate limit is 20 requests per minute. use flask-limiter to implement rate limiting.
# The rate limit is 20 requests per minute
@app.route('/v1/forecast', methods=['GET'])
@limiter.limit("20 per minute")
def get_forecast():
    if request.method == 'GET':
                    # Construct the Open Meteo API URL
            api_url = "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&hourly=temperature_2m"

            # Get rate limit from the database based on the authenticated user
            username = request.authorization.username
            api_key = request.headers.get('X-API-KEY')
            rate_limit, request_count = get_rate_limit(username, api_key)

            # Perform the API request only if the user has available requests within the rate limit
            if request_count <= rate_limit:
                try:
                    # Make the API request
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        # Increment the request count for the user
                        increment_request_count(username, api_key)
                        return response.text, response.status_code, {'Content-Type': 'application/json'}
                    else:
                        # Handle non-200 status codes
                        return response.text, response.status_code, {'Content-Type': 'application/json'}
                except Exception as e:
                    # Handle exceptions during the API request
                    return str(e), 500, {'Content-Type': 'application/json'}
            else:
                # Return 429 Too Many Requests if the user has exceeded the rate limit
                return '{"error": "Rate limit exceeded. Please try again later."}', 429, {'Content-Type': 'application/json'}






if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)