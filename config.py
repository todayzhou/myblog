import os
from dotenv import load_dotenv  # 用来便捷的管理环境变量
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
	BASEDIR = basedir
	CSRF_ENABLED = True
	SQLALCHEMY_TRACK_MODIFICATIONS = True
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	MAIL_SERVER = os.environ.get('MAIL_SERVER')
	MAIL_PORT = os.environ.get('MAIL_PORT') or 25
	MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	ADMIN = os.environ.get('ADMIN')

	POSTS_PRE_PAGE = 5
	MESSAGE_PRE_PAGE = 5
	LANGUAGES = ['zh', 'en']  # 指明支持的语言
	MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
	MS_TRANSLATOR_URL = 'https://api.cognitive.microsofttranslator.com/translate'

	REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
