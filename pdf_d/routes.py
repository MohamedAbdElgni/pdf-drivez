from pdf_d.models import Category, Book
from flask import render_template, url_for, redirect, request, Response, jsonify, send_from_directory
from pdf_d import app
from pdf_d.forms import Filters
from pdf_d.helpers import split_string, remove_duplicates, random_books, make_json
from pdf_d.get_data import vip_search
from sqlalchemy import or_, func
import time
import random
from flask_caching import Cache


@app.errorhandler(Exception)
def handle_error(error):
    # Log the error, if needed
    app.logger.error(error)
    print(error)
    # Redirect to the home page
    return redirect('/')

# Define a specific error handler for 404 (Not Found) errors


@app.errorhandler(404)
def handle_not_found_error(error):
    # Log the error, if needed
    app.logger.error(error)
    

    # Redirect to the home page
    return redirect('/')


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
    books = books.all()
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

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/sitemap.xml')
@cache.cached(timeout=3600)
def sitemap():
    category_links = [url_for('category', category_id=category.category_id,
                              _external=True) for category in Category.query.all()]
    book_links = [url_for('book', book=book.book_title.replace(
        " ", "-") + "-" + book.book_id, _external=True) for book in Book.query.all()]

    sitemap_xml = render_template(
        'sitemap.xml', category_links=category_links, book_links=book_links)
    response = Response(sitemap_xml, mimetype='text/xml')
    return response


@app.route('/robots.txt')
def robots():
    print(app.static_folder)
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

@app.route("/sitemap1.xml")
def sitemap1():
    sitemap1_xml = render_template('sitemap1.xml')
    response = Response(sitemap1_xml, mimetype="text/xml")
    return response

@app.route("/sitemap2.xml")
def sitemap2():
    sitemap2_xml = render_template('sitemap2.xml')
    response = Response(sitemap2_xml, mimetype="text/xml")
    return response

@app.route("/sitemap3.xml")
def sitemap3():
    sitemap3_xml = render_template('sitemap3.xml')
    response = Response(sitemap3_xml, mimetype="text/xml")
    return response

@app.route("/sitemap4.xml")
def sitemap4():
    sitemap4_xml = render_template('sitemap4.xml')
    response = Response(sitemap4_xml, mimetype="text/xml")
    return response

@app.route("/sitemap5.xml")
def sitemap5():
    sitemap5_xml = render_template('sitemap5.xml')
    response = Response(sitemap5_xml, mimetype="text/xml")
    return response

@app.route("/sitemap6.xml")
def sitemap6():
    sitemap6_xml = render_template('sitemap6.xml')
    response = Response(sitemap6_xml, mimetype="text/xml")
    return response

@app.route("/sitemap7.xml")
def sitemap7():
    sitemap7_xml = render_template('sitemap7.xml')
    response = Response(sitemap7_xml, mimetype="text/xml")
    return response

@app.route("/sitemap8.xml")
def sitemap8():
    sitemap8_xml = render_template('sitemap8.xml')
    response = Response(sitemap8_xml, mimetype="text/xml")
    return response

@app.route("/sitemap9.xml")
def sitemap9():
    sitemap9_xml = render_template('sitemap9.xml')
    response = Response(sitemap9_xml, mimetype="text/xml")
    return response

@app.route("/sitemap10.xml")
def sitemap10():
    sitemap10_xml = render_template('sitemap10.xml')
    response = Response(sitemap10_xml, mimetype="text/xml")
    return response
