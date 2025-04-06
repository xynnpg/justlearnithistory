from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField, SelectField, HiddenField, PasswordField
from wtforms.validators import DataRequired, Length, NumberRange

class LessonForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=200)])
    content = HiddenField('Content', validators=[DataRequired()])
    order = IntegerField('Order', validators=[DataRequired()])
    submit = SubmitField('Save Lesson')

class TestForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=200)])
    order = IntegerField('Order', validators=[DataRequired(), NumberRange(min=1)])
    questions_json = HiddenField('Questions JSON', validators=[DataRequired()])
    submit = SubmitField('Save Test')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login') 