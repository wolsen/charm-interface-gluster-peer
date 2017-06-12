# Overview

This interface handles the exchange of data between peers in a glusterfs
charm deployment using the `gluster-peer` interface protocol.

# Usage

The interface will set the following reactive states, as appropriate:

  * `{relation_name}.connected` The relation has been initiated and is ready
    to be configured for the remote unit's consumption. The local unit should
    provide local information for which address the remote gluster node
    should use for actions such as probing and which bricks are available.
    The following methods should be used for the local unit to provide this
    information to the remote unit:

    * `set_address`
    * `set_bricks`

    Note: the `set_address` method requires an address_type to be specified.
    This is to support network splits, which may not be fully supported in
    gluster.

  * `{relation_name}.available` The relation has been completed in that the
    remote units have provided their address and their available bricks. The
    local unit may have need information from the remote units (e.g. when
    creating a volume). This information can be retrieved using the following
    methods:

    * `ip_map`
    * `brick_map`
