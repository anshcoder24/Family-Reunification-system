from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Session ke liye
app.secret_key = "family-reunification-secret-key"


# =====================================================
# DATABASE
# =====================================================

def get_db_connection():
    conn = sqlite3.connect("family.db")
    conn.row_factory = sqlite3.Row
    return conn


# =====================================================
# CREATE TABLES + ADMIN USER
# =====================================================

def create_tables():

    conn = get_db_connection()

    # Registered persons
    conn.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            camp TEXT NOT NULL,
            family_name TEXT NOT NULL,
            phone TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Login users
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Admin user
    admin = conn.execute("""
        SELECT id
        FROM users
        WHERE email = ?
    """, ("admin@gmail.com",)).fetchone()

    if admin is None:

        conn.execute("""
            INSERT INTO users
            (name, email, password)
            VALUES (?, ?, ?)
        """, (
            "Admin",
            "admin@gmail.com",
            "admin123"
        ))

    conn.commit()
    conn.close()


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():

    conn = get_db_connection()

    total_registrations = conn.execute("""
        SELECT COUNT(*) AS total
        FROM persons
    """).fetchone()["total"]

    persons = conn.execute("""
        SELECT *
        FROM persons
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        total_registrations=total_registrations,
        persons=persons
    )


# =====================================================
# REGISTER PERSON
# =====================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        camp = request.form.get("camp", "").strip()
        family_name = request.form.get("family_name", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not age or not gender or not camp or not family_name:

            return render_template(
                "register.html",
                error="Please fill all required fields."
            )

        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO persons
            (
                name,
                age,
                gender,
                camp,
                family_name,
                phone,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            age,
            gender,
            camp,
            family_name,
            phone,
            created_at
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    return render_template("register.html")


# =====================================================
# SIGN IN
# =====================================================

@app.route("/signin", methods=["GET", "POST"])
def signin():

    if request.method == "POST":

        email = request.form.get("login", "").strip()
        password = request.form.get("password", "").strip()

        print("================================")
        print("LOGIN ATTEMPT")
        print("Email:", email)
        print("Password:", password)

        conn = get_db_connection()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        conn.close()

        print("User:", user)

        if user and user["password"] == password:

            # Login session
            session.clear()

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            print("LOGIN SUCCESS")
            print("Session:", dict(session))

            return redirect(url_for("dashboard"))

        print("LOGIN FAILED")

        return render_template(
            "signin.html",
            error="Invalid email or password."
        )

    return render_template("signin.html")


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    print("================================")
    print("DASHBOARD")
    print("Session:", dict(session))

    # Login check
    if "user_id" not in session:

        print("NO LOGIN SESSION")

        return redirect(url_for("signin"))

    conn = get_db_connection()

    total_registrations = conn.execute("""
        SELECT COUNT(*) AS total
        FROM persons
    """).fetchone()["total"]

    persons = conn.execute("""
        SELECT *
        FROM persons
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_registrations=total_registrations,
        persons=persons,
        user_name=session.get("user_name")
    )


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =====================================================
# OTHER PAGES
# =====================================================

@app.route("/search")
def search():
    return "Search Family Member Page"


@app.route("/about")
def about():
    return "About Page"


@app.route("/camps")
def camps():
    return "Camps Page"


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    create_tables()

    app.run(
        debug=True,
        port=8000
    )