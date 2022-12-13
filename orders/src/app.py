# from crypt import methods
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
import ast
import time
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
from aws_xray_sdk.core import patch

load_dotenv()

app = Flask(__name__)
CORS(app)

xray_recorder.configure(service='order_service',
                        daemon_address="13.212.154.220:2000")
XRayMiddleware(app, xray_recorder)
libraries = (['requests'])
patch(libraries)

GET_CART = os.getenv("GET_CART")
DELETE_CART = os.getenv("DELETE_CART")
UPDATE_STOCKS = os.getenv("UPDATE_STOCKS")
PAYMENT_LAMBDA = os.getenv("PAYMENT_LAMBDA")
PROCESS_ORDER = os.getenv("PROCESS_ORDER")
HOME_PAGE = os.getenv("HOME_PAGE")


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return json.JSONEncoder.default(self, o)


@app.route("/order", methods=["GET"])
def order():
    response = requests.get(GET_CART,
                            params={"username": "username"})
    data = response.json()

    cart = data["cart"]

    return render_template("order.html", username="username", cart=cart,
                           process_order_link=PROCESS_ORDER)


@app.route("/process_order", methods=["POST"])
def process_order():
    # name = request.form.get("name")
    address = request.form.get("address")
    delivery_date = request.form.get("delivery_date")
    username = request.form.get("username")
    cart = request.form.get("cart")
    cart = ast.literal_eval(cart)
    print(type(cart))
    for item in cart:
        item["quantity"] = int(item["quantity"])
        item["price"] = int(item["price"])

    datetime_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    expiryTimestamp = int(time.time() + 24*3600*7)
    data = {
        "username": username,
        "cart": cart,
        "date": datetime_now,
        "delivery_date": delivery_date,
        "delivery_address": address,
        "ttl": expiryTimestamp
    }
    print(data)
    payment_response = requests.post(PAYMENT_LAMBDA, json=data)
    if payment_response.status_code:
        cart_response = requests.delete(DELETE_CART,
                                        data=json.dumps({
                                            "username": username
                                            }))
        if cart_response.status_code == 200:
            store_response = requests.post(UPDATE_STOCKS,
                                           data=json.dumps(cart,
                                                           cls=DecimalEncoder))

            if store_response.status_code == 200:
                return render_template("success.html", home_page=HOME_PAGE)
        # return render_template("success.html")
    return render_template("failure.html", home_page=HOME_PAGE)


@app.route("/health")
def health_check():
    return jsonify(
            {
                "message": "Order service is healthy."
            }
    ), 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5200, debug=True)
