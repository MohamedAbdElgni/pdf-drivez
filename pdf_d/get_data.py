import logging
from pdf_d.models import Category, Cat_Links, Book
from pdf_d import app, db
from flask import url_for
import requests
import random
from bs4 import BeautifulSoup
import re
import os
import time
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import aliased, subqueryload
from sqlalchemy.orm import aliased


def get_cat(mod=Category):
    # this is the url of the website to get main categories
    url = "https://www.pdfdrive.com/"

    html = requests.get(url)
    # parse the html
    soup = BeautifulSoup(html.text, "html.parser")
    # get the books info
    categories = soup.find_all("div", class_="categories-list")

    soup = BeautifulSoup(str(categories), "html.parser")
    i = 0
    # Extract the last part of the 'href'
    for cat in soup.find_all("a", href=True):
        category_name = cat.get_text()  # Get the text inside the <a> element
        category_img_link = cat.img[
            "src"
        ]  # Get the 'src' attribute of the <img> element
        category_link = cat["href"]
        category_type = "parent"
        category_text = "None"
        category_id = category_link.split("/")[-1]
        parent_category_id = "None"

        # insert into dbmodel Category

        category = mod(
            category_id=category_id.strip(),
            category_name=category_name.strip(),
            category_image_link=f"https://www.pdfdrive.com{category_img_link.strip()}",
            category_link=f"https://www.pdfdrive.com{category_link.strip()}",
            category_type=category_type.strip(),
            category_text=category_text.strip(),
            category_parent_id=parent_category_id.strip(),
            category_group=category_name.strip(),
        )

        db.session.add(category)
        db.session.commit()
        i += 1
    print(f"number of categories added: {i}")
    return f"number of categories added: {i}"


def get_sub_cat(mod=Category):
    """so lets be clear
    this function will get the sub categories of each category
    first we will get the category link from the db
    then we will get the sub categories of each category
    then we will insert them into the db
    the parent category will be the category we got from the db
    each url for category will be like this
    https://www.pdfdrive.com/category/category_id
    and for each category we will get the sub categories
    they can be parent cat act like a sub cat so we will handle that
    by checking if the category is already in the db
    if it is we will also add it as a sub cat but its parent will be the category we got from the db
    """
    categories = mod.query.all()
    category_links = [category.category_link for category in categories]
    category_group = [category.category_group for category in categories]
    x = 0
    for i in category_links:
        url = i
        html = requests.get(url)
        parent_category_ID = url.split("/")[-1]
        # parse the html
        soup = BeautifulSoup(html.text, "html.parser")
        cats = soup.find_all(
            "div", class_="categories-list subcategories-list mt-4")

        soup = BeautifulSoup(str(cats), "html.parser")
        for cat in soup.find_all("a", href=True):
            category_name = cat.get_text()  # Get the text inside the <a> element
            category_img_link = cat.img[
                "src"
            ]  # Get the 'src' attribute of the <img> element
            category_link = cat["href"]
            category_type = "child"
            category_text = "None"
            category_id = category_link.split("/")[-1]
            parent_category_id = parent_category_ID
            # insert into dbmodel Category
            category = mod(
                category_id=category_id.strip(),
                category_name=category_name.strip(),
                category_image_link=f"https://www.pdfdrive.com{category_img_link.strip()}",
                category_link=f"https://www.pdfdrive.com{category_link.strip()}",
                category_type=category_type.strip(),
                category_text=category_text.strip(),
                category_parent_id=parent_category_id.strip(),
                category_group=category_group[x],
            )
            db.session.add(category)
            db.session.commit()
            print(f"category added: {category_name}")
        x += 1
        # set timeout in the loop to avoid getting banned
        time.sleep(1)

    return "done"


def get_pages_for_cats(url=None, cat_name=None, cat_id=None):
    cat = Category.query.filter_by(category_type="child").all()
    cat_model = Cat_Links()
    for category in cat:
        cat_id = category.category_id
        cat_name = category.category_name
        url = category.category_link
        url_list = []
        html = requests.get(url)
        soup = BeautifulSoup(html.text, 'html.parser')
        pagenathin_div = soup.find('div', class_='Zebra_Pagination')
        soup = BeautifulSoup(str(pagenathin_div), "html.parser")
        for li_element in soup.find_all('li', string='…'):
            li_element.extract()
        for li_element in soup.find_all('li'):
            url_list.append(li_element.find('a')['href'])
        try:
            last_numbers = [re.search(r'/p(\d+)/', url).group(1)
                            for url in url_list if re.search(r'/p(\d+)/', url)]
            if last_numbers:
                cat_max_page = int(max(last_numbers))
            else:
                cat_max_page = 1
        except ValueError:
            # Handle the case where there are non-integer values in last_numbers
            cat_max_page = 1

        # insert into dbmodel Cat_Links
        cat_model = Cat_Links(
            cat_id=cat_id,
            cat_name=cat_name,
            cat_link_start_link=url.strip(),
            cat_max_page=cat_max_page,
        )
        db.session.add(cat_model)
        db.session.commit()

    return "done"


def generate_pdfdrive_urls(base_url, max_page):
    pdfdrive_urls = [base_url]
    if max_page > 1:
        for page in range(2, max_page + 1):
            pdfdrive_urls.append(f"{base_url}/p{page}/")
    else:
        pass

    return pdfdrive_urls


def get_books_div(url):
    # get the html
    html = requests.get(url)
    # parse the html
    soup = BeautifulSoup(html.text, "html.parser")
    # get the books info
    books_div = soup.find_all("div", {"class": "files-new"})
    # get the books link
    soup = BeautifulSoup(str(books_div), "html.parser")
    for li_element in soup.find_all('li', class_='liad'):
        li_element.extract()

    return soup


def get_books(param=bool):
    book = Book()

    # do it with `~` first then try with then only scrap with this 2 links
    excluded_links = [
        "https://www.pdfdrive.com/category/112",
        "https://www.pdfdrive.com/category/113"
    ]
    if param:
        cat_links = db.session.query(Cat_Links).filter(
            ~Cat_Links.cat_link_start_link.in_(excluded_links)).all()
    else:
        cat_links = db.session.query(Cat_Links).filter(
            Cat_Links.cat_link_start_link.in_(excluded_links)).all()
    cat_primary_link = [cat.cat_link_start_link for cat in cat_links]
    cat_max_page = int(max([cat.cat_max_page for cat in cat_links]))
    cat_cat_id = [cat.cat_id for cat in cat_links]
    print(cat_primary_link, cat_max_page)
    for link in cat_primary_link:
        cat_all_url = generate_pdfdrive_urls(link, max_page=cat_max_page)
        for url, cat_id in zip(cat_all_url, cat_cat_id):
            result = get_books_div(url)
            cat_id = cat_id
            for li_element in result.find_all('li'):
                # Extract book title, year, image link, and pages as before
                title = li_element.find('h2').text.strip()
                year = li_element.find('span', class_='fi-year').text.strip()
                img_link = li_element.find('img')['data-original']
                pages = li_element.find('span', class_='fi-pagecount')
                if pages:
                    pages = pages.text.strip()
                else:
                    pages = 'Unknown'
                description = li_element.find(
                    'div', class_='file-info').next_sibling.strip()
                book_link = li_element.find('a')['href'].strip()
                book_id = li_element.find('a')['data-id']
                book_category = cat_id
                book_size = li_element.find(
                    'span', class_='fi-size hidemobile').text.strip()
                # insert into dbmodel Book

                book = Book(
                    book_id=book_id,
                    book_title=title,
                    book_author="None",
                    category=book_category,
                    book_download_link=book_link,
                    book_size=book_size,
                    book_img_link=img_link,
                    book_pages=pages,
                    year=year,
                    book_description=description,
                )
                db.session.add(book)
                db.session.commit()
                print(f"book added: {title}")
            # set timeout in the loop to avoid getting banned
            time.sleep(.5)
    return "done"


def scrap_book_cats(book_dl):
    """ helper function for get_cat_for_every_book"""
    # this function will scrap the book categories and return a list of categories
    # get the book link
    book_link = "https://www.pdfdrive.com"+book_dl
    # get the html
    html = requests.get(book_link)
    # parse the html
    soup = BeautifulSoup(html.text, "html.parser")
    # get the categories
    try:
        cats = soup.find_all('div', class_='ebook-tags')[0].find_all('a')
        categories = [a.text for a in cats]
    except IndexError:
        categories = []
    try:
        book_author = soup.find_all(
            'div', class_='ebook-author')[0].find_all('a')[0].text
    except IndexError:
        book_author = ""

    return categories, book_author


def get_cat_for_every_book(mod):
    """this function will get the category for every book
    and update the book row with the category and author with out insert more rows
    """
    books = mod.query.all()
    for book in books:
        book_dl = book.book_download_link
        categories, book_author = scrap_book_cats(book_dl)
        # if book_author == "": add none to the author
        if book_author == "":
            book_author = "None"
        if categories == []:
            categories = "None"
        book.book_author = book_author
        book.scrap_cat = ",".join(categories)
        db.session.commit()
        print(f"book updated: {book.book_title}")

#############################################
# this function for search route in the app #
#############################################


def vip_search(q):
    """this function will search for the books on the website
        and insert the books into the db
        this is the example url for the search
        https://www.pdfdrive.com/search?q=rich+dad+poor+dad+dsadsad&pagecount=&pubyear=&searchin=&em=&more=true

    """
    q = q.replace(" ", "+")
    base_url = f"https://www.pdfdrive.com/search?q={q}&pagecount=&pubyear=&searchin=&em=&more=true"
    
    

    # get the books
    soup = get_books_div(base_url)
    # get the books link
    for li_element in soup.find_all('li'):
        # Extract book title, year, image link, and pages as before
        title = li_element.find('h2').text.strip()
        year = li_element.find('span', class_='fi-year').text.strip()
        img_link = li_element.find('img')['data-original']
        pages = li_element.find('span', class_='fi-pagecount')
        if pages:
            pages = pages.text.strip()
        else:
            pages = 'Unknown'
        description = li_element.find(
            'div', class_='file-info').next_sibling.strip()
        book_link = li_element.find('a')['href'].strip()
        book_id = li_element.find('a')['data-id']
        book_category = 999
        book_size = li_element.find(
            'span', class_='fi-size hidemobile').text.strip()

        if not Book.query.filter_by(book_id=book_id).first():

            book = Book(
                book_id=book_id,
                book_title=title,
                book_author="None",
                category=book_category,
                book_download_link=book_link,
                book_size=book_size,
                book_img_link=img_link,
                book_pages=pages,
                year=year,
                book_description=description,
            )
            db.session.add(book)
            db.session.commit()
        else:
            continue
    return "done"
###################################
# Important functions for the app #
###################################


def get_search_keywords():
    """
    Retrieves a list of search keywords from the PDF Drive website.
    --- helper function for get_start_url_for_keywords ---
    Returns:
        A list of strings representing search keywords.
    """
    url = "https://www.pdfdrive.com/category/16"
    html = requests.get(url)
    # parse the html
    soup = BeautifulSoup(html.text, "html.parser")
    ul_element = soup.find("ul", class_="search-tags")
    a_tags = ul_element.find_all("a")
    secret_cats = [a.text for a in a_tags]
    return secret_cats


def get_start_url_for_keywords(keywords):
    """
    Given a list of keywords, generates a start URL for each keyword and adds it to the Cat_Links table in the database.
    If the keyword already exists in the table, it skips to the next keyword.
    Returns "done" when all keywords have been processed.
    --- This gonna be the first function to run after the app is deployed----
    args:
        keywords: the get_search_keywords function
    """
    keywords = get_search_keywords()
    base_url = "https://www.pdfdrive.com/"
    for cat in keywords:
        start_url = base_url + f"{cat.replace(' ','-')}-books.html"
        request = requests.get(start_url)
        soup = BeautifulSoup(request.text, "html.parser")
        page_div = soup.find("div", class_="Zebra_Pagination")
        page_nums = []
        if page_div:
            for a_element in page_div.find_all("a"):
                text = a_element.get_text()
                if text.isdigit():
                    page_nums.append(int(text))
        # get the max page number
        try:
            max_page = max(page_nums)
        except ValueError:
            max_page = 1
        # check if cat name is in the cat_links table if not add it else got to the next cat
        cat_link = Cat_Links.query.filter_by(cat_name=cat).first()
        if not cat_link:
            cat_link = Cat_Links(
                cat_id=999,
                cat_name=cat,
                cat_link_start_link=start_url,
                cat_max_page=max_page,
            )
            db.session.add(cat_link)
            db.session.commit()
            print(f"cat added: {cat}")
        else:
            print(f"cat already in the db: {cat}")
            continue
    return "done"


def generate_urls_for_keywords(word, max_page):
    """returns a dict of urls max pages and the original keyword 
        -- helper function for get_latest_books_from_key_words --
    Args:
        word (str): the keyword
    Example:
        >>> generate_urls_for_keywords("the power of now", 2)
        >>> {'urls': 
                        ['https://www.pdfdrive.com/the-power-of-now-books.html', 
                        'https://www.pdfdrive.com/search?q=the%20power%20of%20now&pagecount=&pubyear=&searchin=&page=2',
                        'https://www.pdfdrive.com/search?q=the%20power%20of%20now&pagecount=&pubyear=&searchin=&page=3',],
                        'max_page': 2, 'keyword': 'the power of now'}
    """
    word = word
    max_page = int(max_page)
    results = {}
    search_word = word.replace(" ", "%20")
    base_url = "https://www.pdfdrive.com/"
    urls = [base_url + f"{word.replace(' ','-')}-books.html"]
    if max_page > 1:
        for page in range(2, max_page + 1):
            urls.append(
                f"{base_url}search?q={search_word}&pagecount=&pubyear=&searchin=&page={page}"
            )
    else:
        pass
    results["urls"] = urls
    results["max_page"] = max_page
    results["keyword"] = word

    return results


def get_latest_books_from_key_words():
    """this function will get the books for each keyword and add it to the db
        with a category of new 999
        then reset he got_it col to 1
        -- this function will be called by a cron job every 24 hours --
    """
    # get cat names and max pages for each cat where got_it col<1
    cats_from_db = Cat_Links.query.filter_by(got_it=0).all()
    cat_names = [cat.cat_name for cat in cats_from_db]
    cat_max_page = [cat.cat_max_page for cat in cats_from_db]
    # generate urls for each cat and scrap the books
    for cat_name, cat_max in zip(cat_names, cat_max_page):
        urls = generate_urls_for_keywords(cat_name, cat_max)

        db.session.commit()
        for url in urls["urls"]:
            # add here the time out
            try:
                result = get_books_div(url)
            except requests.exceptions.ConnectionError:
                print("connection error")
                print("sleeping for 10 seconds")
                time.sleep(10)
                continue
            for li_element in result.find_all('li'):
                # Extract book title, year, image link, and pages as before
                title = li_element.find('h2').text.strip()
                year = li_element.find('span', class_='fi-year').text.strip()
                img_link = li_element.find('img')['data-original']
                pages = li_element.find('span', class_='fi-pagecount')
                if pages:
                    pages = pages.text.strip()
                else:
                    pages = 'Unknown'
                description = li_element.find(
                    'div', class_='file-info').next_sibling.strip()
                book_link = li_element.find('a')['href'].strip()
                book_id = li_element.find('a')['data-id']
                book_category = 999
                book_size = li_element.find(
                    'span', class_='fi-size hidemobile').text.strip()
                # check if the book is already in the db with the id and the book_title
                if Book.query.filter_by(book_id=book_id).first():
                    print(f"book already in the db: {title}")
                    continue
                else:
                    # insert into dbmodel Book
                    book = Book(
                        book_id=book_id,
                        book_title=title,
                        book_author="None",
                        category=book_category,
                        book_download_link=book_link,
                        book_size=book_size,
                        book_img_link=img_link,
                        book_pages=pages,
                        year=year,
                        book_description=description if len(
                            description) > 10 else title,
                        scrap_cat="New",
                    )
                    db.session.add(book)
                    db.session.commit()
                    print(f"book added: {title}")
            # set random timeout in the loop to avoid getting banned

            time.sleep(random.randint(1, 8))
        # make the got_it col = 1
        reset_the_cat_to_got_it = Cat_Links.query.filter_by(
            cat_name=cat_name).first()
        reset_the_cat_to_got_it.got_it = 1
        db.session.commit()
    return "done"


# with app.app_context():
#      #insert the new category to the db for the depolyment
    # category = Category(category_id=999,
    #                   category_name="New",
    #                   category_image_link="https://illustoon.com/photo/7899.png",
    #                   category_type="parent", category_text="None",
    #                   category_parent_id=113,
    #                   category_group="New")
    # db.session.add(category)
    # db.session.commit()
#     #get_start_url_for_keywords(keywords=None)
#     #get_latest_books_from_key_words()

