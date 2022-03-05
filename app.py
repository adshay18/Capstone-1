from crypt import methods
from curses.ascii import SI
from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
import requests

from models import db, connect_db, User, Like, Image, Board, Fav_Board, Board_Image
from forms import SignupForm, LoginForm
from secret import base_url, my_headers

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///picl'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = 'litup'
toolbar = DebugToolbarExtension(app)

connect_db(app)

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


####################### Make homepage filled with images from pexel api ########################
@app.route('/')
def home_page():
    '''Shows homepage for app'''
    response = requests.get(f'{base_url}/search?query=red', headers=my_headers)
    images = response.json()['photos']
    
    return render_template('home.html', images=images)



################### Sign up, login, and logout routes ############################

@app.route('/signup', methods=["GET", "POST"])
def signup():
    '''Create a new user and add to db, redirect back to homepage'''
    
    form = SignupForm()
    
    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data
                )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('signup.html', form=form)

        login(user)

        return redirect("/")

    else:
        return render_template('signup.html', form=form)
    
@app.route('/logout')
def logout_user():
    """Handle logout of user."""

    logout()
    flash("Logged out. Please login again to continue.", 'success')

    return redirect('/login')

@app.route('/login', methods=["GET", "POST"])
def login_user():
    '''Handle login of user.'''
    
    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials, please try again.", 'danger')

    return render_template('login.html', form=form)


####################### Search Routes ################################

@app.route('/search')
def find_images():
    """Page with matching images to search results"""
    
    search = request.args.get('q')
    if not search:
        return render_template('browse.html')
    else:
        response = requests.get(f'{base_url}/search?query={search}', headers=my_headers)
        images = response.json()['photos']
    return render_template('results.html', images=images)


####################### User routes ######################################

@app.route('/users')
def list_users():
    '''Listing all users'''
    
    
@app.route('/users/<int:user_id>')
def show_user(user_id):
    '''Show user profile'''
    
    
@app.route('/users/<int:user_id>/likes')
def show_likes(user_id):
    '''Show list of images the user likes'''
    
    
@app.route('/users/<int:user_id>/boards')
def show_user_boards(user_id):
    '''Show boards user has created'''
    

@app.route('/users/<int:user_id>/fav_boards')
def show_favorites(user_id):
    '''Show boards this user has favorited'''
    

#################### Board routes   ####################################
@app.route('/boards')
def show_boards():
    '''List all boards'''


@app.route('/boards/<int:board_id>')
def show_board(board_id):
    '''Show board page'''
    

    
################# Adding/removing likes/boards/fav_boards ############################   
 
@app.route('/users/like/<int:img_id>', methods=["POST"])
def add_like(img_id):
    '''Add image to user's likes'''
    

@app.route('/users/unlike/<int:img_id>', methods=["POST"])
def remove_like(img_id):
    '''Remove image from user's likes'''
    
@app.route('/users/add_board', methods=["POST"])
def create_board():
    '''Create new board for current user'''
    
    
@app.route('/users/delete_board/<int:board_id>', methods=["POST"])
def delete_board():
    '''Delete board for current user'''
    
@app.route('/boards/<int:board_id>/add/<int:img_id>', methods=["POST"])
def add_image_to_board(board_id, img_id):
    '''Handle adding an image to a board'''
    

@app.route('/boards/<int:board_id>/remove/<int:img_id>', methods=["POST"])
def remove_image_from_board(board_id, img_id):
    '''Handle removing an image from a board'''
    
    
@app.route('/users/favorite/<int:board_id>', methods=["POST"])
def add_fav_board(board_id):
    '''Add board to list of current user's favorite boards'''
    
@app.route('/users/unfavorite/<int:board_id>', methods=["POST"])
def remove_fav_board(board_id):
    '''Remove board from list of current user's favorite boards'''