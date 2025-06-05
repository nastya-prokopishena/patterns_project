import os
from pymongo import MongoClient
from bson.objectid import ObjectId

class Database:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, connection_string=None):
        if not self._initialized:
            connection_string = connection_string or os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
            self.client = MongoClient(connection_string)
            self.db = self.client['bike_shop']
            self.users_collection = self.db['users']
            self.orders_collection = self.db['orders']
            self._initialized = True

class User:
    def __init__(self, email, name, password):
        self.email = email
        self.name = name
        self.password = password

    def to_dict(self):
        return {
            'email': self.email,
            'name': self.name,
            'password': self.password
        }

class Product:
    def __init__(self, bike_type=None, color=None):
        self.bike_type = bike_type
        self.color = color

class RegularBike(Product):
    def __init__(self, bike_type=None, color=None):
        super().__init__(bike_type, color)
        self.is_electric = False

class ElectricBike(Product):
    def __init__(self, bike_type=None, color=None):
        super().__init__(bike_type, color)
        self.is_electric = True

def save_user(user):
    db = Database()
    return db.users_collection.insert_one(user.to_dict())

def save_bike_order(bike_data, user_id=None):
    db = Database()
    return db.orders_collection.insert_one({
        'bike_type': bike_data['bike_type'],
        'color': bike_data['color'],
        'is_electric': bike_data.get('is_electric', False),
        'user_id': user_id
    })
