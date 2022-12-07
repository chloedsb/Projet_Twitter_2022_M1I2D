from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

#we use expire_on_commit false to be able to call attributes of our classes without having to look in the data base again
db = SQLAlchemy(session_options={"expire_on_commit": False})

#dict {user_id1 : {dict user_id2 : follow object if user1 follows user2}}
dictFollowing = dict()
#dict {user_id1 : {dict user_id2 : follow object if user2 follows user1}}
dictFollowed = dict()
#dict {user_id : user object}
dictUIDToUser = dict()
#dict {username : user_id}
dictUsernameToUID = dict()
#dict {user_id : linked_list containing all of user's tweets, sorted by date}
dictTweets = dict()
#dict {user_id : linked_list containing all of user's retweets, sorted by date}
dictReTweets = dict()
#dict {tweet_id : tweet object}
dictIDToTwt = dict()
#dict {word : set of tweets containing that word}
dictWords = dict()
#dict {tweet_id : node of linked list in dictTweets containing that tweet} (used to delete tweets in O(1))
dictTwtIdToNode = dict()
#dict {retweet_id : node of linked list in dictReTweets containing that retweet} (used to delete retweets in O(1))
dictRtIdToNode = dict()
#set of all registered emails
mailSet = set()

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
        id = int(id)
        if id in dictUIDToUser:
            return dictUIDToUser[id]
        else:
            return None

    return app
