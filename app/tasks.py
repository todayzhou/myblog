from app import create_app, db
from flask import render_template
from app.auth import email
from app.models import Task, User, Post
import time, sys, json
from rq import get_current_job

# 因为后台任务需要一个单独的进程来执行，所以需要额外起一个app来供使用,比如获取数据库、发送邮件等
app = create_app()
app.app_context().push()  # 把app的上下文推进来,之所以flask run运行的时候不需要这一步，是因为run的时候自动实现了推送上下文


def _set_task_progress(progress):
	job = get_current_job()
	if job:
		job.meta['progress'] = '%.f%%' % progress
		job.save_meta()
		task = Task.query.get(job.get_id())  # primary_key 是可以直接通过get的方式来获取的
		task.user.add_notifications('task_progress', {'task_id': job.get_id(),
													'progress': '%.f%%' % progress})

		if progress >= 100:
			task.complete = True
		db.session.commit()


# 导出用户的post任务
def export_posts(user_id):
	# web应用中的错误和异常会有app.logger来收集，但是对于后台任务是一个单独的进程，所以需要手动来收集错误信息，否则只能通过worker的控制台才能看到错误
	try:
		_set_task_progress(0)
		user = User.query.get(user_id)
		total_post = user.posts.count()
		data = []
		i = 0
		for post in user.posts.order_by(Post.timestamp.desc()).all():
			data.append({'body': post.body,
						 'timestamp': post.timestamp.isoformat() + 'Z'})  # 把datetime格式的时间转换成字符串，最后加上时区
			i += 1
			time.sleep(3)
			_set_task_progress(100*i/total_post)

		email.send_email(subject='[myblog] your posts',
						 sender=app.config['ADMIN'],
						 receiver=[user.email],
						 text_body=render_template('auth/email/export_posts.txt', user=user),
						 html_body=render_template('auth/email/export_posts.html', user=user),
						 attachments=[('posts.txt', 'text/plain',
									   json.dumps({'posts': data}, ensure_ascii=False, indent=4).encode('utf-8'))],
						 # indent=4是为了更好看的输出, encode编码是为了保证附件的中文不被转换成16进制
						 sync=True)  # 这里已经是后台任务，所以选择成同步模式发送邮件，否则会有问题
	except:
		_set_task_progress(100)
		app.logger.error('Unhandled exception', exc_info=sys.exc_info())  # sys.exc_info()方法包含了错误的traceback信息


def example(s):
	job = get_current_job()
	print('start the task.')
	for i in range(s):
		# 回传执行进度, meta是一个字典，可以自定义键值
		job.meta['progress'] = 100 * i/s
		job.save_meta()
		print(i)
		time.sleep(1)
	job.meta['progress'] = 100
	job.save_meta()
	print('end of tasks.')


def example1(s):
	print(s)