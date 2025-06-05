from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from builders import BikeBuilder
from facades import BikeShopFacade
from models import User
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail(app)

@app.route('/')
def index():
    return render_template('base.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(
            email=request.form['email'],
            name=request.form['name'],
            password=request.form['password']
        )
        try:
            result = BikeShopFacade.register_user(user)
            session['user_id'] = str(result.inserted_id)
            flash('Реєстрація успішна! Перевірте вашу пошту для підтвердження.')
            return redirect(url_for('bike_selection'))
        except ValueError as e:
            flash(str(e))
    return render_template('register.html')


@app.route('/bike-selection', methods=['GET', 'POST'])
def bike_selection():
    if 'user_id' not in session:
        flash('Спочатку увійдіть або зареєструйтесь')
        return redirect(url_for('register'))

    if request.method == 'POST':
        try:
            bike_builder = BikeBuilder()
            bike_data = {
                'bike_type': request.form['bike_type'],
                'color': request.form['color'],
                'is_electric': 'is_electric' in request.form
            }

            bike = (bike_builder
                    .set_electric(bike_data['is_electric'])
                    .set_bike_type(bike_data['bike_type'])
                    .set_color(bike_data['color'])
                    .build())

            BikeShopFacade.create_bike_order(
                bike_data,
                session.get('user_id')
            )

            flash(f"Замовлено велосипед: {bike.bike_type}, {bike.color}")
            return redirect(url_for('index'))
        except ValueError as e:
            flash(str(e))

    return render_template('bike_selection.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Ви вийшли з системи')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_data = {
            'email': request.form['email'],
            'password': request.form['password']
        }

        try:
            user_id = BikeShopFacade.login_user(login_data)
            if user_id:
                session['user_id'] = str(user_id)
                flash('Вхід виконано успішно!')
                return redirect(url_for('index'))
            else:
                flash('Невірний email або пароль')
        except ValueError:
            flash('Невірні дані для входу')

    return render_template('login.html')


@app.route('/orders')
def view_orders():
    if 'user_id' not in session:
        flash('Спочатку увійдіть в систему')
        return redirect(url_for('login'))

    orders = BikeShopFacade.get_user_orders(session['user_id'])
    return render_template('orders.html', orders=orders)


if __name__ == '__main__':
    app.run(debug=True)
