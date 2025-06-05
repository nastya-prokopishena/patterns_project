import re
import logging
from models import Database, save_user, save_bike_order
from flask_mail import Message

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class BikeShopFacade:
    @staticmethod
    def validate_user_data(user_data):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return (
                user_data.get('email') and
                re.match(email_regex, user_data['email']) is not None and
                user_data.get('name') and len(user_data['name']) >= 2 and
                user_data.get('password') and len(user_data['password']) >= 6
        )

    @staticmethod
    def register_user(user):
        from app import app, mail
        if not BikeShopFacade.validate_user_data(user.to_dict()):
            raise ValueError('Невірні дані користувача')

        result = save_user(user)
        try:
            with app.app_context():
                msg = Message(
                    subject="Підтвердження реєстрації",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[user.email]
                )
                msg.body = f"Вітаємо, {user.name}! Ви успішно зареєструвались у магазині велосипедів."
                mail.send(msg)
                logger.debug(f"Email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {str(e)}")
            # Continue execution even if email fails
        return result

    @staticmethod
    def create_bike_order(bike_data, user_id=None):
        return save_bike_order(bike_data, user_id)

    @staticmethod
    def login_user(login_data):
        db = Database()
        user = db.users_collection.find_one({
            'email': login_data['email'],
            'password': login_data['password']
        })
        return user['_id'] if user else None

    @staticmethod
    def get_user_orders(user_id):
        db = Database()
        orders = db.orders_collection.find({'user_id': user_id})
        return list(orders)