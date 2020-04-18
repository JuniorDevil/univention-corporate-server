# -*- coding: utf-8 -*-
"""
|UDM| functions for checking/manipulating |IP| addresses and ranges.
"""
# Copyright 2004-2020 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

from __future__ import absolute_import

from ipaddress import IPv4Address, IPv4Network  # FIXME: Unfortunately this file is called the same as the Python module and even absolute_import above cannot make it work - doctest bewlow will NOT work! Therefore we should move the code in the 3 locations were it is used only.


def ip_is_in_network(subnet, subnetmask, ip):
	# type: (str, str, str) -> bool
	"""
	Check if the given |IPv4| address is inside the given subnet.

	:param subnet: A |IPv4| network address.
	:param subnetmask: The |IPv4| network prefix length.
	:param ip: The |IPv4| address to check.
	:returns: `True` if the |IP| address is inside the subnet, `False` otherwise.

	.. deprecated:: 4.4-4
	   Used in ../admin/handlers/__init__.py and ../admincli/admin.py only

	>>> ip_is_in_network('192.0.2.0', 24, '192.0.2.42')
	True
	>>> ip_is_in_network('192.0.2.0', 24, '192.0.3.42')
	False
	"""
	return IPv4Address(u'%s' % (ip,)) in IPv4Network(u'%s/%s' % (subnet, subnetmask), strict=False)


if __name__ == '__main__':
	import doctest
	doctest.testmod()
