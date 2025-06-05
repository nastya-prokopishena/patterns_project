import unittest
import mongomock
from unittest.mock import patch, MagicMock
from models import Database, User, RegularBike, ElectricBike, save_user, save_bike_order
from facades import BikeShopFacade
from builders import BikeBuilder
from app import app, mail
import os


class TestBikeShop(unittest.TestCase):
    def setUp(self):
        # Mock MongoDB using mongomock
        self.client = mongomock.MongoClient()
        self.db = Database()
        self.db.client = self.client
        self.db.db = self.client['bike_shop']
        self.db.users_collection = self.db.db['users']
        self.db.orders_collection = self.db.db['orders']

        # Set up Flask test client
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

        # Mock Flask-Mail
        self.mail_patcher = patch('app.mail.send')
        self.mock_send = self.mail_patcher.start()

    def tearDown(self):
        self.mail_patcher.stop()
        self.db.users_collection.delete_many({})
        self.db.orders_collection.delete_many({})

    def test_database_singleton_same_instance(self):
        db1 = Database()
        db2 = Database()
        self.assertIs(db1, db2, "Database instances should be the same (Singleton)")


    def test_database_initialized_once(self):
        db1 = Database()
        db2 = Database()
        self.assertEqual(db1.db.name, db2.db.name)
        self.assertEqual(db1.users_collection.name, db2.users_collection.name)

    def test_user_to_dict(self):
        user = User(email="test@example.com", name="Test User", password="password123")
        expected = {
            'email': "test@example.com",
            'name': "Test User",
            'password': "password123"
        }
        self.assertEqual(user.to_dict(), expected)

    def test_regular_bike_is_not_electric(self):
        bike = RegularBike(bike_type="Mountain", color="Blue")
        self.assertFalse(bike.is_electric)
        self.assertEqual(bike.bike_type, "Mountain")
        self.assertEqual(bike.color, "Blue")

    def test_electric_bike_is_electric(self):
        bike = ElectricBike(bike_type="City", color="Red")
        self.assertTrue(bike.is_electric)
        self.assertEqual(bike.bike_type, "City")
        self.assertEqual(bike.color, "Red")

    def test_bike_builder_valid_regular_bike(self):
        builder = BikeBuilder()
        bike = builder.set_electric(False).set_bike_type("Road").set_color("Black").build()
        self.assertIsInstance(bike, RegularBike)
        self.assertEqual(bike.bike_type, "Road")
        self.assertEqual(bike.color, "Black")
        self.assertFalse(bike.is_electric)

    def test_bike_builder_valid_electric_bike(self):
        builder = BikeBuilder()
        bike = builder.set_electric(True).set_bike_type("Hybrid").set_color("Green").build()
        self.assertIsInstance(bike, ElectricBike)
        self.assertEqual(bike.bike_type, "Hybrid")
        self.assertEqual(bike.color, "Green")
        self.assertTrue(bike.is_electric)

    def test_bike_builder_missing_fields(self):
        builder = BikeBuilder()
        with self.assertRaises(ValueError):
            builder.set_electric(False).set_color("Blue").build()

    def test_bike_builder_no_bike_initialized(self):
        builder = BikeBuilder()
        with self.assertRaises(ValueError):
            builder.set_bike_type("Road").build()

    def test_validate_user_data_valid(self):
        user_data = {
            'email': "test@example.com",
            'name': "John Doe",
            'password': "secure123"
        }
        self.assertTrue(BikeShopFacade.validate_user_data(user_data))

    def test_validate_user_data_invalid_email(self):
        user_data = {
            'email': "invalid-email",
            'name': "John Doe",
            'password': "secure123"
        }
        self.assertFalse(BikeShopFacade.validate_user_data(user_data))

    def test_validate_user_data_short_name(self):
        user_data = {
            'email': "test@example.com",
            'name': "J",
            'password': "secure123"
        }
        self.assertFalse(BikeShopFacade.validate_user_data(user_data))

    def test_validate_user_data_short_password(self):
        user_data = {
            'email': "test@example.com",
            'name': "John Doe",
            'password': "12345"
        }
        self.assertFalse(BikeShopFacade.validate_user_data(user_data))


    def test_register_user_invalid_data(self):
        user = User(email="invalid", name="T", password="123")
        with self.assertRaises(ValueError):
            BikeShopFacade.register_user(user)

    def test_create_bike_order(self):
        bike_data = {'bike_type': "Mountain", 'color': "Blue", 'is_electric': False}
        user_id = "12345"
        result = BikeShopFacade.create_bike_order(bike_data, user_id)
        order = self.db.orders_collection.find_one({'_id': result.inserted_id})
        self.assertEqual(order['bike_type'], "Mountain")
        self.assertEqual(order['color'], "Blue")
        self.assertEqual(order['user_id'], user_id)

    def test_login_user_success(self):
        user = User(email="test@example.com", name="Test User", password="password123")
        save_user(user)
        login_data = {'email': "test@example.com", 'password': "password123"}
        user_id = BikeShopFacade.login_user(login_data)
        self.assertIsNotNone(user_id)

    def test_login_user_invalid_credentials(self):
        login_data = {'email': "test@example.com", 'password': "wrongpassword"}
        user_id = BikeShopFacade.login_user(login_data)
        self.assertIsNone(user_id)

    def test_get_user_orders(self):
        user_id = "12345"
        bike_data = {'bike_type': "Mountain", 'color': "Blue", 'is_electric': False, 'user_id': user_id}
        save_bike_order(bike_data, user_id)
        orders = BikeShopFacade.get_user_orders(user_id)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['bike_type'], "Mountain")

    def test_register_route_success(self):
        response = self.app.post('/register', data={
            'email': "test@example.com",
            'name': "Test User",
            'password': "password123"
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/bike-selection'))

    def test_bike_selection_route_unauthenticated(self):
        response = self.app.get('/bike-selection', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/register'))

    def test_login_route_success(self):
        # Setup - create a test user
        user = User(email="test@example.com", name="Test User", password="password123")
        save_user(user)

        # Execute
        response = self.app.post('/login', data={
            'email': "test@example.com",
            'password': "password123"
        }, follow_redirects=False)

        # Verify
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/'))


if __name__ == '__main__':
    unittest.main()