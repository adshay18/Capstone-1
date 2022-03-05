from crypt import methods
from curses.ascii import SI
from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
import requests

from models import db, connect_db, User, Like, Image, Board, Fav_Board, Board_Image
from forms import SignupForm, LoginForm, UserEditForm
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

def store_search():
    """If a user makes a search, add it to session"""
    session['SEARCH_TERM'] = request.args.get('q')
    
def delete_search():
    session['SEARCH_TERM'] = None

def login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def logout():
    """Logout user."""
    delete_search()
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


####################### Make homepage filled with images from pexel api ########################
@app.route('/')
def home_page():
    '''Shows homepage for app'''
    
    if g.user:
        delete_search()
        response = requests.get(f'{base_url}/search?query=random', headers=my_headers)
        images = response.json()['photos']
        for image in images:
            try:
                pexel_id = image['id']
                url = image['src']['original']
                avg_color = image['avg_color']
                
                img = Image(pexel_id=pexel_id, url=url, avg_color=avg_color)
                
                db.session.add(img)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
        
        user_likes = Like.query.filter(Like.user_id==g.user.id).all()
        likes = [like.pexel_id for like in user_likes]
        user = g.user
        
        return render_template('home.html', images=images, user=user, likes=likes)
    else:
        return render_template('home-visitor.html')



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
                email=form.email.data,
                image_url=form.image_url.data
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
        store_search()
        response = requests.get(f'{base_url}/search?query={search}', headers=my_headers)
        images = response.json()['photos']
        for image in images:
            try:
                pexel_id = image['id']
                url = image['src']['original']
                avg_color = image['avg_color']
                
                img = Image(pexel_id=pexel_id, url=url, avg_color=avg_color)
                
                db.session.add(img)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                
            user_likes = Like.query.filter(Like.user_id==g.user.id).all()
            likes = [like.pexel_id for like in user_likes]
            user = g.user
    return render_template('results.html', images=images, likes=likes, user=user)

@app.route('/browse')
def show_browse_page():
    '''Page with different search bars'''
    return render_template('browse.html')

####################### User routes ######################################

@app.route('/users')
def list_users():
    '''Listing all users'''
    
    search = request.args.get('u')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)
    
@app.route('/users/<int:user_id>')
def show_user(user_id):
    '''Show user profile'''
    delete_search()
    user = User.query.get_or_404(user_id)

    # snag images from db
    images = user.likes
    
    return render_template('users/profile.html', images=images, user=user)
        
@app.route('/users/<int:user_id>/boards')
def show_user_boards(user_id):
    '''Show boards user has created'''
    

@app.route('/users/<int:user_id>/fav_boards')
def show_favorites(user_id):
    '''Show boards this user has favorited'''
    
@app.route('/users/edit', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    elif g.user:
        form = UserEditForm(obj=g.user)
        
        if form.validate_on_submit():
            user = User.authenticate(g.user.username,
                                    form.password.data)

            if user:
                user.username = form.username.data
                user.email = form.email.data
                user.image_url = form.image_url.data
                user.banner_url = form.banner_url.data
                user.bio = form.bio.data
                user.location = form.location.data
                db.session.add(user)
                db.session.commit()
                
                flash(f"Profile updated!", "success")
                return redirect(f"/users/{g.user.id}")

            flash("Incorrect password.", 'danger')
        return render_template('users/edit.html', form=form, user=g.user)
    
@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")

#################### Board routes   ####################################
@app.route('/boards')
def show_boards():
    '''List all boards'''
    
    search = request.args.get('b')

    if not search:
        boards = Board.query.all()
    else:
        boards = Board.query.filter(Board.name.like(f"%{search}%")).all()

    return render_template('boards/index.html', boards=boards)

@app.route('/boards/<int:board_id>')
def show_board(board_id):
    '''Show board page'''
    

    
################# Adding/removing likes/boards/fav_boards ############################   
 
@app.route('/users/like/<int:img_id>', methods=["POST"])
def add_like(img_id):
    '''Add image to user's likes'''
    if not g.user:
        flash('Access denied.', 'danger')
        return redirect('/login')
    img = Image.query.filter(Image.pexel_id==img_id).first()
    user = g.user
    like = Like(user_id=user.id, pexel_id=img_id)
    db.session.add(like)
    db.session.commit()
    
    if not session['SEARCH_TERM']:
        return redirect('/')
    elif session['SEARCH_TERM']:
        return redirect(f"/search?q={session['SEARCH_TERM']}")
@app.route('/users/unlike/<int:img_id>', methods=["POST"])
def remove_like(img_id):
    '''Remove image from user's likes'''
    if not g.user:
        flash('Access denied.', 'danger')
        return redirect('/login')

    user = g.user
    like = Like.query.filter(Like.pexel_id==img_id, Like.user_id==user.id).first()
    db.session.delete(like)
    db.session.commit()
    if not session['SEARCH_TERM']:
        return redirect('/')
    elif session['SEARCH_TERM']:
        return redirect(f"/search?q={session['SEARCH_TERM']}")
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