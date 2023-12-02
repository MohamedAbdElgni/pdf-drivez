from pdf_d.models import Category, Book
from flask import render_template, url_for, redirect, request, Response, jsonify, send_from_directory,abort
from pdf_d import app
from pdf_d.forms import Filters
from pdf_d.helpers import split_string, remove_duplicates, random_books, make_json
from pdf_d.get_data import vip_search
from sqlalchemy import or_, func
import time
import random
from flask_caching import Cache


# Error handler for 404 Not Found
# Error handler for 404 Not Found

@app.errorhandler(404)
def page_not_found(error):
    sug_books = random_books(Book, 4)
    categories = Category.query.filter_by(category_type="parent").all()
    return render_template("error.html", categories=categories, sug_books=sug_books), 404

# Route for the error page
@app.route("/error")
def error_page():
    sug_books = random_books(Book, 4)
    categories = Category.query.filter_by(category_type="parent").all()
    return render_template("error.html", categories=categories, sug_books=sug_books)


@app.route("/")
@app.route("/home")
def home():
    # get all parent categories and not category name = New
    parent_categories = Category.query.filter_by(
        category_type="parent").filter(Category.category_name != "New").all()

    # Initialize a list to store the results as dictionaries
    result = []
    for category in parent_categories:
        # make a category dict to hold the category name and details and books and books
        # adding the category id and category text col is contaning both the category description and the font awesome icon
        # category text will contain the category description and a font awesome icon sperated by a # so the icon will be on the right side and the text on the left
        # to the category dict and each cat dict will have a list of 4 books
        category_dict = {'category_id': category.category_id,
                         'category_name': category.category_name,
                         'category_text': category.category_text.split("#")[0],
                         'category_icon': category.category_text.split("#")[1],
                         'category_link': url_for('category', category_id=category.category_id),
                         'books': []}

        books = Book.query.filter(or_(Book.scrap_cat.like(f'%{category.category_name},%'),
                                      Book.scrap_cat.like(
                                          f'%,{category.category_name},%'),
                                      Book.scrap_cat.like(f'%,{category.category_name}%'))).order_by(func.random()).limit(4)

        for book in books:
            # now we gonna add the book to the category dict all book info will be added to the book dict
            book_dict = {'book_id': book.book_id,
                         'book_title': book.book_title,
                         'book_author': book.book_author,
                         'book_download_link': book.book_download_link,
                         'book_img_link': book.book_img_link,
                         'book_pages': book.book_pages,
                         'book_size': book.book_size,
                         'book_description': book.book_description,
                         'year': book.year,
                         'book_link': url_for('book', book=book.book_title.replace(" ", "-") + "-" + book.book_id)}
            category_dict['books'].append(book_dict)
        result.append(category_dict)
    sug_books = random_books(Book, 4)
    categories = Category.query.filter_by(category_type="parent").all()
    title = "Home"
    return render_template("home.html", categories=categories, title=title, sug_books=sug_books, result=result)


@app.route("/suggest_random_ebook")
def suggest_random_ebook():
    # Generate a random book using your random_books function
    # Assuming random_books returns a list
    random_book = random_books(Book, 1)[0]
    random_book = random_book.book_title.replace(
        " ", "-") + "-" + random_book.book_id
    # Redirect the user to the book page for the random book
    return redirect(url_for('book', book=random_book))


@app.route("/category/<int:category_id>")
def category(category_id):
    # Get the category id from the URL
    selected_category_name = Category.query.filter_by(
        category_id=category_id).first().category_name
    sug_books = random_books(Book, 8)
    categories = Category.query.filter_by(category_type="parent").all()
    parent = Category.query.filter_by(category_id=category_id).first()

    parent_cat_group = parent.category_group
    # Get the subcategories for the category
    related_categories = Category.query.filter_by(
        category_group=parent_cat_group
    ).all()

    # Fetch all books for the category and convert them to a JSON-serializable format
    cat_books = Book.query.filter(or_(
        Book.scrap_cat.like(f'%{parent.category_name},%'),
        Book.scrap_cat.like(f'%,{parent.category_name},%'),
        Book.scrap_cat.like(f'%,{parent.category_name}%'),
        Book.scrap_cat.like(f'{selected_category_name}%'),
    )).order_by(func.random()).all()

    cat_books_json = [
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

    return render_template(
        "category.html",
        title=parent.category_name,
        parent_cat=parent,
        rltd_categories=related_categories,
        categories=categories,
        sug_books=sug_books,
        cat_books_json=cat_books_json,  # Pass the JSON-serializable list to the template
    )


@app.route("/book/<book>")
def book(book):
    # categories for side bar

    categories = Category.query.filter_by(category_type="parent").all()
    book_id = book.split("-")[-1]
    sug_books = random_books(Book, 8)
    selected_book = Book.query.filter_by(book_id=book_id).first()
    book_category = split_string(selected_book.scrap_cat, ",")
    book_category = Category.query.filter(
        Category.category_name.in_(book_category)).all()
    book_category = remove_duplicates(
        [{"category_name": cat.category_name, "category_id": cat.category_id}for cat in book_category])

    similar_books = make_json(random_books(
        Book, 100, selected_book.category_name))

    return render_template("book.html", title=selected_book.book_title, similar_books=similar_books, book_category=book_category, book=selected_book, categories=categories, sug_books=sug_books,)


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = Filters()
    query = request.args.get('q')
    # run vip search
    try:
        vip_search(query)
    except:
        pass
    start_time_in_s = time.time()
    books = Book.query.filter(or_(
        Book.book_title.like(f'{query}%'),
        Book.book_title.like(f'%{query}%'),
        Book.book_title.like(f'%{query}')))

    if form.validate_on_submit():
        # Filter books based on form inputs
        if form.exact_match.data:
            books = books.filter(Book.book_title == query)
        if form.year_select.data != 'Year':
            books = books.filter(
                Book.year == form.year_select.data)
        if form.pages_select.data != '500':
            books = books.filter(
                Book.book_pages <= form.pages_select.data)
            books = books.all()
    # Execute the query and get the filtered books
    books = books
    end_time_in_s = time.time()
    total_time = round(end_time_in_s - start_time_in_s, 4)

    if books:
        books = make_json(books)
    else:
        books = []
    search_results_count = len(books)

    sug_books = random_books(Book, 8)
    categories = Category.query.filter_by(category_type="parent").all()
    return render_template("search.html",
                           categories=categories, sug_books=sug_books, total_time=total_time, search_results_count=search_results_count, sbooks=books, query=query, form=form, title=query)
# static pages


@app.route("/about")
def about():
    sug_books = random_books(Book, 8)
    categories = Category.query.filter_by(category_type="parent").all()
    title = "About"
    return render_template("about.html", title=title, categories=categories, sug_books=sug_books)


@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')


@app.route("/mobile-app")
def mobile_app():
    sug_books = random_books(Book, 8)
    categories = Category.query.filter_by(category_type="parent").all()
    title = "Mobile App"
    return render_template("mobile.html", title=title, categories=categories, sug_books=sug_books)


@app.route("/privacy")
def privacy():
    sug_books = random_books(Book, 8)
    categories = Category.query.filter_by(category_type="parent").all()
    title = "Terms & Condition"
    return render_template("privacy.html", title=title, categories=categories, sug_books=sug_books)


@app.route("/contact")
def contact():
    sug_books = random_books(Book, 8)
    categories = Category.query.filter_by(category_type="parent").all()
    title = "Contact"
    return render_template("contact.html", title=title, categories=categories, sug_books=sug_books)


@app.route("/dmca")
def dmca():
    sug_books = random_books(Book, 8)
    categories = Category.query.filter_by(category_type="parent").all()
    title = "DMCA"
    return render_template("dmca.html", title=title, categories=categories, sug_books=sug_books)


@app.route("/feedback")
def feedback():
    sug_books = random_books(Book, 8)
    categories = Category.query.filter_by(category_type="parent").all()
    title = "Feedback"
    return render_template("feedback.html", title=title, categories=categories, sug_books=sug_books)


@app.route("/sitemap")
def sitemap_html():
    # get the unique categories from the database
    categories = Category.query.filter_by(category_type="parent").all()
    title = "Sitemap"
    return render_template("sitemap_html.html", title=title, categories=categories)


# site map for books for each category
# only unique books for each category
@app.route("/sitemap/<int:category_id>/<int:part>")
def sitemap(category_id, part):
    # get the uniqe books based on the category id only
    # where the book name is unique

    if category_id != 999 and part == 1:
        parent = Category.query.filter_by(category_id=category_id).first()
        books = Book.query.filter(or_(
            Book.scrap_cat.like(f'%{parent.category_name},%'),
            Book.scrap_cat.like(f'%,{parent.category_name},%'),
            Book.scrap_cat.like(f'%,{parent.category_name}%'),
            Book.scrap_cat.like(f'{parent.category_name}%'),
        )).all()
        book_links = [url_for('book', book=book.book_title.replace(
            " ", "-") + "-" + book.book_id, _external=True) for book in books]
        sitemap_content = render_template(
            "sitemap.xml", book_links=book_links)
    else:
        # Get the first 1/6 books for category_id 999
        all_books = Book.query.filter_by(category=category_id).all()
        total_books = len(all_books)
        start_index = (part - 1) * (total_books // 30)
        end_index = part * (total_books // 30)
        part_books = all_books[start_index:end_index]

        # Generate book links
        book_links = [url_for('book', book=book.book_title.replace(
            " ", "-") + "-" + str(book.book_id), _external=True) for book in part_books]

        # Render the sitemap template with book links
        sitemap_content = render_template("sitemap.xml", book_links=book_links)

    return Response(sitemap_content, content_type='text/xml')

@app.route("/sitemap.xml")
def sitemap_index():
    sitemap_content = render_template("sitemap_index.xml")
    return Response(sitemap_content, content_type='text/xml')

@app.route("/robots.txt")
def robots_txt():
    robots_content = render_template("robots.txt")
    return robots_content, 200, {'Content-Type': 'text/plain'}
