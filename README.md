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

  * `{relation_name}.departed` A unit of the gluster cluster has been removed.
    The local unit can query the remaining units via the `ip_map` or 
    `brick_map` methods.  

  * `{relation_name}.bricks.available` One or more storage bricks on a remote  
    unit is new to the local unit. All bricks in the cluster can be retrieved
    using the `brick_map` method, which return a mapping of units to bricks.

  * `{relation_name}.bricks.removed` One or more storage bricks previously 
    known by the local unit is no longer in the remote unit. The current map 
    of known bricks in the application can be retrieved using the `brick_map`
    method.
