from flask import Flask, request, current_app  # current_app 虽然没有被显示调用，但是必须导入
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
import os
from flask_login import LoginManager
from config import basedir, Config
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel
from flask_babel import lazy_gettext as _l
from redis import Redis
import rq

'''数据库相关'''
db = SQLAlchemy()
migrate = Migrate()

'''登录系统相关'''
login = LoginManager()
login.login_view = 'auth.login'  # 告诉flask-login 登陆视图函数是什么，用于@login_required 装饰器保护
login.login_message = _l('Please log in to access this page.')

'''邮件'''
mail = Mail()

'''CSS框架bootstrap'''
bootstrap = Bootstrap()

'''日期显示'''
moment = Moment()

'''多语言'''
babel = Babel()


# 根据http请求选择最佳语言
@babel.localeselector
def get_locale():
	# return 'zh'
	return request.accept_languages.best_match(current_app.config['LANGUAGES'])


# 工厂函数中创建app
def create_app(config_class=Config):
	app = Flask(__name__)
	app.config.from_object(config_class)
	from app import models

	db.init_app(app)
	migrate.init_app(app, db)
	login.init_app(app)
	mail.init_app(app)
	bootstrap.init_app(app)
	moment.init_app(app)
	babel.init_app(app)

	# 后台任务
	app.redis = Redis.from_url(app.config['REDIS_URL'])
	app.task_queue = rq.Queue('myblog-tasks', connection=app.redis)

	# 蓝图注册到app上
	from app.errors import bp as errors_bp
	from app.auth import bp as auth_bp
	from app.main import bp as main_bp
	from app.api import bp as api_bp
	app.register_blueprint(errors_bp)
	app.register_blueprint(auth_bp, url_prefix='/auth')  # url_prefix 前缀使得所有和认证相关的url前面都会加上auth目录，路由分离、直观
	app.register_blueprint(main_bp)
	app.register_blueprint(api_bp, url_prefix='/api')

	# '''不开启调试模式情况下，error信息自动通过邮件发送回来'''
	if not app.debug and 0:
		if app.config['MAIL_SERVER']:
			auth = None
			if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
				auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
			secure = None
			if app.config['MAIL_USE_TLS']:
				secure = ()
			mail_handler = SMTPHandler(
				mailhost=(app.config['MAIL_SERVER'], int(app.config['MAIL_PORT'])),
				fromaddr='no-reply@' + app.config['MAIL_SERVER'],
				toaddrs=app.config['ADMINS'],
				subject='Microblog Failure',
				credentials=auth,
				secure=secure
			)
			mail_handler.setLevel(logging.ERROR)
			app.logger.addHandler(mail_handler)
			# app中尝试的错误信息都将会通过这个email处理器发送，在程序中需要记录的错误都添加到app.logger中，比如 app.logger.error('....', exc_info=)
	
	# '''记录日志到文件'''
	if not app.debug and 0:
		if not os.path.exists('logs'):
			os.mkdir('logs')
		file_hander = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)
		file_hander.setFormatter(logging.Formatter(
			'%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
		))
		file_hander.setLevel(logging.INFO)
		app.logger.addHandler(file_hander)
	
		app.logger.setLevel(logging.INFO)
		app.logger.info('microblog setup')

	return app
	