from datetime import datetime, timedelta
import unittest
from app import current_app, db, create_app
from config import Config
from app.models import User, Post


class TestConfig(Config):
	TESTING = True
	SQLALCHEMY_DATABASE_URI = 'sqlite://'


class UserModelCase(unittest.TestCase):
	def setUp(self):
		self.app = create_app(TestConfig)
		# 创建应用上下文，不然db.create_all()无法工作
		self.app_context = self.app.app_context()
		self.app_context.push()
		db.create_all()

	def tearDown(self):
		db.session.remove()
		db.drop_all()
		self.app_context.pop()

	def test_password_hashing(self):
		u = User(username='zhousl')
		u.set_password('123')
		self.assertFalse(u.check_password('234'))
		self.assertTrue(u.check_password('123'))

	def test_avatar(self):
		u = User(username='todayzhou', email='todayzhou@126.com')
		self.assertEqual(u.avatar(120),
						'https://www.gravatar.com/avatar/62e3341ab245b18ee91ce8ae852e8d48?d=identicon&s=120')

	def test_follow(self):
		u1 = User(username='z1')
		u2 = User(username='z2')
		db.session.add_all([u1, u2])
		db.session.commit()

		self.assertEqual(u1.followed.all(), [])
		self.assertEqual(u2.followed.all(), [])

		u1.follow(u2)
		db.session.commit()

		self.assertTrue(u1.is_following(u2))
		self.assertEqual(u1.followed.all(), [u2])
		self.assertEqual(u2.followers.count(), 1)
		self.assertEqual(u2.followers.first().username, 'z1')

		u1.unfollow(u2)
		db.session.commit()

		self.assertFalse(u1.is_following(u2))
		self.assertEqual(u1.followed.count(), 0)
		self.assertEqual(u2.followers.count(), 0)

	def test_follow_posts(self):
		u1 = User(username='z1')
		u2 = User(username='z2')
		u3 = User(username='z3')
		u4 = User(username='z4')
		db.session.add_all([u1, u2, u3, u4])

		now = datetime.utcnow()
		p1 = Post(body='post for z1', author=u1, timestamp=now+timedelta(seconds=1))
		p2 = Post(body='post for z2', author=u2, timestamp=now+timedelta(seconds=3))
		p3 = Post(body='post for z3', author=u3, timestamp=now+timedelta(seconds=2))
		p4 = Post(body='post for z4', author=u4, timestamp=now+timedelta(seconds=6))
		db.session.add_all([p1, p2, p3, p4])
		db.session.commit()

		u1.follow(u2)
		u1.follow(u3)
		u2.follow(u3)
		u3.follow(u4)
		db.session.commit()

		fp1 = u1.followed_posts().all()
		fp2 = u2.followed_posts().all()
		fp3 = u3.followed_posts().all()
		fp4 = u4.followed_posts().all()

		self.assertEqual(fp1, [p2, p3, p1])
		self.assertEqual(fp2, [p2, p3])
		self.assertEqual(fp3, [p4, p3])
		self.assertEqual(fp4, [p4])

	def test_reset_password(self):
		import time
		u = User(username='z1')
		u.set_password('123')
		db.session.add(u)
		db.session.commit()

		token = u.get_reset_token()
		u_verify = User.verify_reset_password_token(token)
		self.assertEqual(u, u_verify)

		token = u.get_reset_token(expires=1)
		time.sleep(2)
		u_verify = User.verify_reset_password_token(token)
		self.assertFalse(u_verify)
