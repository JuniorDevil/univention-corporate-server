#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  session handling
#
# Copyright 2006-2011 Univention GmbH
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

import locale, sys, os, string, ldap

import notifier
import notifier.signals as signals
import notifier.popen as popen

from OpenSSL import *

import univention.uldap

from message import *
from client import *
from version import *
from definitions import *

from univention.management.console.module import Manager as ModuleManager
from univention.management.console.syntax import Manager as SyntaxManager
from univention.management.console.category import Manager as CategoryManager
from univention.management.console.verify import SyntaxVerificationError
from univention.management.console.auth import AuthHandler
from univention.management.console.acl import ConsoleACLs
import univention.management.console as umc

class State( signals.Provider ):
	def __init__( self, client, socket ):
		signals.Provider.__init__( self )
		self.__auth = AuthHandler()
		self.__auth.signal_connect( 'authenticated', self._authenticated )
		self.client = client
		self.socket = socket
		self.processor = None
		self.authenticated = False
		self.buffer = ''
		self.requests = {}
		self.authResponse = None
		self.signal_new( 'authenticated' )
		self.resend_queue = []

	def __del__( self ):
		ud.debug( ud.ADMIN, ud.PROCESS, 'State: dying' )
		del self.processor

	def _authenticated( self, success ):
		self.signal_emit( 'authenticated', success, self )

	def authenticate( self, username, password ):
		self.__auth.authenticate( username, password )

	def credentials( self ):
		return self.__auth.credentials()


class ModuleProcess( Client ):
	COMMAND = '/usr/bin/univention-management-console-module'

	def __init__( self, module, interface, debug = '0', locale = None ):
		socket = '/var/run/univention-management-console/%u-%lu.socket' % \
				 ( os.getpid(), long( time.time() * 1000 ) )
		# determine locale settings
		args = [ ModuleProcess.COMMAND, '-m', module, '-s', socket,
				 '-i', interface, '-d', debug ]
		if locale:
			args.extend( ( '-l', '%s' % locale ) )
			self.__locale = locale
		else:
			self.__locale = None
		Client.__init__( self, unix = socket, ssl = False, auth = False )
		self.signal_connect( 'response', self._response )
		ud.debug( ud.ADMIN, ud.PROCESS, 'running: %s' % args )
		self.__process = popen.RunIt( args, stdout = False )
		self.__process.signal_connect( 'finished', self._died )
		self.__pid = self.__process.start()
		self._connect_retries = 1
		self.signal_new( 'result' )
		self.signal_new( 'finished' )
		self.name = module

	def __del__( self ):
		ud.debug( ud.ADMIN, ud.PROCESS, 'ModuleProcess: dying' )
		self.disconnect()
		self.__process.stop()
		ud.debug( ud.ADMIN, ud.PROCESS, 'ModuleProcess: child stopped' )

	def _died( self, pid, status ):
		ud.debug( ud.ADMIN, ud.PROCESS, 'ModuleProcess: child died' )
		self.signal_emit( 'finished', pid, status, self.name )

	def _response( self, msg ):
		if msg.command == 'SET' and 'commands/permitted' in msg.arguments:
			return

		self.signal_emit( 'result', msg )

	def pid( self ):
		return self.__pid

class Processor( signals.Provider ):
	'''Implements a proxy and command handler. It handles all internal
	UMCP commands and passes the commands for a module to the
	subprocess.'''
	moduleManager = ModuleManager()
	syntaxManager = SyntaxManager()
	categoryManager = CategoryManager()

	def __init__( self, username, password ):
		self.__username = username
		self.__password = password
		# default interface is 'web'
		self.__interface = 'web'
		signals.Provider.__init__( self )

		# # initialize the handler modules
		# self.__manager = umc.ModuleManager()

		# stores the module processes [ modulename ] = <>
		self.__processes = {}
		self.__locale = None
		self.__sessionid = None

		self.__killtimer = {}

		lo = ldap.open( umc.configRegistry[ 'ldap/server/name' ] )

		try:
			userdn = lo.search_s( umc.configRegistry[ 'ldap/base' ], ldap.SCOPE_SUBTREE,
								  '(&(objectClass=person)(uid=%s))' % self.__username )[ 0 ][ 0 ]

			self.lo = univention.uldap.access( host = umc.configRegistry[ 'ldap/server/name' ],
											   base = umc.configRegistry[ 'ldap/base' ], binddn = userdn,
											   bindpw = self.__password, start_tls = 2 )
		except:
			self.lo = None

		# read the ACLs
		self.acls = ConsoleACLs( self.lo, self.__username, umc.configRegistry[ 'ldap/base' ] )
		self.__command_list = Processor.moduleManager.get_command_descriptions( umc.configRegistry[ 'hostname' ], self.acls )

		self.signal_new( 'response' )


	def __del__( self ):
		ud.debug( ud.ADMIN, ud.PROCESS, 'Processor: dying' )
		for process in self.__processes.values():
			del process

	def get_module_name( self, command ):
		return Processor.moduleManager.search_command( self.__comand_list, command )

	def request( self, msg ):
		if msg.command == 'EXIT':
			self.handle_request_exit( msg )
		elif msg.command == 'GET':
			self.handle_request_get( msg )
		elif msg.command == 'SET':
			self.handle_request_set( msg )
		elif msg.command == 'VERSION':
			self.handle_request_version( msg )
		elif msg.command == 'COMMAND':
			self.handle_request_command( msg )
		elif msg.command in ( 'STATUS', 'CANCEL', 'CLOSE' ):
			self.handle_request_unknown( msg )
		else:
			self.handle_request_unknown( msg )

	def _purge_child(self, module_name):
		if module_name in self.__processes:
			ud.debug( ud.ADMIN, ud.INFO, 'session.py: module %s is still running - purging module out of memory' % module_name)
			pid = self.__processes[ module_name ].pid()
			os.kill(pid, 9)
		return False

	def handle_request_exit( self, msg ):
		if len( msg.arguments ) < 1:
			return self.handle_request_unknown( msg )

		module_name = msg.arguments[ 0 ]
		if module_name:
			if module_name in self.__processes:
				self.__processes[ module_name ].request( msg )
				ud.debug( ud.ADMIN, ud.INFO, 'session.py: got EXIT: asked module %s to shutdown gracefully' % module_name)
				# added timer to kill away module after 3000ms
				cb = notifier.Callback( self._purge_child, module_name )
				self.__killtimer[ module_name ] = notifier.timer_add( 3000, cb )
			else:
				ud.debug( ud.ADMIN, ud.INFO, 'session.py: got EXIT: module %s is not running' % module_name )

	def handle_request_version( self, msg ):
		res = Response( msg )
		res.status = 200 # Ok
		res.body[ 'version' ] = VERSION

		self.signal_emit( 'response', res )


	def handle_request_get( self, msg ):
		res = Response( msg )

		if 'modules/list' in msg.arguments:
			modules = {}
			for id, module in self.__command_list.items():
				modules[ id ] = { 'name' : module.name, 'description' : module.description, 'icon' : module.icon, 'categories' : module.categories }
			res.body[ 'modules' ] = modules
			res.body[ 'categories' ] = self.categoryManager.all()
			ud.debug( ud.ADMIN, ud.INFO, 'session.py: modules: %s' % str( self.__command_list ) )
			ud.debug( ud.ADMIN, ud.INFO, 'session.py: categories: %s' % str( res.body[ 'categories' ] ) )
			res.status = 200 # Ok

		elif 'categories/list' in msg.arguments:
			res.body[ 'categories' ] = self.categoryManager.all()
			res.status = 200 # Ok
		elif 'syntax/verification' in msg.arguments:
			syntax_name = msg.options.get( 'syntax' )
			value = msg.options.get( 'value' )
			if not value or not syntax_name:
				res.status = 600 # failed to process command
			else:
				res.status = 200
				try:
					self.syntaxManager.verify( syntax_name, value )
					res.result = True
				except SyntaxVerificationError, e:
					res.result = False
					res.message = str( e )
		elif 'hosts/list' in msg.arguments:
			# only support for localhost
			res.body = { 'hosts': [ '%s' % umc.configRegistry[ 'hostname' ] ] }
			res.status = 200 # Ok

		else:
			res.status = 402 # invalid command arguments

		self.signal_emit( 'response', res )

	def handle_request_set( self, msg ):
		res = Response( msg )
		if len( msg.arguments ) < 2:
			return self.handle_request_unknown( msg )

		if msg.arguments[ 0 ] == 'locale':
			res.status = 200
			self.__locale = msg.arguments[ 1 ]
			try:
				locale.setlocale( locale.LC_MESSAGES,
								  locale.normalize( msg.arguments[ 1 ] ) )
			except locale.Error:
				# specified locale is not available
				res.status = 601
				ud.debug( ud.ADMIN, ud.WARN,
						 'session.py: handle_request_set: setting locale: status=601: specified locale is not available (%s)' % \
						 self.__locale )
			self.signal_emit( 'response', res )

		elif msg.arguments[ 0 ] == 'sessionid':
			res.status = 200
			self.__sessionid = msg.arguments[ 1 ]
			self.signal_emit( 'response', res )

		elif msg.arguments[ 0 ] == 'interface':
			if len( msg.arguments ) == 2 and msg.arguments[ 1 ]:
				self.__interface = msg.arguments[ 1 ]
				res.status = 200
			else:
				# invalid command arguments
				res.status = 402
			self.signal_emit( 'response', res )

		else:
			return self.handle_request_unknown( msg )

	def __is_command_known( self, msg ):
		# only one command?
		command = None
		if len( msg.arguments ) > 0:
			command = msg.arguments[ 0 ]

		module_name = Processor.moduleManager.search_command( self.__command_list, command )
		if not module_name:
			res = Response( msg )
			res.status = 404 # unknown command
			res.message = status_information( 404 )
			self.signal_emit( 'response', res )
			return None

		return module_name

	def handle_request_command( self, msg ):
		module_name = self.__is_command_known( msg )
		if module_name and msg.arguments:
			if not self.acls.is_command_allowed( msg.arguments[ 0 ], options = msg.options ):
				response = Response( msg )
				response.status = 405 # not allowed
				response.message = status_information( 405 )
				self.signal_emit( 'response', response )
				return
			if not module_name in self.__processes:
				ud.debug( ud.ADMIN, ud.INFO, 'creating new module and passing new request to module %s: %s' % (module_name, str(msg._id)) )
				if umc.configRegistry.get( 'umc/module/debug/level' ):
					mod_proc = ModuleProcess( module_name, self.__interface,
								  debug = umc.configRegistry[ 'umc/module/debug/level' ],
								  locale = self.__locale )
				else:
					mod_proc = ModuleProcess( module_name, self.__interface,
											  locale = self.__locale  )
				mod_proc.signal_connect( 'result', self._mod_result )
				cb = notifier.Callback( self._socket_died, module_name, msg )
				mod_proc.signal_connect( 'closed', cb )
				cb = notifier.Callback( self._mod_died, msg )
				mod_proc.signal_connect( 'finished', cb )
				self.__processes[ module_name ] = mod_proc
				cb = notifier.Callback( self._mod_connect, mod_proc, msg )
				notifier.timer_add( 50, cb )
			else:
				ud.debug( ud.ADMIN, ud.INFO, 'passing new request to running module %s' % module_name )
				self.__processes[ module_name ].request( msg )

	def _mod_connect( self, mod, msg ):
		ud.debug( ud.ADMIN, ud.PROCESS, 'trying to connect' )
		if not mod.connect():
			ud.debug( ud.ADMIN, ud.PROCESS, 'failed' )
			if mod._connect_retries > 200:
				ud.debug( ud.ADMIN, ud.ERROR, 'connection to module process failed')
				res = Response( msg )
				res.status = 503 # error connecting to module process
				res.message = status_information( 503 )
				self.signal_emit( 'response', res )
			else:
				mod._connect_retries += 1
				return True
		else:
			ud.debug( ud.ADMIN, ud.INFO, 'ok')

			# send acls
			req = Request( 'SET', args = [ 'commands/permitted' ], opts = { 'acls' : self.acls.json(), 'commands' : self.__command_list[ mod.name ].json() } )
			mod.request( req )

			# set credentials
			req = Request( 'SET', args = [ 'credentials' ], opts = { 'username' : self.__username, 'password' : self.__password } )
			mod.request( req )

			# set locale
			if self.__locale:
				req = Request( 'SET', args = [ 'locale' ], opts = { 'locale' : self.__locale } )
				mod.request( req )

			# set sessionid
			if self.__sessionid:
				req = Request( 'SET', args = [ 'sessionid' ], opts = { 'sessionid' : self.__sessionid } )
				mod.request( req )

			mod.request( msg )

		return False

	def _mod_result( self, msg ):
		self.signal_emit( 'response', msg )

	def _socket_died( self, module_name, msg):
		ud.debug( ud.ADMIN, ud.WARN, 'socket died (module=%s)' % module_name )
		res = Response( msg )
		res.status = 502 # module process died unexpectedly
		self._mod_died(0, 0, module_name, msg)

	def _mod_died( self, pid, status, name, msg ):
		if status:
			ud.debug( ud.ADMIN, ud.WARN, 'module process died (%d): %s' % ( pid, str( status ) ) )
			res = Response( msg )
			res.status = 502 # module process died unexpectedly
		else:
			ud.debug( ud.ADMIN, ud.INFO, 'module process died: everything fine' )
		if name in self.__processes:
			ud.debug( ud.ADMIN, ud.WARN, 'module process died: cleaning up requests')
			self.__processes[ name ].invalidate_all_requests()
		# if killtimer has been set then remove it
		if name in self.__killtimer:
			ud.debug( ud.ADMIN, ud.INFO, 'module process died: stopping killtimer of "%s"' % name )
			notifier.timer_remove( self.__killtimer[ name ] )
			del self.__killtimer[ name ]
		if name in self.__processes:
			del self.__processes[ name ]

	def handle_request_status( self, msg ):

		self.handle_request_unknown( msg )


	def handle_request_cancel( self, msg ):

		self.handle_request_unknown( msg )


	def handle_request_close( self, msg ):

		self.handle_request_unknown( msg )


	def handle_request_unknown( self, msg ):
		res = Response( msg )
		res.status = 404 # unknown command
		res.message = status_information( 404 )

		self.signal_emit( 'response', res )

if __name__ == '__main__':
	processor = Processor( 'Administrator', 'univention' )
	processor.handle_request_get ( None )
