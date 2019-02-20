#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2019 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

from socket import gethostname
from datetime import datetime
import logging
import json

from univention.config_registry import ConfigRegistry

ucr = ConfigRegistry()
ucr.load()

LOG_FILE = '/var/log/univention/admindiary.log'

def get_events_to_reject():
	ucrv = 'admin/diary/reject'
	blocked_events = ucr.get(ucrv)
	if blocked_events:
		return blocked_events.split()
	return []

class _ShortNameFormatter(logging.Formatter):
	shorten = 'univention.admindiary'

	def format(self, record):
		record.short_name = record.name
		if record.short_name.startswith('%s.' % self.shorten):
			record.short_name = record.short_name[len(self.shorten) + 1:]
		return super(_ShortNameFormatter, self).format(record)


def _setup_logger():
	base_logger = logging.getLogger('univention.admindiary')
	if not _setup_logger._setup:
		log_format = '%(process)6d %(short_name)-12s %(asctime)s [%(levelname)8s]: %(message)s'
		log_format_time = '%y-%m-%d %H:%M:%S'
		formatter = _ShortNameFormatter(log_format, log_format_time)
		handler = logging.FileHandler(LOG_FILE)
		handler.setFormatter(formatter)
		base_logger.addHandler(handler)
		base_logger.setLevel(logging.WARNING)
		_setup_logger._setup = True
	return base_logger
_setup_logger._setup = False


def get_logger(name):
	base_logger = _setup_logger()
	logger = base_logger.getChild(name)
	log_level = ucr.get('admin/diary/logging/%s' % name)
	if log_level:
		log_level = logging.getLevelName(log_level)
		if isinstance(log_level, int):
			logger.setLevel(log_level)
		else:
			logger.warn('Cannot use log level %s. Call ucr set admin/diary/logging/%s=DEBUG (for example)' % (log_level, name))
	return logger


class DiaryEntry(object):
	def __init__(self, username, message, args, tags, context_id, event_name):
		self.username = username
		self.hostname = gethostname()
		self.message = message
		self.args = args
		self.timestamp = datetime.now()
		self.tags = tags
		self.context_id = context_id
		self.event_name = event_name

	def assert_types(self):
		if not isinstance(self.username, basestring):
			raise TypeError('Username has to be "string"')
		if not isinstance(self.hostname, basestring):
			raise TypeError('Hostname has to be "string"')
		if not isinstance(self.args, dict) or not all(isinstance(key, basestring) and isinstance(value, basestring) for key, value in self.args.iteritems()):
			raise TypeError('Args have to be "dict of string/string"')
		if self.message is not None:
			if not isinstance(self.message, dict) or not all(isinstance(key, basestring) and isinstance(value, basestring) for key, value in self.message.iteritems()):
				raise TypeError('Message has to be "dict of string/string"')
			for locale, message in self.message.iteritems():
				try:
					message.format(**self.args)
				except:
					raise TypeError('Message (%s, %r) has wrong format for given args (%r).', locale, message, self.args)
		if not isinstance(self.timestamp, datetime):
			raise TypeError('timestamp has to be "datetime"')
		if not isinstance(self.tags, list) or not all(isinstance(tag, basestring) for tag in self.tags):
			raise TypeError('Tags have to be "list of string"')
		if not isinstance(self.context_id, basestring):
			raise TypeError('Diary ID has to be "string"')
		if not isinstance(self.event_name, basestring):
			raise TypeError('Event name has to be "string"')

	def to_json(self):
		attrs = {
			'username': self.username,
			'hostname': self.hostname,
			'message': self.message,
			'args': self.args,
			'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S%z'),
			'tags': self.tags,
			'context_id': self.context_id,
			'event': self.event_name,
			'type': 'Entry v1',
			}
		return json.dumps(attrs)

	@classmethod
	def from_json(cls, body):
		json_body = json.loads(body)
		entry = cls(json_body['username'], json_body['message'], json_body['args'], json_body['tags'], json_body['context_id'], json_body['event'])
		entry.timestamp = datetime.strptime(json_body['timestamp'], '%Y-%m-%d %H:%M:%S')
		entry.hostname = json_body['hostname']
		entry.assert_types()
		return entry
