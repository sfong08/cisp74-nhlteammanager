from flask import Flask, render_template, request, redirect, abort, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, PlayerModel, ScheduleModel, User
from werkzeug.utils import secure_filename
from pathlib import Path
import os
from datetime import datetime

app = Flask(__name__)

# configure the Flask app
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///teammanager.db'
# database for website deployment
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://u832pi28664c9p:p83d95b3ac128f2a367d74077b26f1351b1a56b31079dd86530ec46c9533c30fe@c5p86clmevrg5s.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d5vibg8gqvdjq6'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SECRET_KEY'] = 'your-secret-key'
db.init_app(app)

# initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # redirect to login page if the user is not authenticated

# load user by ID for login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_table():
    db.create_all()

# User home (redirect to login or register page)
@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')  # Render the home page with buttons to /login or /register


# user sign up
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']

        # Check if the user already exists
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or Email already exists!', 'danger')
            return redirect('/register')

        # Create new user
        user = User(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
        db.session.add(user)
        db.session.commit()

        login_user(user)  # Log the user in immediately after registration
        return redirect('/roster')

    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:  # In real apps, use hashed passwords
            login_user(user)
            return redirect('/accounthome')

        flash('Invalid login credentials', 'danger')

    return render_template('login.html')

# function to handle date parsing
def parse_birthdate(birthdate_str):
    try:
        return datetime.strptime(birthdate_str, "%m/%d/%Y").date()
    except ValueError:
        try:
            return datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        except ValueError:
            return None

# Creating/adding players
@app.route('/create', methods=['GET', 'POST'])
@login_required  # Ensure user is logged in before they can create a player
def create():
    if request.method == 'POST':
        picture_file = request.files.get('picture')
        picture_path = None

        if picture_file:
            filename = secure_filename(picture_file.filename)
            filename = str(Path(filename).as_posix())  # Normalize filename to use forward slashes
            picture_path = filename
            picture_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Retrieve form data
        number = request.form['number']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birthdate_str = request.form['birthdate']
        
        birthdate = parse_birthdate(birthdate_str)
        if not birthdate:
            return "Invalid birthdate format. Please use MM/DD/YYYY.", 400

        hand = request.form['hand']
        birthplace = request.form['birthplace']
        position = request.form['position']
        height = request.form['height']
        weight = request.form['weight']

        # Create new player and associate it with the logged-in user
        player = PlayerModel(
            picture=picture_path,
            number=number,
            first_name=first_name,
            last_name=last_name,
            birthdate=birthdate,
            birthplace=birthplace,
            position=position,
            height=height,
            weight=weight,
            hand=hand,
            user_id=current_user.id  # Associate player with the current user
        )

        db.session.add(player)
        db.session.commit()

        return redirect('/roster')

    return render_template('create.html')

# create a page for the home page of an account
@app.route('/accounthome')
def accounthome():
    return render_template('accounthome.html')

@app.route('/roster')
@login_required  # Ensure user is logged in to view their roster
def roster():
    players = PlayerModel.query.filter_by(user_id=current_user.id).all()  # Only fetch the current user's players

    # Ensure the birthdate is a datetime object, if it's not already
    for player in players:
        if isinstance(player.birthdate, str):
            player.birthdate = datetime.strptime(player.birthdate, "%Y-%m-%d").date()

    return render_template('roster.html', players=players)

# Editing players
@app.route('/<int:id>', methods=['GET'])
@login_required  # Ensure user is logged in before viewing player details
def retrieve_player(id):
    player = PlayerModel.query.filter_by(id=id, user_id=current_user.id).first()  # Ensure player belongs to the logged-in user
    if player:
        return render_template('data.html', player=player)
    return f"Player with ID={id} doesn't exist or you don't have permission.", 403

@app.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required  # Ensure user is logged in before editing player
def update(id):
    player = PlayerModel.query.filter_by(id=id, user_id=current_user.id).first()
    if not player:
        return f"Player with ID={id} doesn't exist or you don't have permission.", 403

    if request.method == 'POST':
        picture_file = request.files.get('picture')
        picture_path = player.picture

        if picture_file:
            filename = secure_filename(picture_file.filename)
            filename = str(Path(filename).as_posix())  # Normalize filename
            picture_path = filename
            picture_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        number = request.form['number']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birthdate_str = request.form['birthdate']
        birthdate = parse_birthdate(birthdate_str)
        if not birthdate:
            return "Invalid birthdate format. Please use MM/DD/YYYY.", 400

        hand = request.form['hand']
        birthplace = request.form['birthplace']
        position = request.form['position']
        height = request.form['height']
        weight = request.form['weight']

        player.picture = picture_path
        player.number = number
        player.first_name = first_name
        player.last_name = last_name
        player.birthdate = birthdate
        player.hand = hand
        player.birthplace = birthplace
        player.position = position
        player.height = height
        player.weight = weight

        db.session.commit()

        return redirect('/roster')

    if isinstance(player.birthdate, str):
        player.birthdate = datetime.strptime(player.birthdate, "%Y-%m-%d").date()

    formatted_birthdate = player.birthdate.strftime('%Y-%m-%d') if player.birthdate else None
    return render_template('update.html', player=player, formatted_birthdate=formatted_birthdate)

# deleting a player
@app.route('/<int:id>/delete', methods=['GET', 'POST'])
@login_required  # Ensure user is logged in before deleting player
def delete(id):
    player = PlayerModel.query.filter_by(id=id, user_id=current_user.id).first()
    if not player:
        return f"Player with ID={id} doesn't exist or you don't have permission.", 403

    if request.method == 'POST':
        db.session.delete(player)
        db.session.commit()
        return redirect('/roster')

    return render_template('delete.html')

# function to handle date parsing 
def parse_gamedate(gamedate_str):
    try:
        return datetime.strptime(gamedate_str, "%m/%d/%Y").date()
    except ValueError:
        try:
            return datetime.strptime(gamedate_str, "%Y-%m-%d").date()
        except ValueError:
            return None

# Creating/adding a game to the schedule
@app.route('/addgame', methods=['GET', 'POST'])
@login_required  # Ensure user is logged in before they can create a game
def addgame():
    if request.method == 'POST':
        # Retrieve form data for the game schedule
        team = request.form['team']
        home_or_away = request.form['home_or_away']
        time_str = request.form['time']  # Keep time as string
        timezone = request.form['timezone']
        location = request.form['location']
        venue = request.form['venue']
        gamedate_str = request.form['date']

        # Parse the game date
        gamedate = parse_gamedate(gamedate_str)
        if not gamedate:
            return "Invalid date format. Please use MM/DD/YYYY.", 400

        # Create new game entry and associate it with the logged-in user
        game = ScheduleModel(
            team=team,
            home_or_away=home_or_away,
            date=gamedate,  # Use parsed date
            time=time_str,  # Store time as text
            timezone=timezone,
            location=location,
            venue=venue,
            user_id=current_user.id  # Associate game with the current user
        )

        db.session.add(game)
        db.session.commit()

        return redirect('/schedule')  # Redirect to the schedule page

    return render_template('addgame.html')

@app.route('/<int:id>/editgame', methods=['GET', 'POST'])
@login_required  # Ensure user is logged in before editing the schedule
def editgame(id):
    # Fetch the schedule entry by id and ensure the current user owns it
    game = ScheduleModel.query.filter_by(id=id, user_id=current_user.id).first()
    if not game:
        return f"Game with ID={id} doesn't exist or you don't have permission.", 403

    if request.method == 'POST':
        # Retrieve form data for game update
        team = request.form['team']
        home_or_away = request.form['home_or_away']
        time_str = request.form['time']  # Keep time as text
        timezone = request.form['timezone']
        location = request.form['location']
        venue = request.form['venue']
        gamedate_str = request.form['date']

        # Parse the game date
        gamedate = parse_gamedate(gamedate_str)
        if not gamedate:
            return "Invalid date format. Please use MM/DD/YYYY.", 400

        # Update the schedule entry with the new values
        game.team = team
        game.home_or_away = home_or_away
        game.time = time_str
        game.timezone = timezone
        game.location = location
        game.venue = venue
        game.date = gamedate  # Use parsed date

        db.session.commit()

        return redirect('/schedule')  # Redirect to the schedule page

    # Ensure the date is formatted for the form
    if isinstance(game.date, str):
        game.date = datetime.strptime(game.date, "%Y-%m-%d").date()

    formatted_date = game.date.strftime('%m/%d/%Y') if game.date else None
    return render_template('editgame.html', game=game, formatted_date=formatted_date)

# Schedule page for the user
@app.route('/schedule')
@login_required  # Ensure user is logged in to view their schedule
def schedule():
    games = ScheduleModel.query.filter_by(user_id=current_user.id).all()  # Only fetch the current user's games

    # Ensure the date and time are in the correct format for display
    for game in games:
        if isinstance(game.date, str):
            game.date = datetime.strptime(game.date, "%Y-%m-%d").date()

    return render_template('schedule.html', games=games)

# deleting a game
@app.route('/<int:id>/deletegame', methods=['GET', 'POST'])
@login_required  # Ensure user is logged in before deleting game schedule
def deletegame(id):
    game = ScheduleModel.query.filter_by(id=id, user_id=current_user.id).first()
    if not game:
        return f"Game with ID={id} doesn't exist or you don't have permission.", 403

    if request.method == 'POST':
        db.session.delete(game)
        db.session.commit()
        return redirect('/schedule')

    return render_template('deletegame.html')

# account details
@app.route('/accountdetails', methods=['GET'])
@login_required
def accountdetails():
    user = current_user  # Assuming the user is logged in and current_user is set
    return render_template('accountdetails.html', user=user)

@app.route('/editaccount', methods=['GET', 'POST'])
@login_required
def editaccount():
    user = current_user

    if request.method == 'POST':
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.username = request.form['username']
        user.email = request.form['email']
        
        if request.form['password']:  # Only update password if provided
            hashed_password = User.hash_password(request.form['password'])  # Assuming you have a method for hashing
            user.password = hashed_password
        
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect('/accountdetails')  # Redirect after POST to prevent form resubmission

    return render_template('editaccount.html', user=user)

# User logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='localhost', port=5000)
