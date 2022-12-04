from flask import Blueprint, render_template, redirect, url_for, flash, request
from .models import User, Tweet, Follow, Like, Retweet
from . import dictUIDToUser, dictUsernameToUID, dictTweets, dictIDToTwt, dictWords
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
    #print(lists)
    output = []
    q = PriorityQueue()
    for l in lists:
        if l:
            q.put((-(l.head.data.date.timestamp()), l.head))
    while not q.empty():
        val, twt = q.get()
        #print((val, (l, index, lenght)), sep="\n")
        output.append(twt.data)
        if twt.has_next():
            q.put((-(twt.next.data.date.timestamp()), twt.next))
    #print(output)
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
        for twt in sorted_tweets:
            print("likes:", twt.dictLikes)
            print("retweets:", twt.dictRetweets)
        sugg = current_user.get_suggestions()
        return render_template("feed.html", user=current_user, tweets=sorted_tweets, dictUIDToUser=dictUIDToUser, suggestions=sugg, dictIDToTwt=dictIDToTwt)
    if request.method == "POST":
        tweet_title = request.form["title"]
        tweet_content = request.form["tweet"]
        new_tweet = Tweet(
            uid = current_user.id,
            pid=0,
            title = tweet_title,
            content = tweet_content,
            date = datetime.now()
        )
        new_tweet.add_to_db()
        dictTweets[current_user.id].append(new_tweet)
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
    tweetsList = [None] * tweets.size
    twt = tweets.head
    for i in range(tweets.size):
        tweetsList[i] = twt.data
        twt = twt.next
    return render_template("user.html",b=b, tweets=tweetsList, usr=user, is_following=value, followings=followings_users, followers=followers_users, dictIDToTwt=dictIDToTwt, dictUIDToUser=dictUIDToUser)
    

@views.route("/comments/<twt_id>", methods=["GET","POST"])
@login_required
def comments(twt_id):
    twt_id = int(twt_id)
    if request.method == "GET":
        tweet = dictIDToTwt[twt_id]
        username = dictUIDToUser[tweet.uid].username
        comments = [None] * len(tweet.comments)
        usernames = []
        i=0
        for com in tweet.comments:
            usernames.append(dictUIDToUser[com.uid].username)
            comments[i] = com
            i+=1
        return render_template("comments.html", twt=tweet, cmts=comments, dictUIDToUser=dictUIDToUser)
    if request.method == "POST":
        comment = request.form["comment"]
        new_com = Tweet(
            uid = current_user.id,
            pid = twt_id,
            content = comment,
            date = datetime.now(),
            title = ""
        )
        new_com.add_to_db()
        dictIDToTwt[twt_id].comments.add(new_com)
        dictTweets[current_user.id].append(new_com)
        dictIDToTwt[new_com.id] = new_com
        words = re.findall(r'\w+', new_com.content)
        for word in words:
            if word not in dictWords:
                dictWords[word] = []
            dictWords[word].append(new_com)
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
    tweets = dictTweets.pop(current_user.id)
    relations = current_user.get_relations()
    for uid, state in relations.items():
        if state[0] != 0:
            current_user.unfollow(uid)
        if state[1] != 0:
            dictUIDToUser[uid].unfollow(current_user.id)
    for twt in tweets:
        dictIDToTwt[twt.id].delete()
    dictUsernameToUID.pop(current_user.username)
    current_user.delete_from_db()
    dictUIDToUser.pop(current_user.id)
    return redirect(url_for("auth.logout"))