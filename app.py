from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, BooleanField
from wtforms.validators import InputRequired, Length, Email
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(50))
    plants = db.relationship('Plant', backref='user', lazy='dynamic')

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    plant_date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    entries = db.relationship('Entry', backref='plant', lazy='dynamic')

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    ventilation = db.Column(db.Integer)
    fertilized = db.Column(db.Boolean)
    watered = db.Column(db.Boolean)
    pruned = db.Column(db.Boolean)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'))

class RegisterForm(FlaskForm):
    username = StringField('Benutzername', validators=[InputRequired(), Length(min=4, max=50)])
    email = StringField('E-Mail', validators=[InputRequired(), Email(), Length(max=100)])
    password = PasswordField('Passwort', validators=[InputRequired(), Length(min=6, max=50)])
    submit = SubmitField('Registrieren')

class LoginForm(FlaskForm):
    username = StringField('Benutzername', validators=[InputRequired(), Length(min=4, max=50)])
    password = PasswordField('Passwort', validators=[InputRequired(), Length(min=6, max=50)])
    submit = SubmitField('Login')

class PlantForm(FlaskForm):
    name = StringField('Pflanzenname', validators=[InputRequired(), Length(max=100)])
    plant_date = StringField('Pflanzdatum (TT.MM.JJJJ)', validators=[InputRequired()])
    submit = SubmitField('Pflanze hinzufügen')
    def validate_plant_date(self, plant_date):
        try:
            datetime.strptime(plant_date.data, '%d.%m.%Y')
        except ValueError:
            raise ValidationError('Ungültiges Datumsformat. Bitte verwenden Sie das Format TT.MM.JJJJ.')

class EntryForm(FlaskForm):
    date = DateField('Datum', validators=[InputRequired()], format='%Y-%m-%d')
    temperature = StringField('Temperatur (C)', validators=[InputRequired()])
    humidity = StringField('Luftfeuchtigkeit (%)', validators=[InputRequired()])
    ventilation = StringField('Lüftung (0-100)', validators=[InputRequired()])
    fertilized = BooleanField('Düngung')
    watered = BooleanField('Bewässerung')
    pruned = BooleanField('Schnitt')
    submit = SubmitField('Eintrag hinzufügen')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('index'))
        flash('Ungültiger Benutzername oder Passwort')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Registrierung erfolgreich. Bitte loggen Sie sich ein.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = PlantForm()
    if form.validate_on_submit():
        plant_date = datetime.strptime(form.plant_date.data, '%d.%m.%Y')
        new_plant = Plant(name=form.name.data, plant_date=plant_date, user_id=current_user.id)
        db.session.add(new_plant)
        db.session.commit()
        return redirect(url_for('index'))
    plants = Plant.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', form=form, plants=plants)

@app.route('/entries/<int:plant_id>', methods=['GET', 'POST'])
@login_required
def entries(plant_id):
    form = EntryForm()
    if form.validate_on_submit():
        new_entry = Entry(
            date=form.date.data,
            temperature=form.temperature.data,
            humidity=form.humidity.data,
            ventilation=form.ventilation.data,
            fertilized=form.fertilized.data,
            watered=form.watered.data,
            pruned=form.pruned.data,
            plant_id=plant_id
        )
        db.session.add(new_entry)
        db.session.commit()
        flash('Eintrag erfolgreich hinzugefügt.')
        return redirect(url_for('entries', plant_id=plant_id))
    
    plant = Plant.query.get(plant_id)
    entries = Entry.query.filter_by(plant_id=plant_id).all()
    
    return render_template('entries.html', form=form, plant=plant, entries=entries)
    
if __name__ == '__main__':
    app.run(debug=True)

