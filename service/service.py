"""
My Service

Describe what your service does here
"""

import os
#import sys
#import logging
#import json
import requests
from flask import Flask, jsonify, request, url_for, make_response, abort
from flask_api import status  # HTTP Status Codes
from werkzeug.exceptions import NotFound

# For this example we'll use SQLAlchemy, a popular ORM that supports a
# variety of backends including SQLite, MySQL, and PostgreSQL
#from flask_sqlalchemy import SQLAlchemy
from service.models import Product, DataValidationError

# Import Flask application
from . import app

SHOPCART_ENDPOINT = os.getenv('SHOPCART_ENDPOINT', 'http://localhost:5000/shopcarts')
######################################################################
# Error Handlers
######################################################################

@app.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles Value Errors from bad data """
    return bad_request(error)

@app.errorhandler(status.HTTP_400_BAD_REQUEST)
def bad_request(error):
    """ Handles bad reuests with 400_BAD_REQUEST """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_400_BAD_REQUEST, error="Bad Request", message=message
        ),
        status.HTTP_400_BAD_REQUEST,
    )

@app.errorhandler(status.HTTP_404_NOT_FOUND)
def not_found(error):
    """ Handles resources not found with 404_NOT_FOUND """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_404_NOT_FOUND, error="Not Found", message=message
        ),
        status.HTTP_404_NOT_FOUND,
    )


@app.errorhandler(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
def mediatype_not_supported(error):
    """ Handles unsuppoted media requests with 415_UNSUPPORTED_MEDIA_TYPE """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            error="Unsupported media type",
            message=message,
        ),
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    )

######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """ Root URL response """
    return "Welcome to the flask service for the Products team", status.HTTP_200_OK

######################################################################
# LIST ALL PRODUCTS
######################################################################
@app.route("/products", methods=["GET"])
def list_products():
    """ Returns all of the Products """
    app.logger.info("Request for product list")
    products = []
    
    category = request.args.get("category")
    name = request.args.get("name")
    description = request.args.get("description")

    if category:
        products = Product.find_by_category(category)
    elif name:
        products = Product.find_by_name(name)
    elif description:
        products = Product.find_by_description(description)
    else:
        products = Product.all()
    
    results = [product.serialize() for product in products]
    app.logger.info("Returning %d products", len(results))
    return make_response(jsonify(results), status.HTTP_200_OK)

######################################################################
# QUERY PRODUCTS BY PRICE RANGE
######################################################################
@app.route("/products/price", methods=["GET"])
def query_product_by_price():
    """ List all the product by their price range """
    app.logger.info("Querying products by provided price range")
    products = []

    minimum = request.args.get('minimum')
    maximum = request.args.get('maximum')
    if maximum is None or minimum is None:
        return request_validation_error("Minimum and Maximum cannot be empty")

    products = Product.query_by_price(minimum, maximum)

    results = [product.serialize() for product in products]
    app.logger.info("Returning %d products", len(results))
    return make_response(jsonify(results), status.HTTP_200_OK)

######################################################################
# ADD A NEW PRODUCT
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """
    Creates a Products
    This endpoint will create a Product based the data in the body that is posted
    """
    app.logger.info("Request to create a product")
    check_content_type("application/json")
    product = Product()
    product.deserialize(request.get_json())
    product.create()
    message = product.serialize()

    location_url = url_for("get_products", product_id=product.id, _external=True)

    app.logger.info("Product with ID [%s] created.", product.id)

    return make_response(jsonify(message), status.HTTP_201_CREATED, {"Location": location_url})

######################################################################
# READ A PRODUCT
######################################################################
@app.route("/products/<int:product_id>", methods=["GET"])
def get_products(product_id):
    """
    Read a product
    This endpoint will return a product based on its id
    """
    app.logger.info("Request for product with id: %s", product_id)
    product = Product.find(product_id)
    if not product:
        raise NotFound("Product with id '{}' was not found.".format(product_id))

    app.logger.info("Returning product: %s", product.name)
    return make_response(jsonify(product.serialize()), status.HTTP_200_OK)

######################################################################
# DELETE A PRODUCT
######################################################################

@app.route("/products/<int:product_id>", methods=["DELETE"])

def delete_products(product_id):
    """
    Delete a Product
    This endpoint will delete a product based the id specified in the path
    """
    app.logger.info("Request to delete product with id: %s", product_id)
    product = Product.find(product_id)
    if product:
        product.delete()

    app.logger.info("Product with ID [%s] delete complete.", product_id)
    return make_response("", status.HTTP_204_NO_CONTENT)

######################################################################
# UPDATE AN EXISTING PRODUCT
######################################################################
@app.route("/products/<int:product_id>", methods=["PUT"])
def update_products(product_id):
    """
    Update a product
    This endpoint will update a product based on the request body
    """
    app.logger.info("Request to update product with id: %s", product_id)
    check_content_type("application/json")
    product = Product.find(product_id)
    if not product:
        raise NotFound("Product with id '{}' was not found.".format(product_id))
    product.deserialize(request.get_json())
    product.id = product_id
    product.update()

    app.logger.info("Product with ID [%s] updated.", product.id)
    return make_response(jsonify(product.serialize()), status.HTTP_200_OK)

######################################################################
# PURCHASE AN EXISTING PRODUCT
######################################################################
@app.route("/products/<int:product_id>/purchase", methods=["POST"])
def purchase_products(product_id):
    """
    Purchase a product
    This endpoint will purchase a product based on the request body which should include the amount, user id, and shopcart id
    """
    app.logger.info("Request to purchase product with id: %s", product_id)
    check_content_type("application/json")
    product = Product.find(product_id)
    if not product:
        raise NotFound("Product with id '{}' was not found.".format(product_id))
    request_body = request.get_json()
    amount_update = request_body['amount']
    shopcart_id = request_body['shopcart_id']
    shopcart_exists = requests.get(SHOPCART_ENDPOINT, json=request_body)
    if shopcart_exists.status_code == 200:
        new_item = {}
        new_item["id"] = None
        new_item["sid"] = shopcart_id
        new_item["sku"] = product_id
        new_item["amount"] = amount_update
        product = product.serialize()
        new_item["name"] = product["name"]
        new_item["price"] = product["price"]
        new_item["create_time"] = None
        new_item["update_time"] = None
        add_into_shopcart = requests.post(SHOPCART_ENDPOINT + "/{}/items".format(shopcart_id), json=new_item)
        if add_into_shopcart.status_code == 200:
            return make_response("Product successfully added into the shopping cart", status.HTTP_200_OK)
    return make_response("Product was not added in the shopping cart because shopcart does not exist", status.HTTP_404_NOT_FOUND)



######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################

def init_db():
    """ Initialies the SQLAlchemy app """
    global app
    Product.init_db(app)

def check_content_type(content_type):
    """ Checks that the media type is correct """
    if request.headers["Content-Type"] == content_type:
        return
    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(415, "Content-Type must be {}".format(content_type))
