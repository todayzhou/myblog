from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo
from app.models import User
from flask_babel import lazy_gettext as _l   # 对于请求之外在初始化应用的时候存在的字符串，使用懒惰的方式加载


class LoginForm(FlaskForm):
	username = StringField(_l('username'), validators=[DataRequired()])
	password = PasswordField(_l('password'), validators=[DataRequired()])
	remember_me = BooleanField(_l('remember_me'), default=False)
	submit = SubmitField(_l('Sign In'))


class RegistrationForm(FlaskForm):
	username = StringField(_l('username'), validators=[DataRequired()])
	email = StringField(_l('email'), validators=[DataRequired(), Email()])
	password = PasswordField(_l('password'), validators=[DataRequired()])
	password2 = PasswordField(_l('repeat password'), validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField(_l('register'))

	# '''以 validate_<filed_name> 命名的方法会自动当成这个字段的补充验证'''
	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user is not None:
			raise ValidationError(_l('Please use a different username.'))

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is not None:
			raise ValidationError(_l('Please use a different email address.'))


class ResetPasswordRequestForm(FlaskForm):
	email = StringField(_l('email'), validators=[DataRequired(), Email()])
	submit = SubmitField(_l('submit'))

	def validate_email(self, email):
		u = User.query.filter_by(email=email.data).first()
		if not u:
			raise ValidationError(_l('Please use a true email.'))


class ResetPasswordForm(FlaskForm):
	password = PasswordField(_l('password'), validators=[DataRequired()])
	password2 = PasswordField(
		_l('repeat password'), validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField(_l('submit'))