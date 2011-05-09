#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMCP definitions like commands, error codes etc.
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

import univention.management.console.locales as locales

_ = locales.Translation( 'univention.management.console' ).translate

__all__ = ( 'command_names', 'command_is_known', 'command_has_arguments',
			'command_has_options', 'command_is_valid_option',
			'status_information' )

COMMANDS = {
	'AUTH' : ( False, ( 'username', 'password' ) ),
	'COMMAND' : ( True, () ),
	'VERSION' : ( False, None ),
	'GET' : ( True, () ),
	'SET' : ( True, () ),
	'CLOSE' : ( False, None ),
	'CANCEL' : ( False, ( 'ids', ) ),
	'STATUS' : ( False, ( 'ids', ) ),
	'EXIT' : ( True, () ),
}

STATUSINFORMATION = {
	200 : _( 'OK, operation successful' ),
	201 : _( 'OK, containing report message' ),
	210 : _( 'OK, partial response' ),
	250 : _( 'OK, operation successful ask for shutdown of connection' ),
	300 : _( 'Command currently not available/possible' ),
	301 : _( 'non-fatal error, processing may continue' ),
	400 : _( 'Bad request' ),
	401 : _( 'Unauthorized' ),
	402 : _( 'Invalid command arguments' ),
	403 : _( 'Forbidden' ),
	404 : _( 'Not found' ),
	405 : _( 'Command not allowed' ),
	406 : _( 'Unknown command' ),
	411 : _( 'Authentication failed' ),
	412 : _( 'Account is expired' ),
	413 : _( 'Account is disabled' ),
	414 : _( 'Access to console daemon is prohibited' ),
	415 : _( 'Command execution prohibited' ),
	500 : _( 'Internal error' ),
	501 : _( 'Request could not be found' ),
	502 : _( 'Module process died unexpectedly' ),
	503 : _( 'Connection to module process failed' ),
	504 : _( 'SSL server certificate is not trustworthy' ),
	551 : _( 'Unparsable message header' ),
	552 : _( 'Unknown command' ),
	553 : _( 'Invalid number of arguments' ),
	554 : _( 'Unparsable message body' ),
	600 : _( 'Error occuried during command processing' ),
	601 : _( 'Specified locale is not available' ),
	}

def command_names():
	return COMMANDS.keys()

def command_is_known( name ):
	return ( name in COMMANDS.keys() )

def command_has_arguments( name ):
	return COMMANDS.get( name )[ 0 ] == True

def command_has_options( name ):
	return COMMANDS.get( name )[ 1 ] != None

def command_is_valid_option( name, option ):
	if name in COMMANDS:
		valid = COMMANDS[ name ][ 1 ]
		if valid == None:
			return False
		if not len( valid ):
			return True
		return option in valid

	return False

def status_information( status ):
	if status in STATUSINFORMATION:
		return STATUSINFORMATION[ status ]

	return _( 'Unknown state' )
