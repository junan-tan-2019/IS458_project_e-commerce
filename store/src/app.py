from flask import Flask, request, jsonify, render_template, session, redirect
from flask import url_for
from flask_cors import CORS
import boto3
import redis
import os
from decimal import Decimal
import json
import requests
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
from aws_xray_sdk.core import patch

load_dotenv()

dynamodb = boto3.resource('dynamodb', region_name=os.getenv("REGION"),
                          aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                          aws_secret_access_key=os
                          .getenv("AWS_SECRET_ACCESS_KEY")
                          #   endpoint_url=os.getenv("DYNAMODB_URL")
                          )

TABLE_NAME = "Items"
table = dynamodb.Table(TABLE_NAME)
redis_client = redis.Redis(os.getenv("REDIS_URL"), port=6379)


app = Flask(__name__)
CORS(app)

xray_recorder.configure(service='store_service',
                        daemon_address="54.151.221.119:2000")
XRayMiddleware(app, xray_recorder)
libraries = (['boto3', 'requests'])
patch(libraries)

HOME_PAGE = os.getenv('HOME_PAGE')
SIGNUP_PAGE = os.getenv("SIGNUP_PAGE")
BOOKLIST_PAGE = os.getenv("BOOKLIST_PAGE")
STATIONERY_PAGE = os.getenv("STATIONERY_PAGE")
FILE_PAGE = os.getenv("FILE_PAGE")
STORE_CART = os.getenv("STORE_CART")
GET_CART = os.getenv("GET_CART")
CART_SERVICE = os.getenv("CART_SERVICE")
ORDER_SERVICE = os.getenv("ORDER_SERVICE")
COGNITO_UI_URL = os.getenv("BASE_COGNITO_UI_URL") + HOME_PAGE


@app.route("/home")
def home():
    '''
        3 Cases:
        1) Unauthenticated user (guest) - show homepage with Log In link
        - no code
        - no session variable

        2) Newly logged-in user - redirect
        - code
        - store session variable
        - redirect and check session variable

        3) Logged-in user - show homepage with username
        - no code
        - has session variable
        - check session variable
    '''

    # Check: Case 3
    if "username" in session:
        username = session["username"]
        return homepage_template(username, 1, 0)

    # Check: Case 2
    if (request.args.get("code")):
        id_token = ""
        access_token = ""
        refresh_token = ""
        username = ""
        # Exchange code for tokens
        get_tokens = requests.post(os.getenv("USERS_API") +
                                   "/users/user-details/token",
                                   data=json.dumps({
                                    "code": request.args.get("code")}))
        if (get_tokens.status_code == 200):
            get_tokens = get_tokens.json()
            if (get_tokens):
                print(get_tokens)
                id_token = get_tokens["id_token"]
                access_token = get_tokens["access_token"]
                refresh_token = get_tokens["refresh_token"]
            else:
                # Auth code expired, login required
                print("Authorization code has expired")

                # Flush cache
                session.pop('username', None)
                session.pop('id_token', None)
                session.pop('access_token', None)
                session.pop('refresh_token', None)

                # Return page with message to login again
                return homepage_template("", 0, 1)
        else:
            # TODO: Better error handling
            print("Token exchange failed")

        # Unpack id_token for username
        # TODO: Break reliance on previous call
        get_username = requests.post(os.getenv("USERS_API") +
                                     "/users/user-details/username",
                                     data=json.dumps({"token": id_token}))
        if (get_username.status_code == 200):
            get_username = get_username.json()
            if (get_username):
                print(get_username)
                username = get_username["body"]
            else:
                # TODO: Better error handling
                print("get_username returns null")
        else:
            # TODO: Better error handling
            print("Username retrieval failed")

        # Store credentials in session
        session["id_token"] = id_token
        session["access_token"] = access_token
        session["refresh_token"] = refresh_token
        session["username"] = username

        # Redirect to regular url
        return (redirect(url_for("home")))

    # Fallback: Case 1
    return homepage_template("", 0, 0)


@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html", signup_page=SIGNUP_PAGE)


@app.route("/sign_up")
def sign_up():
    return render_template("sign_up.html")


@app.route("/health")
def health_check():
    return jsonify(
            {
                "message": "Store service is healthy!"
            }
    ), 200


def fetch_items_from_cache(item_type):
    response = redis_client.get(item_type)
    if response:
        items = json.loads(response)
        return items
    return None


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return json.JSONEncoder.default(self, o)


def store_items_in_cache(itemType, items):
    redis_client.set(itemType, json.dumps(items, cls=DecimalEncoder), ex=900)


@app.route("/view/<itemType>", methods=['GET'])
def view_items(itemType):

    cache_items = fetch_items_from_cache(itemType)
    if cache_items:

        return render_template("items.html", items=cache_items,
                               username="username",
                               store_cart=STORE_CART,
                               homepage=HOME_PAGE,
                               bookpage=BOOKLIST_PAGE,
                               stationerypage=STATIONERY_PAGE,
                               cart_link=CART_SERVICE,
                               filepage=FILE_PAGE)

    try:
        # Assuming itemType is the partition key
        response = table.query(
            KeyConditionExpression=Key('itemType').eq(itemType))
    except ClientError as err:
        return err.response['Error']['Message'], 400
    else:
        items = response["Items"]
        for item in items:
            item['id'] = item['name'].replace(' ', '-')

        store_items_in_cache(itemType, items)

        return render_template("items.html", items=items, username="username",
                               store_cart=STORE_CART,
                               homepage=HOME_PAGE,
                               bookpage=BOOKLIST_PAGE,
                               stationerypage=STATIONERY_PAGE,
                               cart_link=CART_SERVICE,
                               filepage=FILE_PAGE)


@app.route("/view/<itemType>/<name>", methods=['GET'])
def viewItem(item_type, name):
    try:
        key_name = name.replace('-', ' ')
        response = table.get_item(Key={
            "name": key_name,
            "itemType": item_type
        })
    except ClientError as err:
        return err.response['Error']['Message'], 400
    else:
        return response['Item'], 200


@app.route("/get-cart", methods=["GET"])
def get_cart():
    response = requests.get(GET_CART,
                            params={"username": "username"})

    return render_template("cart.html", cart_items=response.json(),
                           username=response.json()["username"],
                           store_cart=STORE_CART,
                           homepage=HOME_PAGE,
                           bookpage=BOOKLIST_PAGE,
                           stationerypage=STATIONERY_PAGE,
                           filepage=FILE_PAGE,
                           order_service=ORDER_SERVICE)


def update_stmt(item):
    update_request = {
        "Update": {
            "ConditionExpression": "#quantity > :limit AND #quantity >= :buy",
            "ExpressionAttributeNames": {"#quantity": "quantity"},
            "ExpressionAttributeValues": {
                ":buy": item["quantity"],
                ":limit": 0
            },
            "Key": {
                'name': item["name"],
                'itemType': item["itemType"]
            },
            "TableName": TABLE_NAME,
            "UpdateExpression": "SET #quantity = #quantity - :buy"
        },
            }
    return update_request


@app.route("/updateStocks", methods=['POST'])
def updateStocks():
    # content = request.get_json(force=True)
    content = json.loads(request.data, strict=False)
    transact_items = []
    # content = ast.literal_eval(content)
    if (isinstance(content, list)):
        for item in content:
            transact_items.append(update_stmt(item))
    else:
        return {"error": "content not a list"}, 400

    # return transact_items
    try:
        response = table.meta.client.transact_write_items(
            TransactItems=transact_items)
    except ClientError as error:
        return error.response['Error']['Message'], 400
    else:
        return response


def homepage_template(username, loggedIn, accessExpired):
    return render_template("home.html",
                           username=username,
                           signin=COGNITO_UI_URL,
                           store_cart=STORE_CART,
                           homepage=HOME_PAGE,
                           bookpage=BOOKLIST_PAGE,
                           stationerypage=STATIONERY_PAGE,
                           cart_link=CART_SERVICE,
                           filepage=FILE_PAGE,
                           loggedIn=loggedIn,
                           accessExpired=accessExpired)


if __name__ == "__main__":
    app.secret_key = os.getenv("APP_SECRET_KEY")
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host='0.0.0.0', port=5000)
