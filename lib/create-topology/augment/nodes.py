'''
Create detailed node-level data structures from topology

* Discover desired imagex (boxes)
* Add default module list to nodes without specific modules
* Set loopback and management interface data
'''

import netaddr
import common
import addressing
import os
import yaml
from box import Box

def adjust_node_list(nodes):
  node_list = []
  if isinstance(nodes, dict):
    for k,v in sorted(nodes.items()):
      if v is None:
        v = Box({},default_box=True)
      elif not isinstance(v,dict):
        common.error('Node data for node %s must be a dictionary' % k)
        v = Box({ 'extra': v })
      v.name = k
      node_list.append(v)
  else:
    for n in nodes:
      node_list.append(n if isinstance(n,dict) else { 'name': n })
  return node_list

def augment_mgmt_if(node,device_data,addrs):
  node.setdefault('mgmt',{})

  if 'ifname' not in node.mgmt:
    mgmt_if = device_data.mgmt_if
    if not mgmt_if:
      ifname_format = device_data.interface_name
      if not ifname_format:
        common.fatal("Missing interface name template for device type %s" % node['device'])

      ifindex_offset = device_data.get('ifindex_offset',1)
      mgmt_if = ifname_format % (ifindex_offset - 1)
    node.mgmt.ifname = mgmt_if

  if addrs:
    for af in 'ipv4','ipv6':
      pfx = af + '_pfx'
      if pfx in addrs:
        if not af in node.mgmt:
          node.mgmt[af] = str(addrs[pfx][node['id']+addrs['start']])

    if addrs.mac_eui:
      addrs.mac_eui[5] = node['id']
      node.mgmt.setdefault('mac',str(addrs['mac_eui']))

#
# Add device (box) images from defaults
#
def augment_node_images(topology):
  provider = topology.provider
  devices = topology.defaults.devices
  if not devices:
    common.fatal('Device defaults (defaults.devices) are missing')

  for n in topology.nodes:
    n.setdefault('device',topology.defaults.get('device'))
    if not n.device:
      common.error('No device type specified for node %s and there is no default device type' % n.name)
      continue

    if n.box:
      continue
    if 'image' in n:
      n.box = n.image
      del n['image']
      continue

    devtype = n.device
    if not devtype in devices:
      common.error('Unknown device %s in node %s' % (devtype,n.name))
      continue

    box = devices[devtype].image[provider]
    if not box:
      common.error('No image specified for device %s (provider %s) used by node %s' % (devtype,provider,n['name']))
      continue

    n.box = box

# Set default list of modules for nodes without specific module list
#
def augment_node_module(topology):
  if not 'module' in topology:
    return

  module = topology['module']
  for n in topology.nodes:
    if not 'module' in n:
      n.module = module

# Merge global module parameters with per-node module parameters
#
def merge_node_module_params(topology):
  for n in topology.nodes:
    if 'module' in n:
      for m in n.module:
        if m in topology:
          n[m] = topology[m] + n[m]

'''
Main node transformation code

* set node ID
* set loopback address(es)
* copy device data from defaults
* set management IP and MAC addresses
'''
def transform(topology,defaults,pools):
  augment_node_images(topology)

  id = 0
  ndict = {}
  for n in topology['nodes']:
    id = id + 1
    if n.id:
      common.error("ERROR: static node IDs are not supported, overwriting with %d: %s" % (id,str(n)))
    n.id = id

    if not n.name:
      common.error("ERROR: node does not have a name %s" % str(n))
      continue

    if pools.loopback:
      prefix_list = addressing.get(pools,['loopback'])
      for af in prefix_list:
        if af == 'ipv6':
          n.loopback[af] = addressing.get_addr_mask(prefix_list[af],1)
        else:
          n.loopback[af] = str(prefix_list[af])

    device_data = defaults.devices[n.device]
    if not device_data:
      common.error("ERROR: Unsupported device type %s: %s" % (n.device,n))
      continue

    augment_mgmt_if(n,device_data,topology.addressing.mgmt)

    ndict[n.name] = n

  topology.nodes_map = ndict
  return ndict
