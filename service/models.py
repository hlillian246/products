"""
Models for Product

All of the models are stored in this module
"""
import logging
from flask_sqlalchemy import SQLAlchemy


# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()

class DataValidationError(Exception):
    """ Used for an data validation errors when deserializing """
    pass


class Product(db.Model):
    """
    Class that represents a product
    """

    logger = logging.getLogger(__name__)
    app = None
    ##################################################
    # Table Schema
    ##################################################

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63),nullable = False)
    description = db.Column(db.String(256),nullable = False)
    category = db.Column(db.String(63),nullable = False)
    price = db.Column(db.Float,nullable = False)

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return "<<Product> %r id=[%s] %r %r %f >" % (self.name, self.id, self.description, self.category, self.price)


    def serialize(self):
        """ Serializes a Product into a dictionary """
        return {
            "id": self.id,
            "name": self.name,
            "description" : self.description,
            "category": self.category,
            "price": self.price
        }

    def deserialize(self, data):
        """
        Deserializes a Product from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.name = data["name"]
            self.description = data["description"]
            self.category = data["category"]
            self.price = data["price"]

        except KeyError as error:
            raise DataValidationError("Invalid product : missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError(
                "Invalid product: body of request contained bad or no data"
            )
        return self

    @classmethod
    def init_db(cls, app):
        """ Initializes the database session """
        cls.logger.info("Initializing database")
        cls.app = app
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables