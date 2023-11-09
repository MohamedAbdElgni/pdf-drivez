from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, SubmitField


class Filters(FlaskForm):
    exact_match = BooleanField('Exact Match', default=False, id='match-filter')
    year_select = SelectField('Year', choices=["Year", 1990, 1995,
                                               2000, 2005, 2010,
                                               2015, 2022],default="Year",id='year-filter',)
    pages_select = SelectField('Pages', choices=[
                               "Pages", 100, 200, 300, 400, 500], default=500, id='pages-filter')
    submit = SubmitField('Filter', id='submit')
    
    
