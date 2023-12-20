from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///entries.db'
app.config['SECRET_KEY'] = 'gr23t782z3i76frguqzrWBJ'  # Change this to a secure random key
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50), nullable=False)
    radius = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))
@app.route('/')
@login_required
def index():
    entries = Entry.query.all()
    return render_template('index.html', api_key='9109a453f44b427cb7c7a77b72c1002b', entries=entries)

@app.route('/get_coordinates', methods=['POST'])
def get_coordinates():
    city = request.form.get('city')
    radius = request.form.get('radius')

    if not city or not radius:
        return "City and radius are required."

    # Get coordinates of the entered city using OpenCage Geocoding API
    geocoding_url = f'https://api.opencagedata.com/geocode/v1/json?q={city}&key=9109a453f44b427cb7c7a77b72c1002b'
    response = requests.get(geocoding_url)
    data = response.json()
    print(response.text)
    if not data.get('results'):
        return "Invalid city name."

    coordinates = data['results'][0]['geometry']

    # Save the entry to the database
    entry = Entry(city=city, radius=float(radius), latitude=coordinates['lat'], longitude=coordinates['lng'])
    db.session.add(entry)
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/edit_entry/<int:entry_id>', methods=['GET'])
def edit_entry(entry_id):
    entry = Entry.query.get_or_404(entry_id)
    return render_template('edit_entry.html', entry=entry)


@app.route('/save_edit_entry/<int:entry_id>', methods=['POST'])
def save_edit_entry(entry_id):
    entry = Entry.query.get_or_404(entry_id)

    # Update entry based on form submission
    entry.city = request.form.get('city')
    entry.radius = float(request.form.get('radius'))

    # Save changes to the database
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    entry = Entry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Check if the default user exists
        default_user = User.query.filter_by(username='admin').first()
        if not default_user:
            # Create a default user if it doesn't exist
            default_user = User(username='admin', password_hash=generate_password_hash('q1JH7BupL5Y:'))
            db.session.add(default_user)
            db.session.commit()
    app.run(port=3256)
