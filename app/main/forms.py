from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Length
from app.models import User
from flask_babel import lazy_gettext as _l   # 对于请求之外在初始化应用的时候存在的字符串，使用懒惰的方式加载
from flask import request


class EditProfileForm(FlaskForm):
	username = StringField(_l('username'), validators=[DataRequired()])
	about_me = TextAreaField(_l('about me'), validators=[Length(min=0, max=140)])
	submit = SubmitField(_l('submit'))

	def __init__(self, original_username, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.original_username = original_username

	def validate_username(self, username):
		if username.data != self.original_username:
			u = User.query.filter_by(username=username.data).first()
			if u is not None:
				raise ValidationError(_l('Please use a different username.'))


class PostForm(FlaskForm):
	post = TextAreaField(_l('say something:'), validators=[DataRequired(), Length(min=1, max=150)])
	submit = SubmitField(_l('submit'))


class SearchForm(FlaskForm):
	q = StringField(_l('search'), validators=[DataRequired()])

	# 由于searchform使用的是get方式的提交数据，flask从request.form获取不到表单数据，所以需要自行传入request.args，以获取q的内容
	def __init__(self, *args, **kwargs):
		if 'formdata' not in kwargs:
			kwargs['formdata'] = request.args
		if 'csrf_enabled' not in kwargs:
			kwargs['csrf_enabled'] = False
		super().__init__(*args, **kwargs)


class MessageForm(FlaskForm):
	message = TextAreaField(_l('message'), validators=[DataRequired(), Length(min=1, max=140)])
	submit = SubmitField('submit')

