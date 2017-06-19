#!/usr/bin/python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from charms.reactive import RelationBase
from charms.reactive import hook
from charms.reactive import scopes
from charmhelpers.core import hookenv
from charmhelpers.core import unitdata


class GlusterPeers(RelationBase):
    scope = scopes.UNIT

    def __init__(self, *args, **kwargs):
        self.local_name = hookenv.local_unit().replace('/', '-')
        super(GlusterPeers, self).__init__(*args, **kwargs)

    @hook('{peers:gluster-peer}-relation-joined')
    def joined(self):
        self.conversation().set_state('{relation_name}.connected')

    @hook('{peers:gluster-peer}-relation-changed')
    def changed(self):
        conv = self.conversation()
        self._evaluate_brick_events()

        # Check to see if this is actually true or not.
        if self.data_complete(conv):
            conv.set_state('{relation_name}.available')

    def _evaluate_brick_events(self):
        """
        Raises any relevant brick change events based on the bricks
        advertised by the remote unit.

        Evaluates the remote unit's advertised bricks and the local unit's
        knowledge of said bricks and sets the following reactive states:

         - `{relation_name}.bricks.available`: When the remote unit
           advertises a brick device which is not known the local unit.

         - `{relation_name}.bricks.removed`: When the local unit knows about a
           brick device that is not advertised by the remote unit.

        Note: the entire brick set is evaluated for the remote unit
        participating in the conversation. AS such, both events/states may be
        set in a single invocation.
        """
        conv = self.conversation()
        local_bricks = set(conv.get_local('bricks') or [])
        remote_bricks = set(conv.get_remote('bricks') or [])

        # When the local unit has more bricks than the remote unit,
        # a bricks.removed state should be set on the conversation.
        if local_bricks.difference(remote_bricks):
            conv.set_state('{relation_name}.bricks.removed')

        # When the peer unit has advertised that it has more bricks than this
        # local unit knows about, then there are new bricks available.
        if remote_bricks.difference(local_bricks):
            conv.set_state('{relation_name}.bricks.available')

        # Save the remote_bricks as the local copy and flush the data to ensure
        # that it is persisted.
        conv.set_local('bricks', conv.get_remote('bricks') or [])
        unitdata.kv().flush()

    @hook('{peers:gluster-peer}-relation-{broken,departed}')
    def departed_or_broken(self):
        conv = self.conversation()
        conv.remove_state('{relation_name}.connected')
        if not self.data_complete(conv):
            conv.remove_state('{relation_name}.available')

    def ip_map(self, address_key='private-address'):
        """
        Returns a list of (unit_name, ip_address) tuples. The unit name will
        will have the '/' replaced by a '-'.

        An example list is:

        [
            ('glusterfs-0', '172.16.10.5'),
            ('glusterfs-1', '172.16.10.6'),
        ]

        :param address_key: the type of address to return, defaults to the
            private-address of the remote unit.
        :return: a list of (unit_name, ip_address) tuples.
        """
        nodes = []
        for conv in self.conversations():
            host_name = conv.scope.replace('/', '-')
            nodes.append((host_name, conv.get_remote(address_key)))

        return nodes

    def brick_map(self):
        """
        Returns a map of the bricks on remote units mapped by the unit's
        name. The unit name will have the '/' replaced by a '-'.

        An example mapping is:

        {
            'glusterfs-1': ['/dev/sdb', '/dev/sdc'],
            'glusterfs-2': ['/dev/sdb', '/dev/sdc', '/dev/sdd'],
        }

        :return: a map with key being hostname and the value being a list of
            brick names on the remote unit.
        """
        brick_map = {}
        for conv in self.conversations():
            host_name = conv.scope.replace('/', '-')
            brick_map[host_name] = conv.get_remote('bricks') or []

        # Include any bricks which have been set by the local unit.
        brick_map[self.local_name] = self._get_local_bricks()

        return brick_map

    def data_complete(self, conv):
        """Determines if the gluster peer conversation is completed or not.

        The conversation is complete when the remote unit has provided its
        address and its list of bricks.

        :param conv: the conversation to check if the data is complete
        """
        data = {
            'private_address': conv.get_remote('private-address'),
            'bricks': conv.get_remote('bricks'),
        }
        if all(data.values()):
            return True
        return False

    def set_address(self, address_type, address):
        """Advertise the address of this unit of a particular type

        :param address_type: str Type of address being advertised, e.g.
            internal/public/admin etc
        :param address: str IP of this unit in 'address_type' network
        :return: None
        """

        for conv in self.conversations():
            conv.set_remote(
                key='{}-address'.format(address_type),
                value=address)

    def set_bricks(self, bricks):
        """Advertise to the remote units what the local unit's bricks are.

        :param bricks: the list of bricks available on the local unit
        :return: None
        """
        for conv in self.conversations():
            conv.set_remote(key='bricks', value=bricks or [])

        # Save the local bricks as a locally scoped key in the local
        # key/value storage. This data will be returned in the brick_map
        # for consumption by the charm.
        self._save_local_bricks(bricks)

    def _save_local_bricks(self, bricks):
        """Saves the list of bricks to the local key/value storage for later
        use.

        :param bricks: the bricks to save in local storage.
        :return: None
        """
        kv = unitdata.kv()
        key = '%s.%s' % (self.local_name, 'bricks')
        kv.set(key, bricks)
        kv.flush()

    def _get_local_bricks(self):
        """Returns a list of the bricks set for the local unit.

        :return list: the list of bricks set by the local unit
        """
        kv = unitdata.kv()
        key = '%s.%s' % (self.local_name, 'bricks')
        return kv.get(key) or []

    def send_all(self, settings, store_local=False):
        """Advertise a setting to peer units

        :param settings: dict Settings to be advertised to peers
        :param store_local: boolean Whether to store setting in local db
        :return: None
        """
        for conv in self.conversations():
            conv.set_remote(data=settings)
            if store_local:
                conv.set_local(data=settings)

    def retrieve_local(self, key):
        """Inspect conversation and look for key in local db

        :param key: str Key to look for in localdb
        :return list: List of values of the specified key
        """
        values = []
        for conv in self.conversations():
            value = conv.get_local(key)
            if value:
                values.append(value)
        return values

    def retrieve_remote(self, key):
        """Inspect conversation and look for key being advertised by peer

        :param key: str Key to look for from peer
        :return list: List of values of the specified key
        """
        values = []
        for conv in self.conversations():
            value = conv.get_remote(key)
            if value:
                values.append(value)
        return values
