from app import db, current_app
from app.auth import bp
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user
from werkzeug.urls import url_parse
from .forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
from app.auth.email import send_password_reset_email
from flask_babel import _


@bp.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:  # current_user 要么是未登录的匿名，要么是通过login_user传入的用户
		return redirect(url_for('main.index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash(_('Invalid username or password.'))
			return redirect(url_for('auth.login'))
		login_user(user, remember=form.remember_me.data)  # 传入成功登陆的用户
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('main.index')
		return redirect(next_page)
	return render_template('auth/login.html', title='Sign In', form=form)


@bp.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	form = RegistrationForm()
	if form.validate_on_submit():
		u = User(username=form.username.data, email=form.email.data)
		u.set_password(password=form.password.data)
		db.session.add(u)
		db.session.commit()
		flash(_('Congratulations, you are now a registered user!'))
		return redirect(url_for('auth.login'))
	return render_template('auth/register.html', form=form, title='Register')


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	form = ResetPasswordRequestForm()
	user = User.query.filter_by(email=form.email.data).first()
	if form.validate_on_submit():
		send_password_reset_email(user)
		flash(_('has send mail to you.'))
		return redirect(url_for('auth.login'))
	return render_template('auth/reset_password_request.html', form=form, title='Reset Password Requeset')


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	u = User.verify_reset_password_token(token)
	if not u:
		flash(_('Invalid token.'))
		return redirect(url_for('auth.login'))
	form = ResetPasswordForm()
	if form.validate_on_submit():
		u.set_password(form.password.data)
		db.session.commit()
		flash(_('Your password have been reset.Please relogin.'))
		return redirect(url_for('auth.login'))
	return render_template('auth/reset_password.html', form=form, title='Reset Password')