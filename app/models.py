from app import db, login, current_app
from app.search import query_index
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin  # 自动实现必要的is_authenticated、is_active 等必要方法
from hashlib import md5
from time import time
import jwt, json
import rq, redis

'''多对多关联表'''
followers = db.Table('followers',
					 db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
					 db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
					 )


class User(UserMixin, db.Model):
	__searchable__ = ['username']
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.DateTime, default=datetime.utcnow)
	posts = db.relationship('Post', backref='author',
							lazy='dynamic')  # Post指定“多”一侧的类名，提供指向"one"一侧的"many"侧的字段名称，使用 post.author。
	followed = db.relationship(
		'User',
		secondary=followers,  # 指定关联表
		primaryjoin=(followers.c.follower_id == id),  # 左侧（关注着）和关联表的联结条件，followed_id对应followers_id
		secondaryjoin=(followers.c.followed_id == id),  # 右侧（被关注着）和关联表的联结条件，和上面的相反
		backref=db.backref('followers', lazy='dynamic'), lazy='dynamic'  # 定义从右侧查询到左侧
	)
	# 具体指定外键，为了防止Message中的两个外键错乱
	message_sent = db.relationship('Message',
								   foreign_keys='Message.sender_id',
								   backref='author', lazy='dynamic')
	message_received = db.relationship('Message',
									   foreign_keys='Message.receiver_id',
									   backref='receiver', lazy='dynamic')
	last_message_read = db.Column(db.DateTime)  # 用来记录最后一次读消息的时间，用来检查是否有新消息

	notifications = db.relationship('Notification', backref='user', lazy='dynamic')

	tasks = db.relationship('Task', backref='user', lazy='dynamic')

	files = db.relationship('Files', backref='user', lazy='dynamic')

	def __init__(self, *args, **kwargs):
		print('init....')
		if not User.query.filter_by(username='system').first():
			print('create system')
			u = User(username='system', email=current_app.config['ADMIN'])
			db.session.add(u)
		super().__init__(*args, **kwargs)

	def __repr__(self):
		return '<User %s>' % self.username

	'''密码相关'''

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	'''头像相关'''

	def avatar(self, size):
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
			digest, size
		)

	'''用户关注'''

	def follow(self, user):
		if not self.is_following(user):
			self.followed.append(user)

	def unfollow(self, user):
		if self.is_following(user):
			self.followed.remove(user)

	def is_following(self, user):
		return self.followed.filter(
			followers.c.followed_id == user.id).count() > 0

	'''联结查询，获取所有关注对象的文章和自己发表的文章'''

	def followed_posts(self):
		followed = Post.query.join(
			followers, (followers.c.followed_id == Post.user_id)).filter(
			followers.c.follower_id == self.id)
		own = Post.query.filter_by(user_id=self.id)
		return followed.union(own).order_by(Post.timestamp.desc())

	'''重置密码'''

	def get_reset_token(self, expires=600):
		return jwt.encode(
			{'reset_password': self.id, 'exp': time() + expires},
			current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

	@staticmethod
	def verify_reset_password_token(token):
		try:
			id = jwt.decode(token, current_app.config['SECRET_KEY'],
							algorithms=['HS256'])['reset_password']
		except:
			return
		return User.query.get(id)

	'''私信'''

	def new_messages(self):
		last_read_message = self.last_message_read or datetime(1900, 1, 1)
		return Message.query.filter_by(receiver=self).filter(
			Message.timestamp > last_read_message
		).count()

	'''消息通知'''

	def add_notifications(self, name, data):
		self.notifications.filter_by(name=name).delete()
		n = Notification(name=name, user=self, payload_json=json.dumps(data))
		db.session.add(n)  # 在模型里面会有上下文自动commit
		return n

	'''后台任务'''

	def launch_task(self, name, description, *args, **kwargs):
		job = current_app.task_queue.enqueue('app.tasks.' + name, self.id, *args, **kwargs)
		t = Task(id=job.get_id(), name=name, description=description, user=self)
		db.session.add(t)
		return t

	def get_tasks_in_progress(self):
		return self.tasks.filter_by(complete=False).all()

	def get_task_in_progress(self, name):
		return self.tasks.filter_by(name=name, complete=False).first()


# 用于搜索的混合类
class SearchableMixin(object):
	@classmethod
	def search(cls, text):
		ids = query_index(cls, text)
		return ids

	# 使用其他全文搜索引擎的时候需要用，根据db.event来事件来触发
	@classmethod
	def before_commit(cls, session):
		pass

	@classmethod
	def after_commit(cls, session):
		pass


# db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
# db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class Post(SearchableMixin, db.Model):
	__searchable__ = ['body']
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey(
		'user.id'))  # 这里的user是数据库表的名称，会自动转换成对应的数据库模型类,使用flask db migrate迁移数据库的时候会自动将数据库的模型小写当做表名
	language = db.Column(db.String(5))

	def __repr__(self):
		return '<Post %s>' % self.id


# 私信消息
class Message(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	body = db.Column(db.String(140))

	def __repr__(self):
		return '<Message %s>' % self.id


# 通知，notification 在发送私信或者查看消息页面的时候更新,可以包含多种消息，比如来信、系统通知等等
class Notification(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), index=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	timestamp = db.Column(db.Float, index=True, default=time)
	payload_json = db.Column(db.Text)

	def get_data(self):
		return json.loads(str(self.payload_json))


# 后台任务
class Task(db.Model):
	id = db.Column(db.String(36), primary_key=True)  # 存储任务id
	name = db.Column(db.String(140), index=True)
	description = db.Column(db.String(140))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	complete = db.Column(db.Boolean, default=False)

	def get_rq_job(self):
		try:
			job = rq.job.Job.fetch(self.id, connection=current_app.redis)
		except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
			return None
		return job

	def get_progress(self):
		job = self.get_rq_job()
		return job.meta.get('progress', '0%') if job is not None else 100


# 上传的文件
class Files(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(36), index=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	path = db.Column(db.String(50), index=True)

	@classmethod
	def allowed_file(cls, filename):
		return '.' in filename and \
			filename.rsplit('.', 1)[1] in current_app.config['ALLOWED_EXTENSIONS']


# '''user_loader回调,被Flask-Login使用获取用户id,在执行current_user的时候会加载，此时db.session已经产生'''
@login.user_loader
def load_user(id):
	return User.query.get(int(id))
