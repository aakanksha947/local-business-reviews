"""Local Business Reviews - a small Flask + SQLite app.

Run:  python app.py   then open http://127.0.0.1:5000
"""
import os
import sqlite3

from flask import Flask, abort, flash, g, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "reviews.db")

CATEGORIES = ["Restaurant", "Cafe", "Salon", "Grocery", "Repair", "Fitness", "Other"]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-in-production")


# ---------- Database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS business (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS review (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL REFERENCES business(id) ON DELETE CASCADE,
            author TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            comment TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    if db.execute("SELECT COUNT(*) FROM business").fetchone()[0] == 0:
        seed(db)
    db.commit()
    db.close()


def seed(db):
    businesses = [
        ("Chai & Chapters", "Cafe", "12 Garden Road", "555-0101",
         "Small cafe with a book swap shelf and strong masala chai."),
        ("Sharma Repairs", "Repair", "48 Market Lane", "555-0102",
         "Phone and laptop repairs, usually done the same day."),
        ("Green Basket", "Grocery", "7 Temple Street", "555-0103",
         "Neighbourhood grocer with fresh local vegetables."),
    ]
    for b in businesses:
        db.execute(
            "INSERT INTO business (name, category, address, phone, description) VALUES (?,?,?,?,?)", b
        )
    reviews = [
        (1, "Asha", 5, "Best chai nearby and a quiet corner to work."),
        (1, "Rohan", 4, "Lovely place, gets crowded on weekends."),
        (2, "Meera", 5, "Fixed my screen in two hours at a fair price."),
        (3, "Imran", 4, "Fresh produce and friendly staff."),
    ]
    for r in reviews:
        db.execute("INSERT INTO review (business_id, author, rating, comment) VALUES (?,?,?,?)", r)


# ---------- Routes ----------
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    sql = """
        SELECT b.*, ROUND(AVG(r.rating), 1) AS avg_rating, COUNT(r.id) AS review_count
        FROM business b LEFT JOIN review r ON r.business_id = b.id
        WHERE 1=1
    """
    params = []
    if q:
        sql += " AND (b.name LIKE ? OR b.description LIKE ? OR b.address LIKE ?)"
        params += [f"%{q}%"] * 3
    if category:
        sql += " AND b.category = ?"
        params.append(category)
    sql += " GROUP BY b.id ORDER BY avg_rating DESC, review_count DESC, b.name"

    businesses = get_db().execute(sql, params).fetchall()
    return render_template("index.html", businesses=businesses, q=q,
                           category=category, categories=CATEGORIES)


@app.route("/business/<int:business_id>")
def business_detail(business_id):
    db = get_db()
    business = db.execute(
        """SELECT b.*, ROUND(AVG(r.rating), 1) AS avg_rating, COUNT(r.id) AS review_count
           FROM business b LEFT JOIN review r ON r.business_id = b.id
           WHERE b.id = ? GROUP BY b.id""",
        (business_id,),
    ).fetchone()
    if business is None:
        abort(404)
    reviews = db.execute(
        "SELECT * FROM review WHERE business_id = ? ORDER BY created_at DESC, id DESC",
        (business_id,),
    ).fetchall()
    return render_template("business.html", business=business, reviews=reviews)


@app.route("/add", methods=["GET", "POST"])
def add_business():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "Other")
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        description = request.form.get("description", "").strip()

        if not name or not address:
            flash("Business name and address are required.", "error")
        elif category not in CATEGORIES:
            flash("Choose a category from the list.", "error")
        else:
            db = get_db()
            cur = db.execute(
                "INSERT INTO business (name, category, address, phone, description) VALUES (?,?,?,?,?)",
                (name, category, address, phone, description),
            )
            db.commit()
            flash("Business added.", "success")
            return redirect(url_for("business_detail", business_id=cur.lastrowid))
    return render_template("add_business.html", categories=CATEGORIES)


@app.route("/business/<int:business_id>/review", methods=["POST"])
def add_review(business_id):
    db = get_db()
    if db.execute("SELECT 1 FROM business WHERE id = ?", (business_id,)).fetchone() is None:
        abort(404)

    author = request.form.get("author", "").strip()
    comment = request.form.get("comment", "").strip()
    try:
        rating = int(request.form.get("rating", 0))
    except ValueError:
        rating = 0

    if not author or not comment or not 1 <= rating <= 5:
        flash("Add your name, a rating from 1 to 5, and a comment.", "error")
    else:
        db.execute(
            "INSERT INTO review (business_id, author, rating, comment) VALUES (?,?,?,?)",
            (business_id, author, rating, comment),
        )
        db.commit()
        flash("Review posted.", "success")
    return redirect(url_for("business_detail", business_id=business_id))


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


@app.template_filter("stars")
def stars(value):
    n = int(round(value or 0))
    return "★" * n + "☆" * (5 - n)


init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
