#!env/bin/python

from app import create_app, db, cli
from app.models import User, Post, Message, Notification, Task

# 使用工厂函数创建app
app = create_app()
# 注册快捷命令
cli.register(app)


# 为flask shell注册上下文, 省去每次进入shell都要重新导入db、User、Post等入口
@app.shell_context_processor
def make_shell_context():
	return {'db': db, 'User': User, 'Post': Post, 'Message': Message,
			'Notification': Notification, 'Task': Task}
