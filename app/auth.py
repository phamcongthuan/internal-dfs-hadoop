from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app import db
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            if user.is_locked == 0:
                session["username"] = user.username
                return redirect(url_for("home"))
            else:
                flash("This user is locked.")
                return redirect(url_for("auth.login"))
        else:
            flash("Invalid username or password.")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, storage_limit=1 * 1024)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful. Please log in.")
            return redirect(url_for("auth.login"))
        except IntegrityError:
            db.session.rollback()
            flash("Username already exists.")
            return redirect(url_for("auth.register"))

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out.")
    return redirect(url_for("auth.login"))
