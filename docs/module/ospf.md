# OSPF Configuration Module

The OSPF configuration module configures OSPF routing process.

### Node Parameters

* **ospf.process** -- process ID (default: 1)
* **ospf.area** -- default OSPF area (default: 0.0.0.0). Used on links without explicit OSPF area, and on loopback interface.

You can specify node parameters as global values (top-level topology elements) or within individual nodes (see [example](#example) for details).

### Link Parameters

* **ospf.cost** -- OSPF cost
* **ospf.area** -- OSPF area. Use on ABRs; node-level OSPF area is recommended for intra-area routers.

**Note:** Per-link areas are currently not implemented in Junos configuration template. Please feel free to fix the configuration template and submit a pull request.

### Other Parameters

Link type is used to set OSPF network type:

* *P2P link* ⇒ **point-to-point** network
* Any other link type ⇒ **broadcast** network

## Example

We want to create a three-router multi-area OSPF network:

* R1 is a backbone area router
* R2 is ABR between backbone area and area 1
* R3 is in intra-area router in area 1.

All devices run OSPF:
```
module: [ ospf ]
```

Default OSPF area is 0.0.0.0:
```
ospf:
  area: 0.0.0.0
```

R1 and R2 are in default OSPF area (no need to specify per-node area):

```
nodes:
  r1:
    device: iosv
  r2:
    device: eos
```

R3 is in area 1. Non-default OSPF area must be specified within node data:

```
nodes:
  r3:
    device: nxos
    ospf:
      area: 0.0.0.1
```

Link between R1 and R2 is in area 0. No need to specify per-link area:

```
links:
- r1:
  r2:
```

Link between R2 and R3 is in area 1. Specify OSPF area within link definition:

```
links:
- r2:
  r3:
  ospf:
    area: 0.0.0.1
```

**Interesting details**: 

* The default value for interface OSPF area is the node OSPF area (specified in configuration template).
* The default value for node OSPF area is the global OSPF area (which is defined in **all** Ansible inventory group).
* Due to the propagation of default values, the OSPF area for R2-R3 link would be area 0 on R2 and area 1 on R3. The OSPF area thus needs to be specified within link definition.

### Resulting Device Configurations

The above topology generates the following device configurations

#### R1 (Cisco IOS)

```
router ospf 1
!
interface Loopback0
 ip ospf 1 area 0.0.0.0
!
interface GigabitEthernet0/1
 ip ospf 1 area 0.0.0.0
 ip ospf network point-to-point
```

#### R2 (Arista EOS)

```
router ospf 1
!
interface Loopback0
 ip ospf area 0.0.0.0
!
interface Ethernet1
 ip ospf area 0.0.0.0
 ip ospf network point-to-point
!
interface Ethernet2
 ip ospf area 0.0.0.1
 ip ospf network point-to-point
```

#### R3 (Cisco Nexus-OS)

```
feature ospf
!
router ospf 1
!
interface loopback0
 ip router ospf 1 area 0.0.0.1
!
interface Ethernet1/1
 ip router ospf 1 area 0.0.0.1
 ip ospf network point-to-point
```

### Complete network topology:

```
module: [ ospf ]

ospf:
  area: 0.0.0.0

nodes:
  r1:
    device: iosv
  r2:
    device: eos
  r3:
    device: nxos
    ospf:
      area: 0.0.0.1

links:
- r1:
  r2:

- r2:
  r3:
  ospf:
    area: 0.0.0.1
```