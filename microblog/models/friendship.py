# -*- coding: utf-8 -*-
import datetime
from microblog.database import db


Friendship = db.Table(
    'friendship',
    db.Column('from_id', db.Integer, db.ForeignKey('people.id'), primary_key=True),
    db.Column('to_id', db.Integer, db.ForeignKey('people.id'), primary_key=True),
    db.Column('follow_time', db.DateTime, default=datetime.datetime.now),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
)


Blackship = db.Table(
    'blackship',
    db.Column('from_id', db.Integer, db.ForeignKey('people.id'), primary_key=True),
    db.Column('to_id', db.Integer, db.ForeignKey('people.id'), primary_key=True),
    db.Column('block_time', db.DateTime, default=datetime.datetime.now)
)


class Group(db.Model):
    __tablename__ = 'group'

    id = db.Column(db.Integer, primary_key=True)
    people_id = db.Column(db.Integer, db.ForeignKey('people.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    visibility = db.Column(db.Integer, default=0)


class Chatting(db.Model):
    __tablename__ = 'chatting'

    id = db.Column(db.Integer, primary_key=True)
    from_id = db.Column(db.Integer, db.ForeignKey('people.id'), nullable=False)
    to_id = db.Column(db.Integer, db.ForeignKey('people.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    chat_time = db.Column(db.DateTime, default=datetime.datetime.now)
    has_read = db.Column(db.Boolean, default=False)

    # from_people = db.relationship()
    # to_people = db.relationship()

    def __init__(self, from_id, to_id, content):
        self.from_id = from_id
        self.to_id = to_id
        self.content = content
