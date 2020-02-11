from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class ToDoForm(FlaskForm):
    add_input = StringField('To Do', validators=[DataRequired()])
    add_submit = SubmitField('Add Item')
    mark_submit = SubmitField("Mark As Complete")
