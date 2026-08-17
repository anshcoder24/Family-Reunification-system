from flask import Flask, render_template, request
import sqlite3
from datetime import datetime

app = Flask(__name__)


# ================= DATABASE CONNECTION =================

def get_db_connection():
    conn = sqlite3.connect("family.db")
    return conn


# ================= HOME =================

@app.route("/")
def home():
    return render_template("index.html")


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():

    # When Register form is submitted
    if request.method == "POST":

        # Required fields
        name = request.form["name"]
        age = request.form["age"]
        gender = request.form["gender"]
        camp = request.form["camp"]
        family_name = request.form["family_name"]

        # Optional fields
        phone = request.form.get("phone")

        # Current date and time
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


        # Connect database
        conn = get_db_connection()


        # Insert data
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


        # Save changes
        conn.commit()

        # Close database
        conn.close()


        return """
        <h2>Registration Successful!</h2>
        <p>Person has been registered successfully.</p>
        <a href="/register">Register Another Person</a>
        """


    # When page is opened
    return render_template("register.html")


# ================= SEARCH =================

@app.route("/search")
def search():
    return "Search Family Member Page"


# ================= ABOUT =================

@app.route("/about")
def about():
    return render_template("about.html")


# ================= SIGN IN =================

@app.route("/signin")
def signin():
    return render_template("signin.html")


# ================= CAMPS =================

@app.route("/camps")
def camps():
    return "Camps Page"


# ================= RUN APP =================

if __name__ == "__main__":
    app.run(debug=True, port=1500)