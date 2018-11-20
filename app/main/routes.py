from app import current_app, db
from app.main import bp
from flask import render_template, flash, redirect, url_for, request, g, jsonify
from flask_login import current_user, login_required
from datetime import datetime
from .forms import EditProfileForm, PostForm, SearchForm, MessageForm
from app.models import User, Post, Message, Notification
from guess_language import guess_language
from flask_babel import get_locale, _
from app.translate import translate


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
	form = PostForm()
	if form.validate_on_submit():
		language = guess_language(form.post.data)
		if language == 'UNKNOWN' or len(language) > 5:
			language = ''
		p = Post(body=form.post.data, author=current_user, language=language)
		db.session.add(p)
		db.session.commit()
		flash(_('Your post is now live!'))
		return redirect(url_for('main.index'))
	page = request.args.get('page', 1, type=int)
	posts = current_user.followed_posts().paginate(
		page, current_app.config['POSTS_PRE_PAGE'], False
	)
	next_url = url_for('main.index', page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('main.index', page=posts.prev_num) \
		if posts.has_prev else None
	return render_template('index.html', posts=posts.items, form=form, title=_('Home page.'),
						   next_url=next_url, prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore():
	page = request.args.get('page', 1, type=int)
	posts = Post.query.order_by(Post.timestamp.desc()).paginate(
		page, current_app.config['POSTS_PRE_PAGE'], False
	)
	next_url = url_for('main.explore', page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('main.explore', page=posts.prev_num) \
		if posts.has_prev else None
	return render_template('index.html', posts=posts.items, title=_('Explore'),
						   next_url=next_url, prev_url=prev_url)


@bp.before_request
def before_request():
	if current_user.is_authenticated:
		current_user.last_seen = datetime.utcnow()
		db.session.commit()  # 这里可以直接commit而不用add()，因为只是修改了属性，而且db.session在调用current_user的时候以及打开
		g.search_form = SearchForm()  # 在这里创建表单实例可以更便捷的把表单放到base.html里面
	g.locale = str(get_locale())   # 获取客户端环境下使用的语言


@bp.route('/user/<username>')
@login_required
def user(username):
	u = User.query.filter_by(username=username).first_or_404()  # 如果没有查到这个user，直接返回404页面，不继续后面的处理
	page = request.args.get('page', 1, type=int)
	posts = u.posts.paginate(
		page, current_app.config['POSTS_PRE_PAGE'], False
	)
	next_url = url_for('main.user', username=username, page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('main.user', username=username, page=posts.prev_num) \
		if posts.has_prev else None
	return render_template('user.html', posts=posts.items, user=u,
						   next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
	user = User.query.filter_by(username=username).first_or_404()
	return render_template('user_popup.html', user=user)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
	form = EditProfileForm(current_user.username)
	if form.validate_on_submit():
		current_user.username = form.username.data
		current_user.about_me = form.about_me.data
		db.session.commit()
		flash(_('Your changes have been saved.'))
		return redirect(url_for('main.user', username=current_user.username))
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.about_me.data = current_user.about_me
	return render_template('edit_profile.html', title=_('Edit Profile'), form=form)


@bp.route('/follow/<username>', methods=['GET', 'POST'])
@login_required
def follow(username):
	u = User.query.filter_by(username=username).first_or_404()

	if u is None:
		flash(_('User %(username)s not found.', username=username))  # 需要翻译的文本，所以用的很古老的格式化占位方式
		return redirect(url_for('main.index'))
	elif u == current_user:
		flash(_('You cannot follow yourself!'))   # 需要翻译
		return redirect(url_for('main.user', username=username))
	current_user.follow(u)
	db.session.commit()
	flash(_('You are following %(username)s!', username=username))
	return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>', methods=['GET', 'POST'])
@login_required
def unfollow(username):
	u = User.query.filter_by(username=username).first_or_404()
	if u is None:
		flash(_('User %(username)s not found.', username=username))
		return redirect(url_for('main.index'))
	elif u == current_user:
		flash(_('You cannot unfollow yourself!'))
		return redirect(url_for('main.user', username=username))
	current_user.unfollow(u)
	db.session.commit()
	flash(_('You are not following %(username)s!', username=username))
	return redirect(url_for('main.user', username=username))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
	# 返回json,json也有很多数据结构，比如数据、对象、值、布尔、字符串、数字等,这里返回就是对象
	return jsonify({'text': translate(text=request.form['text'],
					src_lang=request.form['src_lang'],
					dst_lang=request.form['dst_lang'])})


@bp.route('/search', methods=['GET', 'POST'])
@login_required
def search():
	if not g.search_form.validate():
		return redirect(url_for('main.explore'))
	text = g.search_form.q.data
	ids = Post.search(text)
	ids_len = len(ids)
	return render_template('search.html', title=_('Search'), posts=ids, entry=ids_len)


@bp.route('/send_message/<username>', methods=['GET', 'POST'])
@login_required
def send_message(username):
	user = User.query.filter_by(username=username).first_or_404()
	if current_user == user:
		flash(_('you can not send message to yourself.'))
		return redirect(url_for('main.user', username=username))
	form = MessageForm()
	if form.validate_on_submit():
		mess = Message(author=current_user, receiver=user, body=form.message.data)
		user.add_notifications('unread_messages_count', user.new_messages())
		db.session.add(mess)
		db.session.commit()
		flash(_('your message have been send.'))
		return redirect(url_for('main.user', username=username))
	return render_template('send_message.html', title=_('Send message'), form=form, username=username)


@bp.route('/messages')
@login_required
def messages():
	current_user.last_message_read = datetime.utcnow()
	current_user.add_notifications('unread_messages_count', 0)
	db.session.commit()
	page = request.args.get('page', 1, type=int)
	messages = current_user.message_received.order_by(
		Message.timestamp.desc()).paginate(
		page, current_app.config['MESSAGE_PRE_PAGE'], False
	)
	next_url = url_for('main.messages', page=messages.next_num) \
		if messages.has_next else None
	prev_url = url_for('main.messages', page=messages.prev_num) \
		if messages.has_prev else None
	return render_template('messages.html', next_url=next_url, prev_url=prev_url, title=_('Messages'),
						   messages=messages.items)


@bp.route('/notifications')
@login_required
def notifications():
	# since 的作用是当浏览器已经get到未读消息以后，通过since传递就可以避免已经获取的消息再次传递，减小开销.
	# since 在JavaScript中发送过来，每次刷新页面都会重置成0
	since = request.args.get('since', 0.0, type=float)
	notifications = current_user.notifications.filter(Notification.timestamp > since).order_by(
		Notification.timestamp.desc()
	)
	# 返回一个数组json对象
	return jsonify([{
		'name': n.name,
		'data': n.get_data(),
		'timestamp': n.timestamp
	} for n in notifications])
