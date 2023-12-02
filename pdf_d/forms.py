from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, SubmitField


class Filters(FlaskForm):
    exact_match = BooleanField('Exact Match', default=False, id='match-filter')
    year_select = SelectField('Year', choices = ["Year", *[int(x) for x in range(1995, 2023)]])
    pages_select = SelectField('Pages', choices=[
                               "Pages", 100, 200, 300, 400, 500 ,600,700,800,900,1000,1500,1800,2000], default=500, id='pages-filter')
    submit = SubmitField('Filter', id='submit')
    
    
