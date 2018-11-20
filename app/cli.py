import os, click


def register(app):
	file_dir = app.config['BASEDIR']
	# 创建一个命令组
	@app.cli.group()
	def translate():
		"""Translation and localization commands."""
		pass
	
	
	# 创建子命令
	@translate.command()
	def update():
		"""Update all languages."""
		if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
			raise RuntimeError('extract command failed')
		if os.system('pybabel update -i {} -d app/translations'.format(os.path.join(file_dir, 'messages.pot'))):
			raise RuntimeError('update command failed')
		os.remove('messages.pot')
	
	
	@translate.command()
	def compile():
		"""Compile all languages."""
		if os.system('pybabel compile -d app/translations'):
			raise RuntimeError('compile command failed')
	
	
	@translate.command()
	@click.argument('lang')
	def init(lang):
		"""Initialize a new language."""
		if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
			raise RuntimeError('extract command failed')
		if os.system('pybabel init -i messages.pot -d app/translations -l ' + lang):
			raise RuntimeError('init command failed')
		os.remove('messages.pot')