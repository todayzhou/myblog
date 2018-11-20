

def query_index(model, query):
	querys = query.split()
	if not hasattr(model, '__searchable__') or not querys:
		return
	field = model.__searchable__[0]
	query_handler = "model.query"
	for q in querys:
		query_handler += ".filter(model.{}.like('%{}%'))".format(field, q)

	ids = eval(query_handler+'.all()')
	return ids
