from io import StringIO
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length

class SignupForm(FlaskForm):
    '''Form for adding new Users'''
    
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    image_url = StringField('Profile Image URL - optional')
    
class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
    
class UserEditForm(FlaskForm):
    """Form for editing user profile."""
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    image_url = StringField('Profile Image URL - optional')
    banner_url = StringField('Banner Image URL - optional')
    bio = TextAreaField('Bio - optional')
    location = StringField('Location - optional')
    
    password = PasswordField('Password', validators=[Length(min=6)])
    
class NewBoardForm(FlaskForm):
    """Form to create a new board"""
    name = StringField('Board Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    
class AddImageForm(FlaskForm):
    """Add image to board"""
    board_id = SelectField("Add to Board")