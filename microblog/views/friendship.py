# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flask import Blueprint, g, redirect, url_for, flash, abort, current_app, render_template
from flask.ext.login import login_required
from sqlalchemy import and_
from microblog.forms import ChatForm, AddGroupForm, RenameGroupForm
from microblog.models import People, Friendship, Chatting, Group, Blackship, Notification
from microblog.extensions import db


friendship = Blueprint('friendship', __name__, url_prefix='/friendship')


@friendship.route('/follow/<int:id>/')
@login_required
def follow(id):
    """关注"""
    if g.user.id == id:
        flash('不能关注自己', 'warning')
    else:
        people = People.query.get_or_404(id)
        if g.user.is_following(id):
            flash('不能重复关注', 'warning')
        elif g.user.is_blocking(id):
            flash('不能关注黑名单中的人，请先移出黑名单', 'warning')
        elif people.is_blocking(g.user.id):
            flash('对方拒绝了您的关注请求', 'warning')
        else:
            g.user.following.append(people)
            db.session.add(g.user)
            notification = Notification(from_id=g.user.id, to_id=id, object_table='friendship')
            db.session.add(notification)
            db.session.commit()
            flash('关注成功', 'success')
    return redirect(url_for('frontend.index'))


@friendship.route('/unfollow/<int:id>/')
@login_required
def unfollow(id):
    """取消关注"""
    people = People.query.get_or_404(id)
    if g.user.is_following(id):
        g.user.following.remove(people)
        db.session.add(g.user)
        db.session.commit()
        flash('取消成功', 'success')
    return redirect(url_for('frontend.index'))


@friendship.route('/following/', defaults={'page': 1})
@friendship.route('/following/page/<int:page>/')
@friendship.route('/following/group/<int:gid>/', defaults={'page': 1})
@friendship.route('/following/group/<int:gid>/page/<int:page>/')
@login_required
def show_following(page, gid=None):
    """查看我关注的人"""
    if not gid:
        pagination = g.user.following.order_by(Friendship.c.follow_time).paginate(page, per_page=current_app.config['PER_PAGE'])
        following = pagination.items
        rename_group_form = None
    else:
        pagination = g.user.following.filter(Friendship.c.group_id==gid).order_by(Friendship.c.follow_time).paginate(page, per_page=current_app.config['PER_PAGE'])
        following = pagination.items
        group = Group.query.get_or_404(gid)
        rename_group_form = RenameGroupForm(obj=group)

    add_group_form = AddGroupForm()
    return render_template('friendship.html',
                           people=following,
                           pagination=pagination,
                           active_page='show_following',
                           active_gid=gid,
                           add_group_form=add_group_form,
                           rename_group_form=rename_group_form,
                           title='我关注的')


@friendship.route('/followed/', defaults={'page': 1})
@friendship.route('/followed/page/<int:page>/')
@login_required
def show_followed(page):
    """查看关注我的人"""
    pagination = g.user.followed.order_by(Friendship.c.follow_time).paginate(page, per_page=current_app.config['PER_PAGE'])
    followed = pagination.items
    return render_template('friendship.html',
                           people=followed,
                           pagination=pagination,
                           active_page='show_followed',
                           title='关注我的')


@friendship.route('/mutual/', defaults={'page': 1})
@friendship.route('/mutual/page/<int:page>/')
@login_required
def show_mutual(page):
    """查看互相关注的人"""
    pagination = g.user.get_mutual().order_by(Friendship.c.follow_time).paginate(page, per_page=current_app.config['PER_PAGE'])
    # pagination = g.user.followed.filter(Friendship.c.to_id==g.user.id).\
    #     order_by(Friendship.c.follow_time).paginate(page, per_page=10)
    mutual = pagination.items
    return render_template('friendship.html',
                           people=mutual,
                           pagination=pagination,
                           active_page='show_mutual',
                           title='互相关注')


@friendship.route('/block/<int:id>/')
@login_required
def block(id):
    if g.user.id == id:
        flash('不能将自己加入黑名单', 'warning')
    else:
        people = People.query.get_or_404(id)
        if g.user.is_blocking(id):
            flash('不能重复加入黑名单', 'warning')
        else:
            g.user.blocking.append(people)
            # 取消关注
            if g.user.is_following(id):
                g.user.following.remove(people)
            if people.is_following(g.user.id):
                g.user.followed.remove(people)
            db.session.add(g.user)
            db.session.commit()
            flash('加入黑名单成功', 'success')
    return redirect(url_for('frontend.index'))


@friendship.route('/unblock/<int:id>/')
@login_required
def unblock(id):
    people = People.query.get_or_404(id)
    if g.user.is_blocking(id):
        g.user.blocking.remove(people)
        db.session.add(g.user)
        db.session.commit()
        flash('取消黑名单成功', 'success')
    return redirect(url_for('frontend.index'))


@friendship.route('/blocking/', defaults={'page': 1})
@friendship.route('/blocking/page/<int:page>/')
@login_required
def show_blocking(page):
    """查看黑名单"""
    pagination = g.user.blocking.order_by(Blackship.c.block_time.desc()).paginate(page, per_page=current_app.config['PER_PAGE'])
    blocking = pagination.items
    return render_template('friendship.html',
                           people=blocking,
                           pagination=pagination,
                           active_page='show_blocking',
                           title='黑名单')


@friendship.route('/chat/<int:id>/', methods=['GET', 'POST'])
@login_required
def send_chatting(id):
    if g.user.id == id:
        flash('不能给自己发送私信', 'warning')
        return redirect(url_for('frontend.index'))
    chat_form = ChatForm()
    from_people = g.user
    to_people = People.query.get_or_404(id)

    if chat_form.validate_on_submit():
        chatting = Chatting(from_people.id, to_people.id, content=chat_form.content.data)
        db.session.add(chatting)
        db.session.commit()
        notification = Notification(from_id=g.user.id, to_id=id, object_table='chatting', object_id=chatting.id)
        db.session.add(notification)
        db.session.commit()
        flash('发送成功', 'success')
        return redirect(url_for('frontend.index'))

    return render_template(
        'chatting-new.html',
        chat_form=chat_form,
        from_people=from_people,
        to_people=to_people
    )


@friendship.route('/chat/inbox/', defaults={'page': 1})
@friendship.route('/chat/inbox/page/<int:page>/')
@friendship.route('/chat/inbox/<flag>/', defaults={'page': 1})
@friendship.route('/chat/inbox/<flag>/page/<int:page>/')
@login_required
def show_inbox(page, flag=None):
    if flag in ('hasread', 'unread'):
        has_read = False if flag == 'unread' else True
        pagination = Chatting.query.filter_by(to_id=g.user.id, has_read=has_read).order_by(Chatting.chat_time.desc()).paginate(page, per_page=current_app.config['PER_PAGE'])
    elif not flag:
        pagination = Chatting.query.filter_by(to_id=g.user.id).order_by(Chatting.chat_time.desc()).paginate(page, per_page=current_app.config['PER_PAGE'])
    else:
        abort(404)
    chattings = pagination.items

    return render_template('chatting-box.html',
                           box='inbox',
                           flag=flag,
                           chattings=chattings,
                           pagination=pagination)


@friendship.route('/chat/detail/<box>/<int:id>/')
@login_required
def show_chatting_detail(box, id):
    if box not in ('inbox', 'outbox'):
        abort(404)
    chatting = Chatting.query.get_or_404(id)
    if box == 'inbox' and chatting.to_id == g.user.id:
        chatting.has_read = True
        db.session.add(chatting)
        db.session.commit()
        # 标记为已读
    return render_template('chatting-detail.html', chatting=chatting)


@friendship.route('/chat/outbox/', defaults={'page': 1})
@friendship.route('/chat/outbox/page/<int:page>/')
@login_required
def show_outbox(page):
    pagination = Chatting.query.filter_by(from_id=g.user.id).order_by(Chatting.chat_time.desc()).paginate(page, per_page=current_app.config['PER_PAGE'])
    chattings = pagination.items
    return render_template('chatting-box.html',
                           box='outbox',
                           chattings=chattings,
                           pagination=pagination)


@friendship.route('/following/group/add/', methods=['GET', 'POST'])
@login_required
def add_group():
    group_form = AddGroupForm()
    if group_form.validate_on_submit():
        group = Group(name=group_form.name.data, people_id=g.user.id)
        db.session.add(group)
        db.session.commit()
        flash('新建成功', 'success')
        return redirect(url_for('friendship.show_following'))
    return render_template('group.html', form=group_form)


@friendship.route('/following/group/delete/<int:id>/')
@login_required
def delete_group(id):
    group = Group.query.get_or_404(id)
    if group in g.user.groups:
        db.session.delete(group)
        db.session.commit()
        flash('删除成功', 'success')
    return redirect(url_for('friendship.show_following'))


@friendship.route('/following/group/rename/<int:id>/', methods=['GET', 'POST'])
@login_required
def rename_group(id):
    group = Group.query.get_or_404(id)
    group_form = RenameGroupForm()
    if group.people_id == g.user.id:
        if group_form.validate_on_submit():
            group.name = group_form.name.data
            db.session.add(group)
            db.session.commit()
            flash('重命名成功', 'success')
            return redirect(url_for('friendship.show_following', gid=id))
    else:
        flash('权限不足', 'warning')
    return render_template('group.html', form=group_form)


@friendship.route('/move/<int:pid>/group/default/')
@friendship.route('/move/<int:pid>/group/<int:gid>/')
@login_required
def move_to_group(pid, gid=None):
    #people = People.query.get(pid)
    #People.following.any(pid)
    if g.user.is_following(pid):
        if not gid or g.user.has_group(gid):
            db.session.execute(
                Friendship.update().
                where(and_(Friendship.c.from_id == g.user.id, Friendship.c.to_id == pid)).
                values(group_id=gid))
            db.session.commit()
        else:
            flash('分组不存在', 'info')
    else:
        flash('没有关注此好友', 'info')
    return redirect(url_for('friendship.show_following', gid=gid))
