from app import mail, current_app
from flask_mail import Message
from flask import render_template
import threading


def send_async_mail(app, msg):
	with app.app_context():
		mail.send(msg)


def send_email(subject, sender, receiver, text_body, html_body, attachments=None, sync=False):
	msg = Message(subject, sender=sender, recipients=receiver)
	msg.body = text_body
	msg.html = html_body
	if attachments:
		for attachment in attachments:
			msg.attach(*attachment)
	if sync:
		mail.send(msg)
	else:
		threading.Thread(target=send_async_mail, args=(current_app._get_current_object(), msg)).start()


def send_password_reset_email(user):
	token = user.get_reset_token()
	send_email(
		subject='[Myblog] Reset Password.',
		sender=current_app.config['ADMIN'],
		receiver=[user.email],
		text_body=render_template('auth/email/reset_password.txt', token=token, user=user),
		html_body=render_template('auth/email/reset_password.html', token=token, user=user)
	)