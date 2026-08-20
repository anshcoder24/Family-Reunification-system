from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "family-reunification-secret-key"


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_db_connection():

    conn = sqlite3.connect("family.db")

    conn.row_factory = sqlite3.Row

    return conn


# =====================================================
# CREATE / UPDATE TABLES
# =====================================================

def create_tables():

    conn = get_db_connection()

    # =================================================
    # PERSONS TABLE
    # =================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            camp TEXT NOT NULL,
            family_name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            status TEXT DEFAULT 'Searching',
            created_at TEXT NOT NULL
        )
    """)


    # =================================================
    # USERS TABLE
    # =================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            person_id INTEGER
        )
    """)


    # =================================================
    # MIGRATION - PERSONS
    # =================================================

    person_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(persons)"
        ).fetchall()
    ]


    if "phone" not in person_columns:

        conn.execute("""
            ALTER TABLE persons
            ADD COLUMN phone TEXT
        """)


    if "email" not in person_columns:

        conn.execute("""
            ALTER TABLE persons
            ADD COLUMN email TEXT
        """)


    if "status" not in person_columns:

        conn.execute("""
            ALTER TABLE persons
            ADD COLUMN status TEXT DEFAULT 'Searching'
        """)


    if "created_at" not in person_columns:

        conn.execute("""
            ALTER TABLE persons
            ADD COLUMN created_at TEXT DEFAULT ''
        """)


    # =================================================
    # MIGRATION - USERS
    # =================================================

    user_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(users)"
        ).fetchall()
    ]


    if "role" not in user_columns:

        conn.execute("""
            ALTER TABLE users
            ADD COLUMN role TEXT DEFAULT 'user'
        """)


    if "person_id" not in user_columns:

        conn.execute("""
            ALTER TABLE users
            ADD COLUMN person_id INTEGER
        """)


    # =================================================
    # CREATE / FIX ADMIN ACCOUNT
    # =================================================

    admin_email = "admin@gmail.com"
    admin_password = "admin123"


    admin = conn.execute("""
        SELECT *
        FROM users
        WHERE email = ?
    """, (admin_email,)).fetchone()


    # -----------------------------------------------
    # ADMIN DOES NOT EXIST
    # -----------------------------------------------

    if admin is None:

        password_hash = generate_password_hash(
            admin_password
        )


        conn.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                role,
                person_id
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Admin",
            admin_email,
            password_hash,
            "admin",
            None
        ))


    # -----------------------------------------------
    # ADMIN ALREADY EXISTS
    # -----------------------------------------------

    else:

        # Reset admin account properly
        # This ensures admin123 always works
        password_hash = generate_password_hash(
            admin_password
        )


        conn.execute("""
            UPDATE users

            SET
                name = ?,
                password = ?,
                role = 'admin',
                person_id = NULL

            WHERE email = ?
        """, (
            "Admin",
            password_hash,
            admin_email
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


    conn.close()


    return render_template(
        "index.html",
        total_registrations=total_registrations
    )


# =====================================================
# SIGN IN CHOICE PAGE
# =====================================================

@app.route("/signin")
def signin():

    return render_template(
        "signin.html"
    )


# =====================================================
# ADMIN LOGIN
# =====================================================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        conn = get_db_connection()


        user = conn.execute("""
            SELECT *
            FROM users

            WHERE LOWER(email) = ?

            AND role = 'admin'
        """, (email,)).fetchone()


        conn.close()


        # ---------------------------------------------
        # CHECK ADMIN LOGIN
        # ---------------------------------------------

        if user:

            try:

                password_correct = check_password_hash(
                    user["password"],
                    password
                )

            except Exception:

                password_correct = False


            if password_correct:

                session.clear()


                session["user_id"] = user["id"]

                session["user_name"] = user["name"]

                session["role"] = "admin"


                return redirect(
                    url_for("dashboard")
                )


        # ---------------------------------------------
        # LOGIN FAILED
        # ---------------------------------------------

        return render_template(
            "admin_login.html",
            error="Invalid admin email or password."
        )


    return render_template(
        "admin_login.html"
    )


# =====================================================
# USER LOGIN
# =====================================================

@app.route("/user-login", methods=["GET", "POST"])
def user_login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        conn = get_db_connection()


        user = conn.execute("""
            SELECT *
            FROM users

            WHERE LOWER(email) = ?

            AND role = 'user'
        """, (email,)).fetchone()


        conn.close()


        if user:

            try:

                password_correct = check_password_hash(
                    user["password"],
                    password
                )

            except Exception:

                password_correct = False


            if password_correct:

                session.clear()


                session["user_id"] = user["id"]

                session["user_name"] = user["name"]

                session["role"] = "user"

                session["person_id"] = user["person_id"]


                return redirect(
                    url_for("user_dashboard")
                )


        return render_template(
            "user_login.html",
            error="Invalid email or password."
        )


    return render_template(
        "user_login.html"
    )


# =====================================================
# REGISTER PERSON + USER ACCOUNT
# =====================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()


        age = request.form.get(
            "age",
            ""
        ).strip()


        gender = request.form.get(
            "gender",
            ""
        ).strip()


        camp = request.form.get(
            "camp",
            ""
        ).strip()


        family_name = request.form.get(
            "family_name",
            ""
        ).strip()


        phone = request.form.get(
            "phone",
            ""
        ).strip()


        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        # ---------------------------------------------
        # REQUIRED FIELDS
        # ---------------------------------------------

        if not name or not age or not gender or not camp or not family_name:

            return render_template(
                "register.html",
                error="Please fill all required fields."
            )


        # ---------------------------------------------
        # EMAIL + PASSWORD
        # ---------------------------------------------

        if not email or not password:

            return render_template(
                "register.html",
                error="Email and password are required."
            )


        # ---------------------------------------------
        # PREVENT ADMIN EMAIL REGISTRATION
        # ---------------------------------------------

        if email == "admin@gmail.com":

            return render_template(
                "register.html",
                error="This email is reserved for administrator."
            )


        # ---------------------------------------------
        # DATE
        # ---------------------------------------------

        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )


        # ---------------------------------------------
        # PASSWORD HASH
        # ---------------------------------------------

        password_hash = generate_password_hash(
            password
        )


        conn = get_db_connection()


        # ---------------------------------------------
        # CHECK DUPLICATE EMAIL
        # ---------------------------------------------

        existing_user = conn.execute("""
            SELECT id
            FROM users
            WHERE LOWER(email) = ?
        """, (email,)).fetchone()


        if existing_user:

            conn.close()


            return render_template(
                "register.html",
                error="This email is already registered."
            )


        # ---------------------------------------------
        # INSERT PERSON
        # ---------------------------------------------

        cursor = conn.execute("""
            INSERT INTO persons
            (
                name,
                age,
                gender,
                camp,
                family_name,
                phone,
                email,
                status,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            age,
            gender,
            camp,
            family_name,
            phone,
            email,
            "Searching",
            created_at
        ))


        person_id = cursor.lastrowid


        # ---------------------------------------------
        # CREATE USER ACCOUNT
        # ---------------------------------------------

        conn.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                role,
                person_id
            )

            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            email,
            password_hash,
            "user",
            person_id
        ))


        conn.commit()

        conn.close()


        return redirect(
            url_for("user_login")
        )


    return render_template(
        "register.html"
    )


# =====================================================
# ADMIN DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    # ---------------------------------------------
    # LOGIN CHECK
    # ---------------------------------------------

    if "user_id" not in session:

        return redirect(
            url_for("admin_login")
        )


    # ---------------------------------------------
    # ADMIN ONLY
    # ---------------------------------------------

    if session.get("role") != "admin":

        return redirect(
            url_for("user_dashboard")
        )


    conn = get_db_connection()


    # ---------------------------------------------
    # TOTAL REGISTRATIONS
    # ---------------------------------------------

    total_registrations = conn.execute("""
        SELECT COUNT(*) AS total
        FROM persons
    """).fetchone()["total"]


    # ---------------------------------------------
    # FAMILY MATCHES
    # ---------------------------------------------

    family_matches = conn.execute("""
        SELECT COUNT(*) AS total
        FROM persons
        WHERE status = 'Reunited'
    """).fetchone()["total"]


    # ---------------------------------------------
    # PENDING / SEARCHING
    # ---------------------------------------------

    pending_sync = conn.execute("""
        SELECT COUNT(*) AS total
        FROM persons
        WHERE status != 'Reunited'
    """).fetchone()["total"]


    # ---------------------------------------------
    # ALL PERSON RECORDS
    # ---------------------------------------------

    persons = conn.execute("""
        SELECT *
        FROM persons
        ORDER BY id DESC
    """).fetchall()


    conn.close()


    return render_template(
        "dashboard.html",

        total_registrations=total_registrations,

        family_matches=family_matches,

        pending_sync=pending_sync,

        persons=persons
    )


# =====================================================
# USER DASHBOARD
# =====================================================

@app.route("/user-dashboard")
def user_dashboard():

    # ---------------------------------------------
    # LOGIN CHECK
    # ---------------------------------------------

    if "user_id" not in session:

        return redirect(
            url_for("user_login")
        )


    # ---------------------------------------------
    # USER ONLY
    # ---------------------------------------------

    if session.get("role") != "user":

        return redirect(
            url_for("dashboard")
        )


    person_id = session.get(
        "person_id"
    )


    # ---------------------------------------------
    # FIND PERSON
    # ---------------------------------------------

    conn = get_db_connection()


    person = conn.execute("""
        SELECT *
        FROM persons
        WHERE id = ?
    """, (person_id,)).fetchone()


    conn.close()


    if person is None:

        return "Your registration record was not found."


    return render_template(
        "user_dashboard.html",
        person=person
    )


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()


    return redirect(
        url_for("home")
    )


# =====================================================
# SEARCH
# =====================================================

@app.route("/search")
def search():

    return "Search Family Member Page"


# =====================================================
# ABOUT
# =====================================================

@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# =====================================================
# CAMPS
# =====================================================

@app.route("/camps")
def camps():

    return "Camps Page"


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    create_tables()


    print("")
    print("==============================================")
    print("       FAMILY REUNIFICATION SYSTEM")
    print("==============================================")
    print("")
    print("Admin Login:")
    print("Email    : admin@gmail.com")
    print("Password : admin123")
    print("")
    print("Admin Dashboard:")
    print("http://127.0.0.1:8000/dashboard")
    print("")
    print("==============================================")
    print("")


    app.run(
        debug=True,
        port=800
    )