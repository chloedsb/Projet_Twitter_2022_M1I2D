from flask import Blueprint, render_template, redirect, url_for, flash, request
from .models import User, Tweet, Follow, Comment, Like, Retweet
from . import dictUIDToUser, dictUsernameToUID, dictTweets, dictComments, dictIDToTwt, dictWords
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
        following = current_user.get_following()
        for uid in following:
            tweets.append(dictTweets[uid])
        tweets.append(dictTweets[current_user.id])
        sorted_tweets = sort_tweets(tweets)
        sugg = current_user.get_suggestions()
        for twt in sorted_tweets:
            print(twt.dictRetweets)
        return render_template("feed.html", user=current_user, tweets=sorted_tweets, dictUIDToUser=dictUIDToUser, suggestions=sugg)
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
        words = re.findall(r'\w+', new_tweet.content)
        for word in words:
            if word not in dictWords:
                dictWords[word] = []
            dictWords[word].append(new_tweet)
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
    followings_users = []
    followers_users = []
    for uid in followings:
        followings_users.append(dictUIDToUser[uid])
    for uid in followers:
        followers_users.append(dictUIDToUser[uid])
    return render_template("user.html",b=b, tweets=tweets, usr=user, is_following=value, followings=followings_users, followers=followers_users)
    

@views.route("/comments/<twt_id>", methods=["GET","POST"])
@login_required
def comments(twt_id):
    if request.method == "GET":
        tweet = Tweet.query.filter_by(id=twt_id).first() #à remplacer
        username = dictUIDToUser[tweet.uid].username
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

def delete_(twt_id):
    tweet = dictIDToTwt[int(twt_id)]
    #Delete all the retweets object from db & from ds
    #...
    #Delete tweet from dictWords
    words = re.findall(r'\w+', tweet.content)
    for word in words:
        dictWords[word].remove(tweet)
    #Deletions
    dictTweets[tweet.uid].remove(tweet)
    coms = dictComments.pop(int(twt_id))
    dictIDToTwt.pop(int(twt_id))
    for com in coms:
        com.delete_from_db()
    for uid, like in tweet.dictLikes.items():
        like.delete_from_db()
    tweet.delete_from_db()

@views.route("/delete/<twt_id>")
@login_required
def delete(twt_id):
    delete_(twt_id)
    return redirect(url_for("views.feed"))

@views.route("/retweet/<twt_id>")
@login_required
def retweet(twt_id):
    twt = dictIDToTwt[int(twt_id)]
    twt.retweet(current_user.id)
    dir = request.args.get('redirect')
    if dir == "feed":
        return redirect(url_for("views.feed"))
    else:
        return redirect(url_for("views.user", usr=dir))

@views.route("/like/<twt_id>")
@login_required
def like(twt_id):
    tweet = dictIDToTwt[int(twt_id)]
    tweet.like(current_user.id)
    dir = request.args.get('redirect')
    if dir == "feed":
        return redirect(url_for("views.feed"))
    else:
        return redirect(url_for("views.user", usr=dir))

@views.route("/unlike/<twt_id>")
@login_required
def unlike(twt_id):
    tweet = dictIDToTwt[int(twt_id)]
    tweet.unlike(current_user.id)
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
        delete_(twt.id)
    dictUsernameToUID.pop(current_user.username)
    current_user.delete_from_db()
    dictUIDToUser.pop(current_user.id)
    return redirect(url_for("auth.logout"))