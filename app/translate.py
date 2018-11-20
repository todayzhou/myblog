import json
from app import current_app
from flask_babel import _
import requests


def translate(text, src_lang, dst_lang):
	text = "[{'Text': '%s'}]" % text
	if not current_app.config['MS_TRANSLATOR_KEY'] or not current_app.config['MS_TRANSLATOR_URL']:
		return _('Error: the translation service is not configured.')
	auth = {'Ocp-Apim-Subscription-Key': current_app.config['MS_TRANSLATOR_KEY'],
			'Content-Type': 'application/json'}
	params = {'api-version': 3.0, 'from': src_lang, 'to': dst_lang}
	r = requests.post(url=current_app.config['MS_TRANSLATOR_URL'], params=params, headers=auth,
					data=text)
	if r.status_code != 200:
		return _('Error: the translation service failed.')
	return json.loads(r.content.decode('utf-8'))[0]['translations'][0]['text']

