from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from . import db


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    category_id = db.Column(db.Integer, nullable=False, unique=True)
    category_name = db.Column(db.String(80), nullable=False, index=True)
    category_image_link = db.Column(db.String(150), nullable=False)
    category_link = db.Column(db.String(150), nullable=True)
    category_type = db.Column(db.String(10), nullable=True)
    category_text = db.Column(db.String(150), nullable=True)
    category_parent_id = db.Column(db.String(80), nullable=True)
    # make coulumn for category_group based on the main category
    category_group = db.Column(db.String(80), nullable=True)

    def __repr__(self):
        return f"Category('{self.category_id}', '{self.category_name}', '{self.category_image_link}', '{self.category_link}', '{self.category_type}', '{self.category_text}', '{self.category_parent_id}', '{self.category_group}')"


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    year = db.Column(db.String(4), nullable=True)
    book_id = db.Column(db.String(20), nullable=False)
    book_title = db.Column(db.String(350), nullable=False)
    book_author = db.Column(db.String(150), nullable=True, default="None")
    # make the category id a forign key
    category = db.Column(db.Integer, db.ForeignKey(
        "category.category_id"), nullable=False, index=True)
    category_name = db.relationship(
        "Category", backref=db.backref("books", lazy=True))
    book_download_link = db.Column(db.String(250), nullable=True)
    book_size = db.Column(db.String(15), nullable=True)
    book_img_link = db.Column(db.String(250), nullable=True)
    book_pages = db.Column(db.String(20), nullable=True)
    book_description = db.Column(db.String(500), nullable=True)
    scrap_cat = db.Column(db.String(150), nullable=True)

    def __repr__(self):
        return f"Book('{self.book_id}', '{self.book_title}', '{self.book_author}', '{self.category_name}', '{self.book_download_link}', '{self.book_size}', '{self.book_img_link}', '{self.book_pages}', '{self.book_description}', '{self.scrap_cat}', '{self.category}')"


class Cat_Links(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    cat_id = db.Column(db.Integer, nullable=False)
    cat_name = db.Column(db.String(80), nullable=False, unique=True)
    cat_link_start_link = db.Column(db.String(150), nullable=True)
    cat_max_page = db.Column(db.Integer, nullable=False)
    got_it = db.Column(db.Integer, nullable=True, default=False)

    def __repr__(self):
        return f"Cat_Links('{self.cat_id}', '{self.cat_name}', '{self.cat_link_start_link}', '{self.cat_max_page}', '{self.got_it}')"

