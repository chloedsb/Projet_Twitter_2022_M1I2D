from flask import Blueprint, session, request, redirect, url_for, flash, render_template
from .models import User, Tweet, Follow
from . import dictFollowing, dictFollowed, dictUIDToUser, dictUsernameToUID, dictTweets
from flask_login import login_user, login_required, logout_user, current_user
import re
#from werkzeug.security import generate_password_hash, check_password_hash
#in db: password = generate_password_hash(pwd1, method='sha256')

auth = Blueprint('auth', __name__)

@auth.route("/login", methods = ["GET","POST"])
def login():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("views.feed"))
        return render_template("login.html")
    if request.method == "POST":
        mail = request.form["mail"]
        pwd = request.form["pwd"]
        user = User.query.filter_by(email=mail).first()
        if user:
            if not(user.pwd == pwd):
                flash("Incorrect password", category="error")
                return redirect(url_for("auth.login"))
            else:
                login_user(user, remember=True)
                flash("You have been logged in succesfully !", category="success")
                return redirect(url_for("views.feed"))
        #Si user == None
        flash("We do not know your mail", category="error")
        return redirect(url_for("auth.login"))

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("views.home"))

def check_password(password):
    #https://stackoverflow.com/questions/16709638/checking-the-strength-of-a-password-how-to-check-conditions
    length_error = len(password) < 8
    length_error_2 = len(password) >64
    digit_error = re.search(r"\d", password) is None
    uppercase_error = re.search(r"[A-Z]", password) is None
    lowercase_error = re.search(r"[a-z]", password) is None
    password_ok = not ( length_error or length_error_2 or digit_error or uppercase_error or lowercase_error)

    return {
        'password_ok' : password_ok,
        'length_error' : length_error,
        'length_error_2' : length_error_2,
        'digit_error' : digit_error,
        'uppercase_error' : uppercase_error,
        'lowercase_error' : lowercase_error,
    }

messages = {
    'length_error' : "Password must contains at least 8 characters",
    'length_error_2' : "Password must contains at most 64 characters",
    'digit_error' : "Password must contains at least 1 digit",
    'uppercase_error' : "Password must contains at least 1 uppercase",
    'lowercase_error' : "Password must contains at least 1 lowercase"
    }


@auth.route("/register", methods=["GET","POST"])
def register():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("views.feed"))
        return render_template("register.html")
    elif request.method == "POST":
        usr_name = request.form["usr_name"]
        mail = request.form["mail"]
        pwd = request.form["pwd"]
        pwd_c = request.form["pwd2"]
        #Steps to check the entries
        if dictUsernameToUID[usr_name]:
            flash("Username already exists, choose another", category="error")
            return redirect(url_for("auth.register"))
        if User.query.filter_by(email=mail).first():
            flash("Email address already exists, please login", category="error")
            return redirect(url_for("auth.login"))
        if pwd != pwd_c:
            flash("The two passwords aren't the same, please retry", category="error")
            return redirect(url_for("auth.register"))
        pwd_check = check_password(pwd)
        if pwd_check['length_error']:
            flash(messages['length_error'], category="error")
        if pwd_check['length_error_2']:
            flash(messages['length_error_2'], category="error")
        if pwd_check['digit_error']:
            flash(messages['digit_error'], category="error")
        if pwd_check['uppercase_error']:
            flash(messages['uppercase_error'], category="error")
        if pwd_check['lowercase_error']:
            flash(messages['lowercase_error'], category="error")
        if pwd_check['password_ok']:
            new_user = User(
            username = usr_name,
            email = mail,
            pwd = pwd
            )
            new_user.add_to_db()
            dictUIDToUser[new_user.id] = new_user
            dictUsernameToUID[new_user.username] = new_user.id
            dictFollowing[new_user.id] = dict()
            dictFollowed[new_user.id] = dict()
            dictTweets[new_user.id] = []
            #User is logged in
            login_user(new_user, remember=True)
            flash("You are succesfully registered", category="success")
            return redirect(url_for("views.feed"))
        return redirect(url_for("auth.register"))
