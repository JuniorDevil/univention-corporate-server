# -*- coding: utf-8 -*-
#
# Univention Management Console
#  web interface: control part
#
# Copyright (C) 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import locale, os, sys, time, string

import unimodule

#import univention.admin.uldap
#import univention.admin.modules

import univention.management.console.protocol as umcp
import univention.management.console.tools as umc_tools
import univention.management.console as umc

from uniparts import *

# UMCP client comm
import client
# main widget for UMC (based on notebook)
import widget

import univention_baseconfig

baseConfig = univention_baseconfig.baseConfig()
baseConfig.load()

LANG_DE = 'de_DE.utf8'
#LANG_EN = 'en_EN.utf8'
LANG_EN = 'C'
#LANG_DEFAULT = baseConfig.get ('directory/manager/web/language', locale.getdefaultlocale ())
LANG_DEFAULT = baseConfig.get ('umc/web/language', LANG_EN)

_ = umc.Translation( 'univention.management.console.frontend' ).translate

notebook_widget = None

def create(a,b,c):
	return modconsole( a, b, c )

## def myinfo(settings):
##	if settings.listAdminModule('modconsole'):
##		return unimodule.realmodule("console", _("Console2"), _("Univention Console2"))
##	else:
##		return unimodule.realmodule("console", "", "")

def myrgroup():
	return ""

def mywgroup():
	return ""

def mymenunum():
	return 600

def mymenuicon():
	return '/icon/console.gif'

class modconsole(unimodule.unimodule):
	def __init__( self, a, b, c ):
		unimodule.unimodule.__init__( self, a, b, c )

	def __commonHeader(self, layoutType):
		obs = []
##		if self.save.get( 'auth_ok', None ):
##			self.logoutbut = button(_("Logout"),{'icon':'/style/cancel.gif'},{"helptext":_("Quit Session")})
##			obs.append(self.logoutbut)
		self.save.put( 'header_table_type' , 'content_header_menuless' )
		self.save.put( 'main_table_type' , 'content_main_menuless' )
		if baseConfig.has_key('umc/title') and baseConfig['umc/title']:
			self.save.put( 'site_title' , '%s' % baseConfig['umc/title'] )
		else:
			self.save.put( 'site_title' , 'Univention Management Console' )
		if baseConfig.has_key('umc/title/image') and \
			   baseConfig['umc/title/image']:
			self.save.put( 'header_img' , baseConfig['umc/title/image'] )
		else:
			self.save.put( 'header_img' , 'themes/images/default/management-console.gif' )


		self.subobjs.append(table("",
			{'type':'content_header_menuless'},
			{"obs":[tablerow("",{},{"obs":
						[tablecol("",{'type':layoutType},{"obs":[]}),
						 tablecol("",{'type':layoutType},{"obs":obs})
						 ]})]
			 }))

	def __login(self): # build login-Screen
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Function: __login: log on to UMCP server')
		self.__commonHeader('login_layout')

		# select language
		# the installed languages can be obtained via locale -a
		# but I shouldn't check on that but rely on the languages I set
		# up for this tool
		langs = [
				{"level": '0', "name": 'de', "description": "Deutsch"},
				{"level": '0', "name": 'en', "description": "English"}
				]
		self.chooselang=language_dojo_select(_("Language:"),{'width':'265'},{"helptext":_("Select language for this session"),"choicelist":langs})

		self.usernamein=question_text(_("Username"),{'width':'265','puretext': '1'},{"usertext":self.save.get("relogin_username"),"helptext":_("Please enter your uid.")})
		self.cabut=button(_("Cancel"),{'icon':'/style/cancel.gif'},{"helptext":_("Abort login")})
		if int(os.environ["HTTPS"]) == 1 or self.save.get("http") == 1:
			self.passwdin=question_secure(_("Password"),{'width':'265','puretext': '1'},{"usertext":self.save.get("relogin_passwd"),"helptext":_("Please enter your password.")})
			self.okbut=button(_("OK"),{'icon':'/style/ok.gif'},{"helptext":_("Login")})
		else:
			self.passwdin=question_secure(_("Password"),{'width':'265','passive':'true','puretext': '1'},
						{"usertext":self.save.get("relogin_passwd"),"helptext":_("Please enter your password.")})
			self.okbut=button(_("OK"),{'passive':'true','icon':'/style/ok.gif'},{"helptext":_("Login")})

		rows = []

		rows.append(tablerow("",{},{"obs":[tablecol("",{"colspan":"2",'type':'login_layout'},{"obs":[self.usernamein]})]}))
		rows.append(tablerow("",{},{"obs":[tablecol("",{"colspan":"2",'type':'login_layout'},{"obs":[self.passwdin]})]}))
		rows.append(tablerow("",{},{"obs":[tablecol("",{"colspan":"2",'type':'login_layout'},{"obs":[self.chooselang]})]}))

		#check if http should realy be used
		if int(os.environ["HTTPS"]) != 1:
			sel = ""
			if self.save.get("http") == 1:
				sel = "selected"
			self.httpbut = button('httpbut',{},{"helptext":_("")})
			self.httpbool= question_bool(   _("Not using a secure SSL connection. Click to continue."), {'width':'265'},
							{'helptext': _("Not using a secure SSL connection. Click to continue."),'button':self.httpbut,'usertext':sel})
			use_httpbool=tablecol("",{'colspan':'2','type':'login_layout'},{"obs":[self.httpbool]})
			rows.append(tablerow("",{},{"obs":[use_httpbool]}))

		okcol=tablecol("",{'type':'login_layout'},{"obs":[self.okbut]})
		cacol=tablecol("",{'type':'login_layout'},{"obs":[self.cabut]})
		rows.append(tablerow("",{},{"obs":[okcol,cacol]}))

		self.nbook=notebook('', {}, {'buttons': [(_('Login'), _('Login'))], 'selected': 0})
		self.subobjs.append(self.nbook)

		self.subobjs.append(table("",
			{'type':'content_main_menuless'},
			{"obs":[tablerow("",{},{"obs":[tablecol("",{},{"obs":[table("",{},{"obs":rows})]})]})]}
			))


	def __logout(self): # ask for logout and jump to login or back to process
		self.__commonHeader( 'login_layout')

		self.okbut=button(_("Logout"),{'icon':'/style/ok.gif'},{"helptext":_("Logout")})
		self.cabut=button(_("Cancel"),{'icon':'/style/cancel.gif'},{"helptext":_("Abort logout")})

		rows = []

		logouttext = text('',{},{'text':[_("Do you really want to logout?")]})
		rows.append(tablerow("",{},{"obs":[tablecol("",{"colspan":"2",'type':'login_layout'},{"obs":[ logouttext ]})]}))

		okcol=tablecol("",{'type':'login_layout'},{"obs":[self.okbut]})
		cacol=tablecol("",{'type':'login_layout'},{"obs":[self.cabut]})
		rows.append(tablerow("",{},{"obs":[okcol,cacol]}))

		self.nbook=notebook('', {}, {'buttons': [(_('Logout'), _('Logout'))], 'selected': 0})
		self.subobjs.append(self.nbook)

		self.subobjs.append(table("",
			{'type':'content_main_menuless'},
			{"obs":[tablerow("",{},{"obs":[tablecol("",{},{"obs":[table("",{},{"obs":rows})]})]})]}
			))

	def __process(self):
		global notebook_widget
		self.__commonHeader('about_layout')
		layout = notebook_widget.layout()
		report = notebook_widget.report()

		if report:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, '__process: report: %s' % report )
			self.userinfo( report )
		self.subobjs.extend( layout )

		if notebook_widget.refresh():
			self.atts['refresh']='1000'

			# This "link button" is needed in order for the refresh to
			# work properly.
			hack_button = button( '', { 'link' : '1' }, { 'helptext' : _( 'Update status' ) } )
			self.subobjs.append( hack_button )

	def mytype(self):
		return "dialog"

	def myinit(self):
		self.save = self.parent.save

		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Function: myinit')

		self.lo = self.args[ "uaccess" ] # will be None in console as we don't connect the ldap directly (so far...)

		if self.inithandlemessages():
			return

		if self.save.get('logout'): # quit connection and fall back to login...
			self.save.put('consolemode','logout')
			self.__logout()
			return

		if not self.save.get( 'auth_ok' , False ) == True: # do authentication and login
			# connect to daemon
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Function: myinit: connection to UMCP server')
			if not self.save.get( 'umc_connected', False ):
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Function: myinit: trying ...')
				if not client.connect( timeout = 10 ):
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Function: myinit: FAILED')

			if client.error_get() != client.NOERROR:
				self.save.put( 'consolemode', None )
				self.save.put( 'auth_ok', False )
				self.usermessage( _('Authentication failed: A connection to the UMC daemon could not be established.' ) )
				univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'UMCP client error: no connection')
			else:
				self.save.put('consolemode','login')
				self.save.put( 'umc_connected', True )
				self.__login()
		else:								 # process the umcp-response
			if client.error_get() != client.NOERROR:
				self.save.put( 'consolemode', None )
				self.save.put( 'auth_ok', False )
				self.save.put( 'umc_connected', False )
				return
			self.save.put('consolemode','process')
			global notebook_widget
			if not notebook_widget:
				notebook_widget = widget.Notebook( self.save )

			self.__process()

	def apply(self):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Function: apply')
		self.applyhandlemessages()

		if self.save.get('consolemode') == 'login':
			self.save.put("relogin_username",self.usernamein.xvars.get("usertext",""))
			self.save.put("relogin_password",self.passwdin.xvars.get("usertext",""))

			if int(os.environ["HTTPS"]) != 1 and self.httpbool.selected():
				self.save.put("http",1)
			else:
				self.save.put("http",0)

			if self.cabut.pressed():
				self.save.put( 'auth_ok', False ) # just to be sure

			if self.okbut.pressed():
				authUsername = self.usernamein.xvars.get("usertext","")
				authPassword = self.passwdin.xvars.get("usertext","")

				if not authUsername or not authPassword:
					return
				req = umcp.Request( 'AUTH' )
				req.body[ 'username' ] = authUsername
				req.body[ 'password' ] = authPassword

				id = client.request_send( req )
				response = client.response_wait( id, timeout = 10 )
				if response:
					(authenticated, status, statusinformation) = \
						( response.status() == 200, response.status(),
						  umcp.status_information( response.status() ) )
				else:
					authenticated = False
					statusinformation = 'no response yet :('
				if authenticated:
					self.save.put( 'auth_ok', True )

					# create authenticated ldap connection
					ldapc = umc.LdapConnection()
					if ldapc:
						res = ldapc.searchDn( filter = 'uid=%s' % authUsername )
						# use only first object found
						if res and res[0]:
							ldapc.connect( binddn = res[0], bindpw = authPassword )

					# set locale after authentication
					language = None
					if hasattr(self, 'chooselang'):
						language = self.chooselang.getselected()

					if language:
						if language == 'de':
							language = LANG_DE
						elif language == 'en':
							language = LANG_EN
						else:
							language = LANG_DEFAULT
						# WARNING this code could cause an exception maybe it needs to be surrounded by parenthesis
						os.environ["LC_MESSAGES"] = language
						locale.setlocale( locale.LC_MESSAGES, language )

						req = umcp.Request( 'SET', args = ('locale', language ) )
						id = client.request_send( req )
						response = client.response_wait( id, timeout = 10 )
						if response:
							(status, statusinformation) = \
									 ( response.status(), umcp.status_information( response.status() ) )
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
												   'modconsole.py: locale set (%s): status: %s (%s)' % (language, status, statusinformation))
						else:
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
												   'modconsole.py: setting locale timed out')

					# pass sessionid to UMC server after successful authentication
					req = umcp.Request( 'SET', args = ('sessionid', client._sessionId ) )
					id = client.request_send( req )
					response = client.response_wait( id, timeout = 10 )
					if response:
						(status, statusinformation) = ( response.status(), umcp.status_information( response.status() ) )
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
											   'modconsole.py: sessionid set (%s): status: %s (%s)' % (client._sessionId, status, statusinformation))
					else:
						univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'modconsole.py: setting sessionid timed out')
				else:
					self.save.put( 'consolemode', None )
					self.save.put( 'auth_ok', False )
					self.usermessage( _('Authentication failed: %s') % statusinformation )

		elif self.save.get('consolemode') == 'logout':
			if self.cabut.pressed():
				self.save.put( 'consolemode', 'process' )
				self.save.put( 'logout', None )
			if self.okbut.pressed():
				client.disconnect()
				ldapc = umc.LdapConnection()
				if ldapc:
					ldapc.disconnect()
				self.save.put( 'consolemode', 'login' )
				self.save.put( 'logout', None )
				self.save.put( 'umc_connected', False )
				self.save.put( 'auth_ok', False )
				self.userinfo( _( 'Logout successful.' ) )

		elif self.save.get('consolemode') == 'process':
			global notebook_widget
			notebook_widget.apply()
			report = notebook_widget.report()
			if report:
				self.userinfo( report )

		elif self.save.get('consolemode'):
			raise "unknown consolemode"
		else:
			pass # no consolemode set, maybe a failed login
