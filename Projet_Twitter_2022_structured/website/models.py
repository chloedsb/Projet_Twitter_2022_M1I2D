from . import db, dictFollowing, dictFollowed, dictUIDToUser, dictUsernameToUID, dictTweets, dictComments, dictIDToTwt, dictWords
from sqlalchemy.sql import func
from flask_login import UserMixin, current_user
from datetime import datetime
import re

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(24))
    email = db.Column(db.String(64))
    pwd = db.Column(db.String(64))

    @staticmethod
    def loadUserData():
        us = User.query.all()
        for u in us:
            dictUIDToUser[u.id] = u
            dictUsernameToUID[u.username] = u.id
            dictFollowing[u.id] = dict()
            dictFollowed[u.id] = dict()
            dictTweets[u.id] = []

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
        #Return a list of usernames from people you might follow
        #Followees from your followees you don't already follow
        #Doit etre rapide ! --> à changer
        sugg = []
        followings = dictFollowing[self.id].keys()
        for uid in followings:
            f = list(dictFollowing[uid].keys())
            for f_2 in f:
                if (f_2 not in sugg) and (f_2 not in followings):
                    sugg.append(dictUIDToUser[f_2].username)
        return sugg




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
    title = db.Column(db.String(256))
    content = db.Column(db.String(2048))
    date = db.Column(db.DateTime(timezone=True), default=func.now())

    dictLikes = dict()
    dictRetweets = dict()

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
            date= datetime.now()
        )
        rt.add_to_db()
        self.dictRetweets[uid] = rt
    
    def retweeted_by_current(self):
        return current_user.id in self.dictRetweets.keys()



    @staticmethod
    def loadTweetData():
        twts = Tweet.query.all()
        for twt in twts:
            dictTweets[twt.uid].append(twt) #idem ?
            dictComments[twt.id] = [] #plutot linked list ?
            dictIDToTwt[twt.id] = twt
            #Remplir dictWords
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

    def __eq__(self, other):
        """Overrides the default implementation"""
        return self.id == other.id

    

class Comment(db.Model):
    __tablename__ = "comment"
    id = db.Column("id", db.Integer, primary_key=True, nullable=False)
    uid = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    t_id = db.Column(db.Integer, db.ForeignKey("tweet.id"), nullable=False)
    content = db.Column(db.String(400))
    date = db.Column(db.DateTime(timezone=True), default=func.now())


    @staticmethod
    def loadCommentData():
        cmts = Comment.query.all()
        for cmt in cmts:
            dictComments[cmt.t_id].append(cmt)

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
