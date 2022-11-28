from . import db, dictFollow, dictUIDToUser, dictUsernameToUID, dictTweets, dictComments, dictIDToTwt
from sqlalchemy.sql import func
from flask_login import UserMixin, current_user

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
            dictFollow[u.id] = dict()
            dictTweets[u.id] = []

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def follow(self, uid, f):
        if not (uid in dictFollow[self.id]):
            dictFollow[self.id][uid] = [0, 0]
        dictFollow[self.id][uid][0] = f
        if not (self.id in dictFollow[uid]):
            dictFollow[uid][self.id] = [0, 0]
        dictFollow[uid][self.id][1] = f

    def unfollow(self, uid):
        dictFollow[current_user.id][uid][0].delete_from_db()
        dictFollow[self.id][uid][0] = 0
        if dictFollow[self.id][uid] == [0, 0]:
            dictFollow[self.id].pop(uid)
        dictFollow[uid][self.id][1] = 0
        if dictFollow[uid][self.id] == [0, 0]:
            dictFollow[uid].pop(self.id)

    def is_following(self, uid):
        if not (uid in dictFollow[self.id]):
            return False
        return dictFollow[self.id][uid][0] != 0

    def is_followed(self, uid):
        if not (uid in dictFollow[self.id]):
            return False
        return dictFollow[self.id][uid][1] != 0

    def get_relations(self):
        return dictFollow[self.id]



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

    listLikes = []

    def liked_by_current(self):
        for like in self.listLikes:
            if like.uid == current_user.id:
                return True
        return False


    @staticmethod
    def loadTweetData():
        twts = Tweet.query.all()
        for twt in twts:
            dictTweets[twt.uid].append(twt) #idem ?
            dictComments[twt.id] = [] #plutot linked list ?
            dictIDToTwt[twt.id] = twt



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

    #@staticmethod
    """def loadRetweetData():
        """

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
            twts = Tweet.query.filter_by(id=like.t_id).all()
            for twt in twts:
                twt.listLikes.append(like)

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
