import random
from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from flask import url_for


def scrap_book_cats(book_l):
    # this function will scrap the book categories and return a list of categories
    # get the book link
    book_link = "https://www.pdfdrive.com"+book_l.book_download_link
    # get the html
    html = requests.get(book_link)
    # parse the html
    soup = BeautifulSoup(html.text, "html.parser")
    # get the categories
    a_tags = soup.find_all('div', class_='ebook-tags')[0].find_all('a')
    # get the categories names
    categories = [a.text for a in a_tags]
    return categories


def split_string(s, char_to_split):
    """
    Split a string into unique substrings using the specified character.

    Args:
        s (str): The input string.
        char_to_split (str): The character to split the string by.

    Returns:
        list: A list of unique substrings obtained from the split operation, or an empty list if input is None.
    """
    if s is not None:
        if char_to_split in s:
            substrings = s.split(char_to_split)
            # Use a set to eliminate duplicate substrings
            unique_substrings = list(set(substrings))
            return unique_substrings
        else:
            return [s]
    else:
        return ["New"]


# Example usage:
# input_string = "sadsadasdasd"
# char_to_split_on = ","
# result = split_string(input_string, char_to_split_on)
# print()

def remove_duplicates(input_list):
    seen = set()
    unique_items = []

    for item in input_list:
        item_set = frozenset(item.items())

        if item_set not in seen:
            unique_items.append(item)
            seen.add(item_set)

    return unique_items


def random_books(model: SQLAlchemy, limit=8, param=None):
    # this function will return a list of random books
    # get the books
    Book = model
    num = limit
    if param:
        books = Book.query.filter_by(category_name=param).all()
    else:
        books = Book.query.all()
    # shuffle the books
    random.shuffle(books)
    # get the first 5 books
    if num == "all":
        return books
    else:
        return books[:num]


def make_json(data=None):
    """
    Converts a list of book objects into a list of dictionaries containing book information.

    Args:
        data (list): A list of book objects.

    Returns:
        list: A list of dictionaries containing book information.
    """
    cat_books = data

    return [
        {
            "book_title": book.book_title,
            "book_img_link": book.book_img_link,
            "book_pages": book.book_pages,
            "year": book.year,
            "book_size": book.book_size,
            "book_description": book.book_description,
            "book_author": book.book_author,
            "book_download_link": book.book_download_link,
            "book_id": book.book_id,
            "category": book.category,
            "scrap_cat": book.scrap_cat,
            "date": book.date,
            "book_link": url_for("book", book=book.book_title.replace(" ", "-") + "-" + book.book_id)

        }
        for book in cat_books
    ]

