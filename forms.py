from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length

class LessonForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=200)])
    content = HiddenField('Content', validators=[DataRequired()])
    order = IntegerField('Order', validators=[DataRequired()])
    submit = SubmitField('Save Lesson')

class TestForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=200)])
    questions_json = HiddenField('Questions JSON', validators=[DataRequired()])
    submit = SubmitField('Save Test') 