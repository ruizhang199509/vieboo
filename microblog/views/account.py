# -*- coding: utf-8 -*-
import datetime
from flask import Module, g, request, url_for, redirect, flash, current_app, session
from flask.ext.login import login_user, login_required, logout_user
from flask.ext.principal import identity_changed, Identity, AnonymousIdentity
from microblog.extensions import db, photos
from microblog.models import People, LoginLog
from microblog.forms import LoginForm, RegisterForm, ChangePasswordForm, ModifyProfileForm, AvatarForm
from microblog.helpers import render_template

account = Module(__name__, url_prefix='/account')


# 用户注册
@account.route('/register/', methods=['GET', 'POST'])
def register():
    # 已登录用户则返回首页
    if g.user.is_authenticated():
        return redirect(url_for('frontend.index'))

    register_form = RegisterForm()
    if register_form.validate_on_submit():
        ip = get_client_ip(request)
        people = People(
            email=register_form.email.data,
            password=register_form.password.data,
            nickname=register_form.nickname.data,
            mobile=register_form.mobile.data,
            reg_time=datetime.datetime.utcnow(),
            reg_ip=ip,
        )
        # 将用户写入数据库
        db.session.add(people)
        db.session.commit()
        db.session.close()
        flash(u'注册成功', 'success')
        return redirect(url_for('frontend.index'))
    return render_template('register.html', register_form=register_form)


def get_client_ip(request):
    # 获取 ip 地址
    if 'x-forwarded-for' in request.headers:
        ip = request.headers['x-forwarded-for'].split(', ')[0]
    else:
        ip = request.remote_addr
    return ip


@account.route('/login/', methods=['GET', 'POST'])
def login():
    # 已登录用户则返回首页
    if g.user.is_authenticated():
        return redirect(url_for('frontend.index'))

    login_form = LoginForm()
    if login_form.validate_on_submit():
        people = People.query.authenticate(
            login_form.login.data,
            login_form.password.data,
        )

        if people:
            login_user(people, remember=login_form.remember.data)
            # Flask-Principal 发送信号
            identity_changed.send(current_app._get_current_object(), identity=Identity(people.id))
            print 'sent by login'
            ip = get_client_ip(request)
            login_log = LoginLog(people.id, ip)
            db.session.add(login_log)
            db.session.commit()

            flash(u'登录成功', 'success')
            return redirect(url_for('frontend.index'))
        else:
            flash(u'登录失败', 'warning')

    return render_template('login.html', form=login_form)


# 注销
@account.route('/logout/')
@login_required
def logout():
    logout_user()
    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)
    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    print 'sent by logout'
    flash(u'已注销', 'success')
    return redirect(url_for('frontend.index'))


# 修改密码
@account.route('/password/', methods=['GET', 'POST'])
@login_required
def password():
    change_password_form = ChangePasswordForm()
    if change_password_form.validate_on_submit():
        people = People.query.authenticate(
            g.user.get_email(),
            change_password_form.password_old.data,
        )
        if people:
            people.change_password(change_password_form.password_new.data)
            db.session.add(people)
            db.session.commit()
            db.session.close()
            flash(u'密码修改成功', 'success')
            return redirect(url_for('account.password'))
        else:
            flash(u'原密码不正确', 'warning')
    return render_template('password.html', form=change_password_form, title=u'修改密码')


# 显示与修改个人资料
@account.route('/profile/', methods=['GET', 'POST'])
@login_required
def profile():
    people = g.user
    profile_form = ModifyProfileForm(obj=people)
    if profile_form.validate_on_submit():
        #new_password = profile_form.password.data
        new_nickname = profile_form.nickname.data
        new_mobile = profile_form.mobile.data
        #if new_password:
        #    people.change_password(new_password)
        if new_nickname:
            people.change_nickname(new_nickname)
        if new_mobile:
            people.change_mobile(new_mobile)
        db.session.add(people)
        db.session.commit()
        db.session.close()
        flash(u'个人资料修改成功', 'success')
        return redirect(url_for('account.profile'))
    return render_template('profile.html', form=profile_form, title=u'修改资料')


@account.route('/avatar/', methods=['GET', 'POST'])
@login_required
def avatar():
    avatar_form = AvatarForm()
    people = g.user
    avatar_filename = people.get_avatar()
    if avatar_form.validate_on_submit():
        if avatar_form.avatar.data:
            # 上传头像
            avatar_data = request.files[avatar_form.avatar.name]
            avatar_filename = photos.save(avatar_data)
            print avatar_filename
            url = photos.url(avatar_filename)
            print url
            people.change_avatar(avatar_filename)
            db.session.add(people)
            db.session.commit()
            flash(u'上传成功', 'success')
            return redirect(url_for('account.avatar'))
    return render_template('avatar.html', avatar_form=avatar_form, title=u'修改头像')

