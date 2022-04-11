from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
# from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
import requests
import os


from models import db, connect_db, User, Like, Image, Board, Fav_Board, Board_Image
from forms import SignupForm, LoginForm, UserEditForm, NewBoardForm, AddImageForm
from secret import base_url, my_headers

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'postgres://qfypfgfblivuxq:01791daa8b0fc57654cd28e081d4cf3055c112f6587c14ec5e5d146479868639@ec2-34-207-12-160.compute-1.amazonaws.com:5432/duhn34i3r8hkf', 'postgresql:///picl')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = 'litup'
# toolbar = DebugToolbarExtension(app)

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
        response = requests.get(f'{base_url}/curated', headers=my_headers)
        images = response.json()['photos']
        images.reverse()
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
        
        user_likes = Like.query.filter(Like.user_id==g.user.id)
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
    if not g.user:
        flash("How did you even do that, you need to be logged in to logout.", "warning")
        return redirect('/')
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
    if not g.user:
        flash("Please login or create an account to access free photos.", "danger")
        return redirect("/")
    search = request.args.get('q')
    page = request.args.get('p', 1)
    prev_page = None
    next_page = None
    
    if not search:
        return render_template('browse.html')
    else:
        store_search()
        response = requests.get(f'{base_url}/search?query={search}&per_page=54&page={page}', headers=my_headers)
        images = response.json()['photos']
        
        try:
            if response.json()['next_page']:
                next_page = int(page) + 1
        except KeyError:
            next_page = None
        
        try:    
            if response.json()['prev_page']:
                prev_page = int(page) - 1
        except KeyError:
            prev_page = None
                                        
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
    
        
    return render_template('results.html', images=images, likes=likes, user=user, search=search, page=page, next_page=next_page, prev_page=prev_page)

@app.route('/browse')
def show_browse_page():
    '''Page with different search bars'''
    if not g.user:
        flash("Login to search images, users and boards.", "warning")
        return redirect('/browse')
    return render_template('browse.html')

####################### User routes ######################################

@app.route('/users')
def list_users():
    '''Listing all users'''
    if not g.user:
        flash('Please login.', 'warning')
    
    search = request.args.get('u')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users, search=search)
    
@app.route('/users/<int:user_id>')
def show_user(user_id):
    '''Show user profile'''
    delete_search()
    if not g.user:
        flash('Please login or signup to view content.', 'danger')
        return redirect('/')
    
    user = User.query.get_or_404(user_id)

    user_likes = Like.query.filter(Like.user_id==g.user.id).order_by(Like.id.desc()).all()
    likes = [like.pexel_id for like in user_likes]
    # snag images from db
    images = [like.image for like in user_likes]
   
    form = AddImageForm()
    form.board_id.choices = [(board.id, board.name) for board in user.boards]
    
    return render_template('users/profile.html', images=images, user=user, likes=likes, form=form)  
    
    
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

    Fav_Board.query.filter(Fav_Board.user_id==g.user.id).delete()
    Board.query.filter(Board.user_id==g.user.id).delete()
    logout()
    delete_search()
    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")

#################### Board routes   ####################################
@app.route('/boards')
def show_boards():
    '''List all boards'''
    if not g.user:
        flash('Please login or signup to view content.', 'danger')
        return redirect('/')
    
    search = request.args.get('b')

    if not search:
        boards = Board.query.all()
    else:
        boards = Board.query.filter(Board.name.like(f"%{search}%")).all()

    return render_template('boards/index.html', boards=boards, search=search)

@app.route('/users/<int:user_id>/boards')
def show_boards_for_user(user_id):
    '''Show all boards for a given user'''
    delete_search()
    if not g.user:
        flash('Access denied.', 'danger')
        return redirect('/login')
        
    boards = Board.query.filter(Board.user_id==user_id)
    user = User.query.get_or_404(user_id)
    
    return render_template('boards/list.html', user=user, boards=boards)
    
    
@app.route('/users/<int:user_id>/boards/<int:board_id>')
def show_board(user_id, board_id):
    '''Show details for a specific board'''
    if not g.user:
        flash('Please login or signup to view content.', 'danger')
        return redirect('/')
    delete_search()
    user = User.query.get_or_404(user_id)
    board = Board.query.get_or_404(board_id)
    board_images = Board_Image.query.filter(Board_Image.board_id==board_id).all()
    images = [board_image.images for board_image in board_images]
    user_likes = Like.query.filter(Like.user_id==g.user.id).all()
    likes = [like.pexel_id for like in user_likes]
    
    return render_template('boards/details.html', user=user, board=board, images=images, likes=likes)


@app.route('/users/<int:user_id>/fav_boards')
def show_user_favorites(user_id):
    '''Show all of a user's favorite boards'''
    delete_search()
    if not g.user:
        flash('Access denied.', 'danger')
        return redirect('/login')
    
    user = User.query.get_or_404(user_id)
    boards = user.fav_boards
    
    return render_template('boards/list-favorites.html', user=user, boards=boards)
    
################# Adding/removing likes/boards/fav_boards ############################   
 
@app.route('/users/like/<int:img_id>', methods=["POST"])
def add_like(img_id):
    '''Add image to user's likes'''
    if not g.user:
        flash('Access denied.', 'danger')
        return redirect('/login')
    user = g.user
    like = Like(user_id=user.id, pexel_id=img_id)
    db.session.add(like)
    db.session.commit()
    
    return jsonify({
        'user' : g.user.username,
        'like' : 'created',
        'liked_pexel_ids' : [like.pexel_id for like in g.user.likes]
    })
    
    
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
    
    return jsonify({
        'user' : g.user.username,
        'like' : 'deleted',
        'liked_pexel_ids' : [like.pexel_id for like in g.user.likes]
    })
    
    
@app.route('/users/add_board', methods=["GET", "POST"])
def create_board():
    '''Create new board for current user'''
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    elif g.user:
        form = NewBoardForm()

        if form.validate_on_submit():
            
            name = form.name.data
            description = form.description.data
            user_id = g.user.id
            
            board = Board(name=name, description=description, user_id=user_id)

            db.session.add(board)
            db.session.commit()
            
            flash(f"Board created!", "success")
            return redirect(f"/users/{g.user.id}/boards")

            
        return render_template('boards/create.html', form=form, user=g.user)
    
    
@app.route('/users/<int:user_id>/delete_board/<int:board_id>', methods=["POST"])
def delete_board(board_id, user_id):
    '''Delete board for current user'''
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    board = Board.query.get_or_404(board_id)
    board_images = Board_Image.query.filter(Board_Image.board_id==board_id).delete()
    
    db.session.delete(board)
    db.session.commit()
    
    return redirect(f'/users/{user_id}/boards')
    
    
@app.route('/users/<int:user_id>/boards/add/<int:img_id>', methods=["POST"])
def add_image_to_board(user_id, img_id):
    '''Handle adding an image to a board'''
    if not g.user:
        flash('Access unauthorized.', 'danger')
        return redirect('/')
    form = AddImageForm()
    user = g.user
    form.board_id.choices = [(board.id, board.name) for board in user.boards]
    if form.validate_on_submit():
        
        board_id = form.board_id.data
        image_id = img_id
        
        board_image = Board_Image(board_id=board_id, image_id=image_id)
        db.session.add(board_image)
        db.session.commit()
        
        flash(f'Added to board!', 'success')
        return redirect(f'/users/{user.id}')
    
    flash('Something went wrong.', 'primary')
    return redirect(f'/users/{user.id}')

@app.route('/users/<int:user_id>/boards/<int:board_id>/remove/<int:img_id>', methods=["POST"])
def remove_image_from_board(user_id, board_id, img_id):
    '''Handle removing an image from a board'''
    if not g.user:
        flash('Access unauthorized.', 'danger')
        return redirect('/')
    board_image = Board_Image.query.filter(Board_Image.board_id==board_id, Board_Image.image_id==img_id).first()
    db.session.delete(board_image)
    db.session.commit()
    
    return redirect(f'/users/{user_id}/boards/{board_id}')
    
@app.route('/users/<int:user_id>/favorite/<int:board_id>', methods=["POST"])
def add_fav_board(user_id, board_id):
    '''Add board to list of current user's favorite boards'''
    if not g.user:
        flash('Access unauthorized.', 'danger')
        return redirect('/')
    
    board_owner = user_id
    board = board_id
    fav = Fav_Board(user_id=g.user.id, board_id=board)
    db.session.add(fav)
    db.session.commit()
    
    return redirect(f'/users/{board_owner}/boards/{board}')
    
@app.route('/users/<int:user_id>/unfavorite/<int:board_id>', methods=["POST"])
def remove_fav_board(user_id, board_id):
    '''Remove board from list of current user's favorite boards'''
    if not g.user:
        flash('Access unauthorized.', 'danger')
        return redirect('/')
    
    board_owner = user_id
    board = board_id
    
    fav = Fav_Board.query.filter(Fav_Board.board_id==board, Fav_Board.user_id==g.user.id).first()
    
    db.session.delete(fav)
    db.session.commit()
    
    return redirect(f'/users/{board_owner}/boards/{board}')