from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

db = SQLAlchemy(session_options={"expire_on_commit": False})
#session_options=

dictFollowing = dict()
dictFollowed = dict()
dictUIDToUser = dict()
dictUsernameToUID = dict()
#dictTweets sera = {uid:LinkedList(Tweets de uid)} peut etre
dictTweets = dict()
dictComments = dict()
dictIDToTwt = dict()
dictWords = dict()
dictTwtIdToNode = dict()

def create_app():
    app = Flask(__name__)
    app.secret_key = "keykey"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sqlitedb.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = 0
    db.init_app(app)

    

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    from .models import User, Tweet, Follow, Like

    with app.app_context():
        db.create_all()
        User.loadUserData()
        Follow.loadFollowData()
        Tweet.loadTweetData()
        Like.loadLikeData()

    login_manager = LoginManager()
    login_manager.login_view = "views.home"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        if int(id) in dictUIDToUser:
            return dictUIDToUser[int(id)]
        else:
            return None

    return app
