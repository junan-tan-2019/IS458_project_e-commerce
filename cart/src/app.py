from flask import Flask, request, jsonify
import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from flask_cors import CORS
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
from aws_xray_sdk.core import patch

load_dotenv()

app = Flask(__name__)
CORS(app)

xray_recorder.configure(service='cart_service',
                        daemon_address="13.212.154.220:2000")
XRayMiddleware(app, xray_recorder)
libraries = (['boto3'])
patch(libraries)

app.config['CORS_HEADERS'] = 'Content-Type'

dynamodb = boto3.resource('dynamodb', region_name=os.getenv("REGION"),
                          aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                          aws_secret_access_key=os
                          .getenv("AWS_SECRET_ACCESS_KEY")
                          #   endpoint_url=os.getenv("DYNAMODB_URL")
                          )

# dynamodb = boto3.resource('dynamodb', region_name="us-east-1",
#                           endpoint_url=os.getenv("DYNAMODB_URL"))
TABLE_NAME = "Cart"
table = dynamodb.Table(TABLE_NAME)


def createNewCart(item):
    cart = []
    cart.append({"name": item["name"], "quantity": int(item["quantity"]),
                "itemType": item["itemType"],
                 "price": int(item["price"])})
    response = table.put_item(
        Item={
            'username': item['username'],
            'cart': cart
        }
    )
    return response


def addNewItem(item):
    response = table.update_item(
            Key={
                'username': item["username"]
            },

            UpdateExpression='SET #cart = list_append(:item, #cart)',
            ExpressionAttributeValues={
                ":item": [{"name": item["name"],
                          "quantity": int(item["quantity"]),
                           "itemType": item["itemType"],
                           "price": int(item["price"])}]
            },
            ExpressionAttributeNames={
                "#cart": "cart"
            },
            ReturnValues="UPDATED_NEW"
        )
    return response


def addExistItem(res):
    response = table.put_item(
        Item=res,
        ReturnValues='NONE'
    )
    return response


def updateCart(item, cart_res):
    cart_list = cart_res["Item"]["cart"]
    exist = False
    for cart_item in cart_list:
        if cart_item["name"] == item["name"]:
            cart_item["quantity"] += int(item["quantity"])
            # cart_item["itemType"] = item["itemType"]
            cart_item["price"] += int(item["price"])
            exist = True

    if (exist):
        print("hi")
        cart_res["Item"]["cart"] = cart_list
        response = addExistItem(cart_res["Item"])
    else:
        print("hello")
        response = addNewItem(item)

    return response


def getCart(username):
    response = table.get_item(Key={
        "username": username
    })
    return response


@app.route("/health")
def health_check():
    return jsonify(
            {
                "message": "Cart service is healthy!"
            }
    ), 200


@app.route("/add-to-cart", methods=['POST'])
def add_to_cart():
    item = request.get_json()
    try:
        cart_res = getCart(item["username"])
        if "Item" not in cart_res:
            response = createNewCart(item)
        else:
            # print("hello")
            response = updateCart(item, cart_res)
            # print(response)

    except ClientError as error:
        return error.response['Error']['Message'], 400
    else:
        return response
    # return dict(status="success", data=item), 200


@app.route("/get-cart", methods=["GET"])
def get_cart():
    username = request.args.get("username")
    try:
        response = getCart(username)
    except ClientError as error:
        return error.response['Error']['Message'], 400
    else:
        if "Item" in response:
            return response["Item"], 200
        return {"username": "username"}


def deleteCart(username):
    response = table.delete_item(Key={
        'username': username
    })
    return response


@app.route("/delete-cart", methods=["DELETE"])
def delete_cart():
    username = request.get_json(force=True)["username"]

    try:
        response = deleteCart(username)
    except ClientError as error:
        return error.response['Error']['Message'], 400
    else:
        return response


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5300)
