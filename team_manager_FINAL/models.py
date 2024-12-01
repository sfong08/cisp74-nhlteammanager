from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)  # New field for first name
    last_name = db.Column(db.String(100), nullable=False)   # New field for last name
    players = db.relationship('PlayerModel', backref='owner', lazy=True)

class PlayerModel(db.Model):
    __tablename__ = "players"
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # makes foreign key to User model in players table
    id = db.Column(db.Integer, primary_key=True)
    picture = db.Column(db.String())  
    number = db.Column(db.String(2)) 
    first_name = db.Column(db.String())  
    last_name = db.Column(db.String())  
    birthplace = db.Column(db.String())  
    birthdate = db.Column(db.String())  
    position = db.Column(db.String())  
    height = db.Column(db.String())
    weight = db.Column(db.String())
    hand = db.Column(db.String())
    
class ScheduleModel(db.Model):
    __tablename__ = "schedule"
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User model
    id = db.Column(db.Integer, primary_key=True)
    team = db.Column(db.String())
    home_or_away = db.Column(db.String())
    date = db.Column(db.Date)  # Date of the event (no time part)
    time = db.Column(db.String())  # Time of the event (no date part)
    timezone = db.Column(db.String())
    location = db.Column(db.String())  # Location of the event
    venue = db.Column(db.String())  # Venue of the event

    def __repr__(self):
        return f"{self.first_name}:{self.last_name}"    # return a string of the PlayerModel instance by displaying first and last name