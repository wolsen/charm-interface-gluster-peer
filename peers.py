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


class GlusterPeers(RelationBase):
    scope = scopes.UNIT

    @hook('{peers:gluster-peer}-relation-joined')
    def joined(self):
        self.conversation().set_state('{relation_name}.connected')

    @hook('{peers:gluster-peer}-relation-changed')
    def changed(self):
        conv = self.conversation()
        conv.set_state('{relation_name}.connected')
        if self.data_complete(conv):
            conv.set_state('{relation_name}.available')

    @hook('{peers:gluster-peer}-relation-{broken,departed}')
    def departed_or_broken(self):
        conv = self.conversation()
        conv.remove_state('{relation_name}.connected')
        if not self.data_complete(conv):
            conv.remove_state('{relation_name}.available')

    def ip_map(self, address_key='private-address'):
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
            'unit-glusterfs-1': ['/dev/sdb', '/dev/sdc'],
            'unit-glusterfs-2': ['/dev/sdb', '/dev/sdc', '/dev/sdd'],
        }

        :return: a map with key being hostname and the value being a list of
            brick names on the remote unit.
        """
        brick_map = {}
        for conv in self.conversations():
            host_name = conv.scope.replace('/', '-')
            brick_map[host_name] = conv.get_remote('bricks') or []

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
