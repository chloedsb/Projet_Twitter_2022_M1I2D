from flask import Blueprint, render_template, redirect, url_for, flash, request
from .models import User, Tweet, Follow, Comment, Like
from . import dictFollow, dictUIDToUser, dictUsernameToUID, dictTweets, dictComments, dictIDToTwt
from queue import PriorityQueue
from flask_login import login_required, current_user
from datetime import datetime

views = Blueprint('views', __name__)

@views.route("/")
def home():
    return render_template("home.html")

@views.route("/search", methods=["POST"])
@login_required
def search():
    usr_searched = request.form["username"]
    if usr_searched:
        return redirect(url_for("views.user", usr=usr_searched))

def sort_tweets(lists):
    print(lists)
    output = []
    q = PriorityQueue()
    for l in lists:
        if l:
            q.put((-(l[0].date.timestamp()), (l, 0, len(l))))
    while not q.empty():
        val, (l, index, lenght) = q.get()
        #print(val, (l, index, lenght), sep="\n")
        output.append(l[index])
        index+=1
        if index<lenght:
            q.put((-(l[index].date.timestamp()), (l, index, lenght)))
    return output


@views.route("/feed", methods=["GET","POST"])
@login_required
def feed():
    if request.method == "GET":
            tweets = []
            relations = current_user.get_relations()
            for uid, state in relations.items():
                if state[0] != 0:
                    tweets.append(dictTweets[uid]) 
            tweets.append(dictTweets[current_user.id])
            sorted_tweets = sort_tweets(tweets)
            #sorted_usernames = []
            """likes = []
            for twt in sorted_tweets:
                #sorted_usernames.append(dictUIDToUser[twt.uid].username)
                likes.appe"""

                
                
            return render_template("feed.html", user=current_user, tweets=sorted_tweets, dictUIDToUser=dictUIDToUser)
    if request.method == "POST":
        tweet_title = request.form["title"]
        tweet_content = request.form["tweet"]
        new_tweet = Tweet(
            uid = current_user.id,
            title = tweet_title,
            content = tweet_content,
            date = datetime.now()
        )
        new_tweet.add_to_db()
        dictTweets[current_user.id].append(new_tweet)
        dictComments[new_tweet.id] = []
        dictIDToTwt[new_tweet.id] = new_tweet
        return redirect(url_for("views.feed"))

@views.route("/follow/<usr>", methods=["GET","POST"])
@login_required
def follow(usr):
    id = dictUsernameToUID[usr]
    f = Follow(
        id_follower = current_user.id,
        id_followee = id
    )
    f.add_to_db()
    current_user.follow(id, f)
    return redirect(url_for("views.user", usr=usr))

@views.route("/unfollow/<usr>", methods=["GET","POST"])
@login_required
def unfollow(usr):
    id = dictUsernameToUID[usr]
    current_user.unfollow(id)

    return redirect(url_for("views.user", usr=usr))

@views.route("/profile/<usr>", methods=["GET","POST"])
@login_required
def user(usr):
    id = dictUsernameToUID.get(usr)
    if not id:
        flash("Username doesn't exist", category="error")
        return redirect(url_for("views.feed"))
    if id == current_user.id:
        user = current_user
        b = False
        value = True
    else:
        user = dictUIDToUser[id]
        value = current_user.is_following(id)
        b = True
    tweets = dictTweets[id]
    relations = user.get_relations()
    followings = []
    followers = []
    for uid, state in relations.items():
        if state[0] != 0:
            followings.append(dictUIDToUser[int(uid)])
        if state[1] != 0:
            followers.append(dictUIDToUser[int(uid)])
    return render_template("user.html",b=b, tweets=tweets, usr=user, is_following=value, followings=followings, followers=followers)
    

@views.route("/comments/<twt_id>", methods=["GET","POST"])
@login_required
def comments(twt_id):
    if request.method == "GET":
        tweet = Tweet.query.filter_by(id=twt_id).first() #à remplacer
        username = dictUIDToUser[tweet.uid].username
        print(dictComments)
        comments = dictComments[int(twt_id)]
        usernames = []
        for com in comments:
            usernames.append(dictUIDToUser[int(com.uid)].username)
        return render_template("comments.html", twt=tweet, usr=username, cmts=comments, usrs=usernames)
    if request.method == "POST":
        comment = request.form["comment"]
        new_com = Comment(
            uid = current_user.id,
            t_id = twt_id,
            content = comment,
            date = datetime.now()
        )
        new_com.add_to_db()
        dictComments[int(twt_id)].append(new_com)
        return redirect(url_for("views.comments", twt_id=twt_id))

@views.route("/delete/<twt_id>")
@login_required
def delete(twt_id):
    tweet = dictIDToTwt[int(twt_id)]
    dictTweets[tweet.uid].remove(tweet)
    coms = dictComments.pop(int(twt_id))
    dictIDToTwt.pop(int(twt_id))
    for com in coms:
        com.delete_from_db()
    for like in tweet.listLikes:
        like.delete_from_db()
    tweet.delete_from_db()
    return redirect(url_for("views.feed"))

@views.route("/like/<twt_id>")
@login_required
def like(twt_id):
    tweet = dictIDToTwt[int(twt_id)]
    like = Like(
        t_id = twt_id,
        uid = current_user.id
    )
    like.add_to_db()
    tweet.listLikes.append(like)
    dir = request.args.get('redirect')
    if dir == "feed":
        return redirect(url_for("views.feed"))
    else:
        return redirect(url_for("views.user", usr=dir))

@views.route("/unlike/<twt_id>")
@login_required
def unlike(twt_id):
    tweet = Tweet.query.filter_by(id=twt_id).first() #à remplacer
    for like in tweet.listLikes:
        if like.uid == current_user.id:
            tweet.listLikes.remove(like)
            like.delete_from_db()
            break
    dir = request.args.get('redirect')
    if dir == "feed":
        return redirect(url_for("views.feed"))
    else:
        return redirect(url_for("views.user", usr=dir))

@views.route("/profile")
def profile():
    return redirect(url_for("views.user", usr=current_user.username))


@views.route("/delete_account")
@login_required
def delete_account():
    tweets = dictTweets.pop(current_user.id)
    relations = current_user.get_relations()
    for uid, state in relations.items():
        if state[0] != 0:
            current_user.unfollow(uid)
        if state[1] != 0:
            dictUIDToUser[uid].unfollow(current_user.id)
    for twt in tweets:
        list_com = dictComments.pop(twt.id)
        for com in list_com:
            com.delete_from_db()
        twt.delete_from_db()
        
    dictUsernameToUID.pop(current_user.username)
    current_user.delete_from_db()
    dictUIDToUser.pop(current_user.id)
    return redirect(url_for("auth.logout"))