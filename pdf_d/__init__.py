
from flask import Flask

from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdfdrive.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
db = SQLAlchemy(app)

from pdf_d import routes  # noqa E402 F401 F403


# to run the app from the terminal with gunicorn
# gunicorn --bind
