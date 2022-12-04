from sqlalchemy import orm

from . import db, dictFollowing, dictFollowed, dictUIDToUser, dictUsernameToUID, dictTweets, dictComments, dictIDToTwt, \
    dictWords, dictTwtIdToNode
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
    pwd = db.Column(db.String(64))

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id

    @staticmethod
    def loadUserData():
        us = User.query.all()
        for u in us:
            dictUIDToUser[u.id] = u
            dictUsernameToUID[u.username] = u.id
            dictFollowing[u.id] = dict()
            dictFollowed[u.id] = dict()
            dictTweets[u.id] = linked_list()

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def follow(self, uid, f):
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

    def get_followers_of_followers(self):
        #Question 2
        fof = set()
        for uid in dictFollowed[self.id]:
            for user in dictFollowed[uid]:
                if user not in dictFollowed[self.id]:
                    fof.add(dictUIDToUser[user].username)
        return fof


class Follow(db.Model):
    __tablename__ = "follow"
    f_id = db.Column(db.Integer, primary_key=True)
    id_follower = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    id_followee = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    @staticmethod
    def loadFollowData():
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
    pid = db.Column(db.Integer, db.ForeignKey("tweet.id"), nullable=False)
    title = db.Column(db.String(256))
    content = db.Column(db.String(2048))
    date = db.Column(db.DateTime(timezone=True), default=func.now())

    def __init__(self, uid, pid, title, content, date):
        self.init_on_load()
        super(Tweet, self).__init__(uid=uid, pid=pid, title=title, content=content, date=date)

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id

    @orm.reconstructor
    def init_on_load(self):
        # Instance variables during the first load
        self.dictLikes = dict()
        self.dictRetweets = dict()
        self.comments = set()

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
        self.dictLikes[uid] = like

    def unlike(self, uid):
        self.dictLikes.pop(uid).delete_from_db()

    def retweet(self, uid):
        rt = Retweet(
            t_id=self.id,
            uid=uid,
            date=datetime.now()
        )
        rt.add_to_db()
        self.dictRetweets[uid] = rt

    def unretweet(self, uid):
        self.dictLikes.pop(uid).delete_from_db()

    def retweeted_by_current(self):
        return self.liked_by(current_user.id)

    def retweeted_by(self, uid):
        return uid in self.dictRetweets

    def delete(self, cascade=False):
        # Delete all the retweets object from db & from ds
        # ...
        # Delete tweet from dictWords
        words = re.findall(r'\w+', self.content)
        for word in words:
            dictWords[word].remove(self)
            if not dictWords[word]:
                dictWords.pop(word)
        # Deletions
        for com in self.comments:
            com.delete(True)
        if self.is_a_comment():
            tweet = dictIDToTwt[self.pid]
            if not cascade: tweet.comments.remove(self)
        for uid, like in self.dictLikes.items():
            like.delete_from_db()
        for uid, rt in self.dictRetweets.items():
            rt.delete_from_db()
        dictIDToTwt.pop(self.id)

        node = dictTwtIdToNode[self.id]
        l = dictTweets[self.uid]
        l.remove(node)
        self.delete_from_db()

    @staticmethod
    def loadTweetData():
        twts = Tweet.query.all()
        for twt in twts:
            dictTweets[twt.uid].append(twt)  # idem ?
            dictTwtIdToNode[twt.id] = dictTweets[twt.uid].head
            dictIDToTwt[twt.id] = twt
            if twt.is_a_comment():
                dictIDToTwt[twt.pid].comments.add(twt)
                print(twt.content)
            # Remplir dictWords
            words = re.findall(r'\w+', twt.content)
            for word in words:
                if word not in dictWords:
                    dictWords[word] = []
                dictWords[word].append(twt)

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

    @staticmethod
    def loadRetweetData():
        rts = Retweet.query.all()
        for rt in rts:
            twt = dictIDToTwt[rt.t_id]
            twt.retweet(rt.uid)

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
        likes = Like.query.all()
        for like in likes:
            twt = dictIDToTwt[like.t_id]
            twt.like(like.uid)

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
