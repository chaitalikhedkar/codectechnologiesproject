import os
import sqlite3
import boto3
from flask import Flask, render_template, request, redirect, session, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# AWS S3 connection
s3 = boto3.client(
    "s3",
    aws_access_key_id="Your_access_key_id",
    aws_secret_access_key="Your_secret_access_key"
)

BUCKET_NAME = "chaitali2004"


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Register
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users(username,email,password) VALUES(?,?,?)",
            (username,email,password)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")


# Login
@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username,password)
    )

    user = cursor.fetchone()

    if user:
        session["user"] = user[0]
        return redirect("/dashboard")

    return "Invalid login"


# Dashboard
@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM videos")
    videos = cursor.fetchall()

    conn.close()

    return render_template("dashboard.html", videos=videos)


# Upload Video
@app.route("/upload", methods=["GET","POST"])
def upload():

    if request.method == "POST":

        title = request.form["title"]
        file = request.files["video"]

        filename = secure_filename(file.filename)

        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        # Upload to AWS S3
        s3.upload_file(
            path,
            BUCKET_NAME,
            filename
        )

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO videos(title,filename,user_id) VALUES(?,?,?)",
            (title,filename,session["user"])
        )

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("upload.html")


# Watch Video
@app.route("/watch/<id>")
def watch(id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM videos WHERE id=?", (id,))
    video = cursor.fetchone()

    conn.close()

    return render_template("watch.html", video=video)


# Serve uploaded files
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory("uploads", filename)


if __name__ == "__main__":
    app.run(debug=True)

# Delete Video
@app.route("/delete/<id>")
def delete(id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get filename
    cursor.execute("SELECT filename FROM videos WHERE id=?", (id,))
    video = cursor.fetchone()

    if video:
        filename = video[0]

        # Delete file from uploads folder
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete from database
        cursor.execute("DELETE FROM videos WHERE id=?", (id,))
        conn.commit()

    conn.close()

    return redirect("/dashboard")