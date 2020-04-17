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
try:
	from typing import Tuple  # noqa F401
except ImportError:
	pass


def ip_plus_one(ip):
	# type: (str) -> str
	"""
	Return logical next |IPv4| address.

	:param ip: An |IPv4| address in dotted-quad notation.
	:returns: An |IPv4| address in dotted-quad notation.

	.. deprecated:: 4.4-4
	   unused

	>>> ip_plus_one('0.0.0.0')
	'0.0.0.1'
	>>> ip_plus_one('0.0.0.254')
	'0.0.1.0'
	>>> ip_plus_one('0.0.0.255')
	'0.0.1.1'
	"""
	# WTF: this function seems to expect it's a /24 address?!
	addr = IPv4Address(u'%s' % (ip,))
	broadcast = IPv4Network(u'%s/24' % (ip,), strict=False).broadcast_address
	if addr == broadcast:
		addr += 1
	addr += 1
	if addr == broadcast:
		addr += 1
	return str(addr)


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


def ip_is_network_address(subnet, subnetmask, ip):
	# type: (str, str, str) -> bool
	"""
	Check if the given |IPv4| address is the network address (host bits are all zero).

	:param subnet: A |IPv4| network address.
	:param subnetmask: The |IPv4| network prefix length.
	:param ip: The |IPv4| address to check.
	:returns: `True` if the |IP| address is the network address, `False` otherwise.

	.. deprecated:: 4.4-4
	   Used in handlers/dhcp/subnet.py only

	>>> ip_is_network_address('192.0.2.0', 24, '192.0.2.0')
	True
	"""
	return IPv4Address(u'%s' % (ip,)) == IPv4Network(u'%s/%s' % (subnet, subnetmask), strict=False).network_address


def ip_is_broadcast_address(subnet, subnetmask, ip):
	# type: (str, str, str) -> bool
	"""
	Check if the given |IPv4| address is the network broadcast address (host bits are all one).

	:param subnet: The |IPv4| network address.
	:param subnetmask: The |IPv4| network prefix length.
	:param ip: The |IPv4| address to check.
	:returns: `True` if the |IP| address is the network broadcast address, `False` otherwise.

	.. deprecated:: 4.4-4
	   Used in handlers/dhcp/subnet.py only

	>>> ip_is_broadcast_address('192.0.2.0', 24, '192.0.2.255')
	True
	"""
	return IPv4Address(u'%s' % (ip,)) == IPv4Network(u'%s/%s' % (subnet, subnetmask), strict=False).broadcast_address


def ip_compare(ip1, ip2):
	# type: (str, str) -> int
	"""
	Compare two |IPv4| addresses in dotted-quad format.

	:param ip1: The first |IPv4| address.
	:param ip2: The second |IPv4| address.
	:returns: `>0` if the first address is before the second, `<0` if the first is after the second, or `0` when they are equal.

	.. deprecated:: 4.4-4
	   unused

	>>> ip_compare('192.0.2.1', '192.0.2.2')
	1
	>>> ip_compare('192.0.2.2', '192.0.2.2')
	0
	>>> ip_compare('192.0.2.3', '192.0.2.2')
	-1
	"""
	sip1, sip2 = (int(IPv4Address(u'%s' % (ip,))) if ip else 0 for ip in (ip1, ip2))
	return sip2 - sip1


def is_ip_in_range(ip, range):
	# type: (str, Tuple[str, str]) -> bool
	"""
	Check if a |IPv4| address is inside the given range.

	:param ip: The |IPv4| address to check.
	:param range: The inclusive range as a 2-tuple (low, hight) of |IPv4| addresses.
	:returns: `True` if the address is inside the range, `False` otherwise.

	.. deprecated:: 4.4-4
	   used below

	>>> is_ip_in_range('192.0.2.10', ('192.0.2.0', '192.0.2.255'))
	True
	>>> is_ip_in_range('192.0.3.10', ('192.0.2.0', '192.0.2.255'))
	False
	>>> is_ip_in_range('192.0.1.10', ('192.0.2.0', '192.0.2.255'))
	False
	"""
	ip_, first, last = (IPv4Address(u'%s' % (addr,)) for addr in (ip, range[0], range[1]))
	return first <= ip_ <= last


def is_range_overlapping(range1, range2):
	# type: (Tuple[str, str], Tuple[str, str]) -> bool
	"""
	Check if two |IPv4| addresse ranges overlap.

	:param range1: The first range as a 2-tuple (low, high) of |IPv4| addresses.
	:param range2: The second range as a 2-tuple (low, high) of |IPv4| addresses.
	:returns: `True` if the ranges overlap, `False` otherwise.

	.. deprecated:: 4.4-4
	   Used in handlers/dhcp/subnet.py only

	>>> is_range_overlapping(('192.0.2.0', '192.0.2.127'), ('192.0.2.128', '192.0.2.255'))
	False
	>>> is_range_overlapping(('192.0.2.0', '192.0.2.127'), ('192.0.2.64', '192.0.2.191'))
	True
	>>> is_range_overlapping(('192.0.2.0', '192.0.2.255'), ('192.0.2.64', '192.0.2.191'))
	True
	>>> is_range_overlapping(('192.0.2.128', '192.0.2.255'), ('192.0.2.64', '192.0.2.191'))
	True
	"""
	if is_ip_in_range(range1[0], range2) or is_ip_in_range(range1[1], range2):
		return True
	if is_ip_in_range(range2[0], range1) or is_ip_in_range(range2[1], range1):
		return True
	return False


if __name__ == '__main__':
	import doctest
	doctest.testmod()
