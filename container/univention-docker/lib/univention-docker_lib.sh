# UCS Docker shell function collection
#
# Copyright 2015 Univention GmbH
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

CONT_ID_FILE=/var/lib/docker/.stopped_containers

get_container_names() {
	docker ps -q "$@" | tr '\n' ' '
}

_shutdown_container() {
	local CONT_ID="${1:?Missing argument: container ID}"
	local BACKGR="${2:-}"
	local cmd

	if EXE=$(docker exec "${CONT_ID}" which telinit); then
		cmd="telinit 0"
		TIME=60
	elif EXE=$(docker exec "${CONT_ID}" which halt); then
		cmd="halt"
		TIME=60
	elif EXE=$(docker exec ${CONT_ID} which init); then
		cmd="init 0"
		TIME=60
	else
		TIME=10
	fi

	if [ -n "$cmd" ]; then
		docker exec "${CONT_ID}" ${cmd} >/dev/null 2>&1
		if ! [ "$?" -eq 0 ]; then
			sleep 1
			docker exec "${CONT_ID}" ${cmd}
		fi
	fi

	if [ -z "$BACKGR" ]; then
		docker stop --time=$TIME "${CONT_ID}"
	else
		docker stop --time=$TIME "${CONT_ID}" &
	fi
}

shutdown_all_containers() {
	# shutdown all running containers.
	# saves a list of IDs, that will be started with
	# start_previous_containers()

	if [ -z "$(get_container_names)" ]; then
		return 0
	fi

	get_container_names > "$CONT_ID_FILE"
	shutdown_containers
}

shutdown_containers() {
	# no arguments: shutdown all running containers
	# ID ID ...: shutdown the containers with these IDs
	CONTAINERS=${@:-$(get_container_names)}

	# start parallel shutdown
	for CONT_ID in ${CONTAINERS}; do
		_shutdown_container "${CONT_ID}" 1
	done

	# wait for all containers to have stopped
	if [ -z "${CONTAINERS}" ]; then
		return
	fi
	docker wait ${CONTAINERS} >/dev/null 2>&1 &
	DW_PID="$!"

	# don't wait 60s if system has already shutdown, "docker wait" will exit when
	# all containers have either shutdown or been killed
	while kill -0 "${DW_PID}" 2>/dev/null; do
		RUNNING_CONTAINERS=$(containers_running ${CONTAINERS})
		for CONT_ID in $RUNNING_CONTAINERS; do
			if is_container_with_init "${CONT_ID}" && container_with_init_has_shutdown "${CONT_ID}"; then
				output=$(docker kill "${CONT_ID}" 2>&1)
				if ! [ $? -eq 0 ] && [ -n "$output" ]; then
					echo "$output"
				fi
			fi
		done
		sleep 1
	done
}

previous_containers_exist() {
	test -e "$CONT_ID_FILE"
}

start_previous_containers() {
	for CONT_ID in $(cat "$CONT_ID_FILE"); do
		docker start "${CONT_ID}"
	done
}

docker_is_running() {
	docker version >/dev/null 2>&1
}

start_all_stopped_containers() {
	for CONT_ID in $(get_container_names --all); do
		docker start "${CONT_ID}"
	done
}

container_with_init_has_shutdown()  {
	local CONT_ID="${1:?Missing argument: container ID}"

	test "$(docker exec -t "${CONT_ID}" ps ax | wc -l)" -lt 4
}

is_container_with_init() {
	local CONT_ID="${1:?Missing argument: container ID}"

	docker exec -t "${CONT_ID}" ps -p 1 -o comm= | grep -q init
}

containers_running() {
	# args: [id] ...
	# return IDs of those containers that are running
	ALL_CONT_ID=$(get_container_names)

	if [ $# = 0 ] || [ -z "$ALL_CONT_ID" ]; then
		return
	fi

	RET=""
	for CONT_ID in $@; do
		for LIVE_CONT_ID in $ALL_CONT_ID; do
			if [ $CONT_ID = $LIVE_CONT_ID ]; then
				echo -n "$CONT_ID "
			fi
		done
	done
}

