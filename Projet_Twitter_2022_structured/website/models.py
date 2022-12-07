from sqlalchemy import orm

from . import db, dictFollowing, dictFollowed, dictUIDToUser, dictUsernameToUID, dictTweets, dictIDToTwt, \
    dictWords, dictTwtIdToNode, dictReTweets, dictRtIdToNode
from sqlalchemy.sql import func
from flask_login import UserMixin, current_user
from datetime import datetime
from .linkedLists import *

import re


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(24))
    email = db.Column(db.String(64))
    pwd = db.Column(db.Integer) #Integer because it is hashed password

    @orm.reconstructor
    def init_on_load(self):
        self.like_set = set()
        self.retweet_set = set()

    def __init__(self, username, email, pwd):
        self.init_on_load()
        super(User, self).__init__(username=username, email=email, pwd=pwd)

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id

    @staticmethod
    def loadUserData():
        #Loading the data from the database at launch
        us = User.query.all()
        for u in us:
            dictUIDToUser[u.id] = u
            dictUsernameToUID[u.username] = u.id
            dictFollowing[u.id] = dict()
            dictFollowed[u.id] = dict()
            dictTweets[u.id] = linked_list()
            dictReTweets[u.id] = linked_list()

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def tweet(self, content, pid=0, title=""):
        new_tweet = Tweet(
            uid=self.id,
            pid=pid,
            title=title,
            content=content,
            date=datetime.now()
        )
        new_tweet.add_to_db()
        dictTwtIdToNode[new_tweet.id] = dictTweets[current_user.id].append(new_tweet)
        dictIDToTwt[new_tweet.id] = new_tweet
        if new_tweet.is_a_comment():
            dictIDToTwt[pid].comments.add(new_tweet)
        words = re.findall(r'\w+', new_tweet.content)
        for word in words:
            if word not in dictWords:
                dictWords[word] = set()
            dictWords[word].add(new_tweet)

    def follow(self, uid):
        f = Follow(
            id_follower=current_user.id,
            id_followee=uid
        )
        f.add_to_db()
        dictFollowing[self.id][uid] = f
        dictFollowed[uid][self.id] = f

    def unfollow(self, uid):
        dictFollowing[current_user.id][uid].delete_from_db()
        dictFollowing[self.id].pop(uid)
        dictFollowed[uid].pop(self.id)

    def is_following(self, uid):
        return uid in dictFollowing[self.id]

    def is_followed(self, uid):
        return uid in dictFollowed[self.id]

    def get_following(self):
        return dictFollowing[self.id].keys()

    def get_followers(self):
        return dictFollowed[self.id].keys()

    def get_suggestions(self):
        # Return a list of usernames from people you might follow
        # Followees from your followees you don't already follow
        sugg = set()
        for uid in dictFollowing[self.id]:
            for user in dictFollowing[uid]:
                if user not in dictFollowing[self.id]:
                    sugg.add(dictUIDToUser[user].username)
        return sugg


class Follow(db.Model):
    __tablename__ = "follow"
    f_id = db.Column(db.Integer, primary_key=True)
    id_follower = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    id_followee = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    @staticmethod
    def loadFollowData():
        # Loading the data from the database at launch
        fs = Follow.query.all()
        for f in fs:
            dictUIDToUser[f.id_follower].follow(f.id_followee, f)

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


class Tweet(db.Model):
    __tablename__ = "tweet"
    id = db.Column("id", db.Integer, primary_key=True, nullable=False)
    uid = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    pid = db.Column(db.Integer, db.ForeignKey("tweet.id"), nullable=False)#0 if it is a normal tweet, the tweet ID it is answering to if it is a reply
    title = db.Column(db.String(256))
    content = db.Column(db.String(2048))
    date = db.Column(db.DateTime(timezone=True), default=func.now())

    @orm.reconstructor
    def init_on_load(self):
        # Instance variables during the first load
        self.dictLikes = dict()
        self.dictRetweets = dict()
        self.comments = set()

    def __init__(self, uid, pid, title, content, date):
        self.init_on_load()
        super(Tweet, self).__init__(uid=uid, pid=pid, title=title, content=content, date=date)

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id

    def is_a_comment(self):
        return not (self.pid == 0)

    def liked_by_current(self):
        return self.liked_by(current_user.id)

    def liked_by(self, uid):
        return uid in self.dictLikes

    def like(self, uid):
        like = Like(
            t_id=self.id,
            uid=uid
        )
        like.add_to_db()
        dictUIDToUser[uid].like_set.add(self.id)
        self.dictLikes[uid] = like

    def unlike(self, uid):
        dictUIDToUser[uid].like_set.remove(self.id)
        self.dictLikes.pop(uid).delete_from_db()

    def retweet(self, uid):
        rt = Retweet(
            t_id=self.id,
            uid=uid,
            date=datetime.now()
        )
        rt.add_to_db()
        dictUIDToUser[uid].retweet_set.add(self.id)
        self.dictRetweets[uid] = rt
        dictRtIdToNode[rt.id] = dictReTweets[uid].append(rt)

    def unretweet(self, uid):
        rt = self.dictRetweets.pop(uid)
        node = dictRtIdToNode[rt.id]
        dictReTweets[uid].remove(node)
        dictUIDToUser[uid].retweet_set.remove(self.id)
        rt.delete_from_db()

    def retweeted_by_current(self):
        return self.retweeted_by(current_user.id)

    def retweeted_by(self, uid):
        return uid in self.dictRetweets

    def delete(self, cascade=False):
        # Delete tweet from dictWords
        words = re.findall(r'\w+', self.content)
        for word in words:
            dictWords[word].remove(self)
            if not dictWords[word]:
                dictWords.pop(word)
        #Deleting comments
        for com in self.comments:
            com.delete(True)
            #Cascade = True so that we don't modify self.comments while looping through it
        if self.is_a_comment():
            tweet = dictIDToTwt[self.pid]
            if not cascade: tweet.comments.remove(self)
            #If cascade we don't remove the comment from tweets.comments because tweet will be deleted altogether
        #Deleting likes
        for uid, like in self.dictLikes.items():
            dictUIDToUser[uid].like_set.remove(self.id)
            like.delete_from_db()
        #Deleting retweets
        for uid, rt in self.dictRetweets.items():
            node = dictRtIdToNode[rt.id]
            dictReTweets[uid].remove(node)
            dictUIDToUser[uid].retweet_set.remove(self.id)
            rt.delete_from_db()
        dictIDToTwt.pop(self.id)
        #Deleting the tweet from the linked list containing all the user's tweets
        node = dictTwtIdToNode[self.id]
        l = dictTweets[self.uid]
        l.remove(node)
        self.delete_from_db()

    @staticmethod
    def loadTweetData():
        # Loading the data from the database at launch
        twts = Tweet.query.all()
        for twt in twts:
            dictTwtIdToNode[twt.id] = dictTweets[twt.uid].append(twt)
            dictIDToTwt[twt.id] = twt
            if twt.is_a_comment():
                dictIDToTwt[twt.pid].comments.add(twt)
            # Instancing the dictionary linking the tweets and words for the search functionality
            words = re.findall(r'\w+', twt.content)
            for word in words:
                if word not in dictWords:
                    dictWords[word] = set()
                dictWords[word].add(twt)

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


class Retweet(db.Model):
    __tablename__ = "retweet"
    id = db.Column("id", db.Integer, primary_key=True, nullable=False)
    t_id = db.Column(db.Integer, db.ForeignKey("tweet.id"), nullable=False)
    uid = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id

    @staticmethod
    def loadRetweetData():
        # Loading the data from the database at launch
        rts = Retweet.query.all()
        for rt in rts:
            twt = dictIDToTwt[rt.t_id]
            dictUIDToUser[rt.uid].retweet_set.add(twt.id)
            twt.dictRetweets[rt.uid] = rt
            dictRtIdToNode[rt.id] = dictReTweets[rt.uid].append(rt)

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


class Like(db.Model):
    __tablename__ = "like"
    id = db.Column("id", db.Integer, primary_key=True, nullable=False)
    t_id = db.Column(db.Integer, db.ForeignKey("tweet.id"), nullable=False)
    uid = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    @staticmethod
    def loadLikeData():
        # Loading the data from the database at launch
        likes = Like.query.all()
        for like in likes:
            twt = dictIDToTwt[like.t_id]
            dictUIDToUser[like.uid].like_set.add(twt.id)
            twt.dictLikes[like.uid] = like

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
