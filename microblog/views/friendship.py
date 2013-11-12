# -*- coding: utf-8 -*-
from flask import Module, g, redirect, url_for, flash
from flask.ext.login import login_required
from microblog.forms.friendship import ChatForm
from microblog.models import People, Friendship
from microblog.database import db
from microblog.models.friendship import Chatting
from microblog.tools import render_template


friendship = Module(__name__, url_prefix='/friendship')


@friendship.route('/follow/<int:id>/')
@login_required
def follow(id):
    """关注"""
    if g.user.id == id:
        flash(u'不能关注自己', 'warning')
    else:
        people = People.query.get(id)
        if g.user.is_following(id):
            flash(u'不能重复关注', 'warning')
        elif g.user.is_blocking(id):
            flash(u'不能关注黑名单中的人，请先移出黑名单', 'warning')
        elif people.is_blocking(g.user.id):
            flash(u'对方拒绝了您的关注请求', 'warning')
        else:
            g.user.following.append(people)
            db.session.add(g.user)
            db.session.commit()
            flash(u'关注成功', 'success')
    return redirect(url_for('frontend.index'))


@friendship.route('/unfollow/<int:id>/')
@login_required
def unfollow(id):
    """取消关注"""
    people = People.query.get(id)
    if g.user.is_following(id):
        g.user.following.remove(people)
        db.session.add(g.user)
        db.session.commit()
        flash(u'取消成功', 'success')
    return redirect(url_for('frontend.index'))


@friendship.route('/following/')
@login_required
def show_following():
    """查看我关注的人"""
    following = g.user.following.all()
    return render_template('friendship.html', people=following, active_page='show_following')


@friendship.route('/followed/')
@login_required
def show_followed():
    """查看关注我的人"""
    followed = g.user.followed.all()
    return render_template('friendship.html', people=followed, active_page='show_followed')


@friendship.route('/mutual/')
@login_required
def show_mutual():
    """查看互相关注的人"""
    mutual = g.user.following.all()
    return render_template('friendship.html', people=mutual, active_page='show_mutual')


@friendship.route('/block/<int:id>/')
@login_required
def block(id):
    if g.user.id == id:
        flash(u'不能将自己加入黑名单', 'warning')
    else:
        people = People.query.get(id)
        if g.user.is_blocking(id):
            flash(u'不能重复加入黑名单', 'warning')
        else:
            g.user.blocking.append(people)
            # 取消关注
            if g.user.is_following(id):
                g.user.following.remove(people)
            db.session.add(g.user)
            db.session.commit()
            flash(u'加入黑名单成功', 'success')
    return redirect(url_for('frontend.index'))


@friendship.route('/unblock/<int:id>/')
@login_required
def unblock(id):
    people = People.query.get(id)
    if g.user.is_blocking(id):
        g.user.blocking.remove(people)
        db.session.add(g.user)
        db.session.commit()
        flash(u'取消黑名单成功', 'success')
    return redirect(url_for('frontend.index'))


@friendship.route('/blocking/')
@login_required
def show_blocking():
    """查看黑名单"""
    blockings = g.user.blocking.all()
    return render_template('friendship.html', people=blockings, active_page='show_blocking')


@friendship.route('/chat/<int:id>/', methods=['GET', 'POST'])
@login_required
def send_chatting(id):
    if g.user.id == id:
        flash(u'不能给自己发送私信', 'warning')
        return redirect(url_for('frontend.index'))
    chat_form = ChatForm()
    from_people = g.user
    to_people = People.query.get(id)

    if chat_form.validate_on_submit():
        chatting = Chatting(from_people.id, to_people.id, content=chat_form.content.data)
        db.session.add(chatting)
        db.session.commit()
        flash(u'发送成功', 'success')
        return redirect(url_for('frontend.index'))

    return render_template(
        'chatting-new.html',
        chat_form=chat_form,
        from_people=from_people,
        to_people=to_people
    )


@friendship.route('/chat/inbox/', methods=['GET'])
@login_required
def show_inbox():
    chattings = Chatting.query.filter(
        (Chatting.to_id==g.user.id)
    )
    return render_template('chatting-inbox.html', chattings=chattings)


@friendship.route('/chat/detail/<int:id>/')
@login_required
def show_chatting_detail(id):
    chatting = Chatting.query.get(id)
    return render_template('chatting-detail.html', chatting=chatting)
    pass


@friendship.route('/chat/outbox/', methods=['GET'])
@login_required
def show_outbox():
    chattings = Chatting.query.filter(
        (Chatting.from_id==g.user.id)
    )
    return render_template('chatting-outbox.html', chattings=chattings)


# TODO:
# dynamic, joined