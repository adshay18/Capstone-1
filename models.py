from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()
def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)

class Like(db.Model):
    """Images liked by user"""
    
    __tablename__ = 'likes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False)
    
    image_id = db.Column(db.Integer, db.ForeignKey('images.id', ondelete='CASCADE'),
        nullable=False)
    
    image = db.relationship('Image', backref='likes')
    
    def __repr__(self):
        return f'<Like #{self.id}, User {self.user.username}, Image #{self.image.id}>'

class Image(db.Model):
    """Image sourced from pexel API"""
    
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    
    pexel_id = db.Column(db.Integer, nullable=False)
    
    url = db.Column(db.Text, nullable=False)
    
    avg_color = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Image #{self.id}, Pexel ID {self.pexel_id}>'

class Board(db.Model):
    """Board comprised of images a user wants to include""" 
    
    __tablename__ = 'boards'
    
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.Text, nullable=False)
    
    description = db.Column(db.Text, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False)
    images = db.relationship('Image', secondary='board_images')
    user = db.relationship('User', backref='boards')
    
class Board_Image(db.Model):
    '''Images on a board'''
    
    __tablename__ = 'board_images'
    
    id = db.Column(db.Integer, primary_key=True)
    
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id', ondelete='CASCADE'),
        nullable=False)
    
    image_id = db.Column(db.Integer, db.ForeignKey('images.id', ondelete='CASCADE'),
        nullable=False)
    board = db.relationship('Board', backref='board_images')
    images = db.relationship('Image', backref='board_images')
    
    def __repr__(self):
        return f'<Board #{self.board_id} Image #{self.image_id}>'
    
class Fav_Board(db.Model):
    """Boards that a user likes"""
    
    __tablename__ = 'fav_boards'
    
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False)
    
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id', ondelete='CASCADE'),
        nullable=False)
    
    board = db.relationship('Board', backref='fav_boards')
    
    def __repr__(self):
        return f'<Fav_Board #{self.id}, user_id {self.user_id}, board_id {self.board_id}>'
    
class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    likes = db.relationship(
        'Image', secondary='likes'
    )
    
    fav_boards = db.relationship('Board', secondary='fav_boards')

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"


    @classmethod
    def signup(cls, username, email, password):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`."""

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False