from curses.ascii import SI
from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from models import db, connect_db, User, Like, Image, Board, Fav_Board, Board_Image
from forms import SignupForm, LoginForm

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

@app.route('/')
def home_page():
    '''Shows homepage for app'''
    return render_template('home.html')



# Sign up, login, and logout routes

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