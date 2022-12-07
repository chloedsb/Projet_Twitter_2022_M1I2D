from flask import Blueprint, render_template, redirect, url_for, flash, request
from . import dictUIDToUser, dictUsernameToUID, dictTweets, dictIDToTwt, dictWords, dictReTweets, mailSet, \
    dictTwtIdToNode
from .linkedLists import linked_list
from queue import PriorityQueue
from flask_login import login_required, current_user
from datetime import datetime
import re

views = Blueprint('views', __name__)

@views.route("/")
def home():
    return render_template("home.html")

@views.route("/search", methods=["POST"])
@login_required
def search():
    typed = request.form["username"]
    """if typed.startswith("word:"):
        typed = typed.replace("word:", "")
        twts = dictWords.get(typed)
        if not twts:
            flash("Sorry, no results for your search", category="error")
            return redirect(url_for("views.feed"))
        return render_template("display.html", tweets=twts, word=typed, dictUIDToUser=dictUIDToUser)"""
    id = dictUsernameToUID.get(typed)
    if id:
        return redirect(url_for("views.user", usr=typed))
    else:
        twts = dictWords.get(typed)
        if not twts:
            flash("Sorry, no results for your search", category="error")
            return redirect(url_for("views.feed"))
        return render_template("display.html", tweets=twts, word=typed, dictUIDToUser=dictUIDToUser)
    

def sort_tweets(lists):
    #PriorityQueue sort because all lists are previously sorted
    q = PriorityQueue()
    for l in lists:
        if l.size>0:
            q.put(((l.tail.data.date.timestamp()), l.tail))
    output = linked_list()
    while not q.empty():
        val, twt = q.get()
        output.append(twt.data)
        if twt.has_prev():
            q.put(((twt.prev.data.date.timestamp()), twt.prev))
    return output

@views.route("/feed", methods=["GET","POST"])
@login_required
def feed():
    if request.method == "GET":
        following = current_user.get_following()
        tweets = [None]*(len(following)*2+2)
        index = 0
        for uid in following:
            tweets[index] = dictTweets[uid]
            tweets[index+1] = dictReTweets[uid]
            index+=2
        tweets[index] = dictTweets[current_user.id]
        tweets[index+1] = dictReTweets[current_user.id]
        sorted_tweets = sort_tweets(tweets)
        sugg = current_user.get_suggestions()
        return render_template("feed.html", user=current_user, tweets=sorted_tweets, dictUIDToUser=dictUIDToUser, suggestions=sugg, dictIDToTwt=dictIDToTwt)
    if request.method == "POST":
        tweet_title = request.form["title"]
        tweet_content = request.form["tweet"]
        current_user.tweet(title=tweet_title, content=tweet_content)
        return redirect(url_for("views.feed"))

@views.route("/follow/<usr>", methods=["GET","POST"])
@login_required
def follow(usr):
    id = dictUsernameToUID[usr]
    current_user.follow(id)
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
    if id == current_user.id:
        user = current_user
        b = False
        value = True
    else:
        user = dictUIDToUser[id]
        value = current_user.is_following(id)
        b = True
    tweets = dictTweets[id]
    followings = user.get_following()
    followers = user.get_followers()
    return render_template("user.html",b=b, tweets=tweets, usr=user, is_following=value, followings=followings, followers=followers, dictIDToTwt=dictIDToTwt, dictUIDToUser=dictUIDToUser)
    

@views.route("/comments/<twt_id>", methods=["GET","POST"])
@login_required
def comments(twt_id):
    twt_id = int(twt_id)
    if request.method == "GET":
        tweet = dictIDToTwt[twt_id]
        username = dictUIDToUser[tweet.uid].username
        comments = [None] * len(tweet.comments)
        i=0
        for com in tweet.comments:
            comments[i] = com
            i+=1
        return render_template("comments.html", twt=tweet, cmts=comments, dictUIDToUser=dictUIDToUser)
    if request.method == "POST":
        comment = request.form["comment"]
        current_user.tweet(content=comment, pid=twt_id)
        return redirect(url_for("views.comments", twt_id=twt_id))

@views.route("/delete/<twt_id>")
@login_required
def delete(twt_id):
    twt_id = int(twt_id)
    dictIDToTwt[twt_id].delete()
    return redirect(url_for("views.feed"))

@views.route("/retweet/<twt_id>")
@login_required
def retweet(twt_id):
    twt_id = int(twt_id)
    twt = dictIDToTwt[twt_id]
    twt.retweet(current_user.id)
    dir = request.args.get('redirect')
    if dir == "feed":
        return redirect(url_for("views.feed"))
    elif dir in dictUsernameToUID:
        return redirect(url_for("views.user", usr=dir))
    else:
        return redirect(url_for("views.comments", twt_id=dir))

@views.route("/unretweet/<twt_id>")
@login_required
def unretweet(twt_id):
    twt_id = int(twt_id)
    twt = dictIDToTwt[twt_id]
    twt.unretweet(current_user.id)
    dir = request.args.get('redirect')
    if dir == "feed":
        return redirect(url_for("views.feed"))
    elif dir in dictUsernameToUID:
        return redirect(url_for("views.user", usr=dir))
    else:
        return redirect(url_for("views.comments", twt_id=dir))

@views.route("/like/<twt_id>")
@login_required
def like(twt_id):
    twt_id = int(twt_id)
    tweet = dictIDToTwt[twt_id]
    tweet.like(current_user.id)
    dir = request.args.get('redirect')
    if dir == "feed":
        return redirect(url_for("views.feed"))
    elif dir in dictUsernameToUID:
        return redirect(url_for("views.user", usr=dir))
    else:
        return redirect(url_for("views.comments", twt_id=dir))

@views.route("/unlike/<twt_id>")
@login_required
def unlike(twt_id):
    twt_id = int(twt_id)
    tweet = dictIDToTwt[twt_id]
    tweet.unlike(current_user.id)
    dir = request.args.get('redirect')
    if dir == "feed":
        return redirect(url_for("views.feed"))
    elif dir in dictUsernameToUID:
        return redirect(url_for("views.user", usr=dir))
    else:
        return redirect(url_for("views.comments", twt_id=dir))
        

@views.route("/profile")
def profile():
    return redirect(url_for("views.user", usr=current_user.username))


@views.route("/delete_account")
@login_required
def delete_account():
    tweets = dictTweets[current_user.id]
    followers = current_user.get_followers()
    following = current_user.get_following()
    likes = current_user.like_set.copy()
    retweets = current_user.retweet_set.copy()
    for uid in followers:
        dictUIDToUser[uid].unfollow(current_user.id)
    for uid in following:
        current_user.unfollow(uid)
    for like in likes:
        dictIDToTwt[like].unlike(current_user.id)
    for rt in retweets:
        dictIDToTwt[rt].unretweet(current_user.id)
    while tweets.head:
        tweets.head.data.delete()
    dictUsernameToUID.pop(current_user.username)
    current_user.delete_from_db()
    dictUIDToUser.pop(current_user.id)
    mailSet.remove(current_user.email)
    return redirect(url_for("auth.logout"))