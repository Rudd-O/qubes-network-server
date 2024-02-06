import subprocess

from unittest import mock
from qubesroutingmanager import setup_plain_forwarding_for_address


ALREADY_ADDED = """
{
  "nftables": [
    {
      "metainfo": {
        "version": "1.0.5",
        "release_name": "Lester Gooch #4",
        "json_schema_version": 1
      }
    },
    {
      "table": {
        "family": "ip",
        "name": "qubes",
        "handle": 1
      }
    },
    {
      "set": {
        "family": "ip",
        "name": "downstream",
        "table": "qubes",
        "type": "ipv4_addr",
        "handle": 3,
        "elem": [
          "10.137.0.10",
          "10.250.4.13"
        ]
      }
    },
    {
      "set": {
        "family": "ip",
        "name": "allowed",
        "table": "qubes",
        "type": [
          "ifname",
          "ipv4_addr"
        ],
        "handle": 4,
        "elem": [
          {
            "concat": [
              "vif6.0",
              "10.137.0.10"
            ]
          },
          {
            "concat": [
              "vif12.0",
              "10.250.4.13"
            ]
          }
        ]
      }
    },
    {
      "chain": {
        "family": "ip",
        "table": "qubes",
        "name": "prerouting",
        "handle": 1,
        "type": "filter",
        "hook": "prerouting",
        "prio": -300,
        "policy": "accept"
      }
    },
    {
      "chain": {
        "family": "ip",
        "table": "qubes",
        "name": "antispoof",
        "handle": 2
      }
    },
    {
      "chain": {
        "family": "ip",
        "table": "qubes",
        "name": "postrouting",
        "handle": 60,
        "type": "nat",
        "hook": "postrouting",
        "prio": 100,
        "policy": "accept"
      }
    },
    {
      "chain": {
        "family": "ip",
        "table": "qubes",
        "name": "input",
        "handle": 61,
        "type": "filter",
        "hook": "input",
        "prio": 0,
        "policy": "drop"
      }
    },
    {
      "chain": {
        "family": "ip",
        "table": "qubes",
        "name": "forward",
        "handle": 62,
        "type": "filter",
        "hook": "forward",
        "prio": 0,
        "policy": "accept"
      }
    },
    {
      "chain": {
        "family": "ip",
        "table": "qubes",
        "name": "custom-input",
        "handle": 63
      }
    },
    {
      "chain": {
        "family": "ip",
        "table": "qubes",
        "name": "custom-forward",
        "handle": 64
      }
    },
    {
      "chain": {
        "family": "ip",
        "table": "qubes",
        "name": "dnat-dns",
        "handle": 87,
        "type": "nat",
        "hook": "prerouting",
        "prio": -100,
        "policy": "accept"
      }
    },
    {
      "chain": {
        "family": "ip",
        "table": "qubes",
        "name": "qubes-routing-manager",
        "handle": 105
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "prerouting",
        "handle": 5,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "iifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "goto": {
              "target": "antispoof"
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "prerouting",
        "handle": 6,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "payload": {
                  "protocol": "ip",
                  "field": "saddr"
                }
              },
              "right": "@downstream"
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "antispoof",
        "handle": 7,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "concat": [
                  {
                    "meta": {
                      "key": "iifname"
                    }
                  },
                  {
                    "payload": {
                      "protocol": "ip",
                      "field": "saddr"
                    }
                  }
                ]
              },
              "right": "@allowed"
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "antispoof",
        "handle": 8,
        "expr": [
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "postrouting",
        "handle": 65,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "oifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "postrouting",
        "handle": 66,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "oif"
                }
              },
              "right": "lo"
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "postrouting",
        "handle": 67,
        "expr": [
          {
            "masquerade": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "postrouting",
        "handle": 90,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "oifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "postrouting",
        "handle": 91,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "oif"
                }
              },
              "right": "lo"
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "postrouting",
        "handle": 92,
        "expr": [
          {
            "masquerade": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "postrouting",
        "handle": 109,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "oifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "postrouting",
        "handle": 110,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "oif"
                }
              },
              "right": "lo"
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "postrouting",
        "handle": 111,
        "expr": [
          {
            "masquerade": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 68,
        "expr": [
          {
            "jump": {
              "target": "custom-input"
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 69,
        "expr": [
          {
            "match": {
              "op": "in",
              "left": {
                "ct": {
                  "key": "state"
                }
              },
              "right": "invalid"
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 70,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "iifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "match": {
              "op": "==",
              "left": {
                "payload": {
                  "protocol": "udp",
                  "field": "dport"
                }
              },
              "right": 68
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 71,
        "expr": [
          {
            "match": {
              "op": "in",
              "left": {
                "ct": {
                  "key": "state"
                }
              },
              "right": [
                "established",
                "related"
              ]
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 72,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "iifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "l4proto"
                }
              },
              "right": "icmp"
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 73,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "iif"
                }
              },
              "right": "lo"
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 74,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "iifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "reject": {
              "type": "icmp",
              "expr": "host-prohibited"
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 75,
        "expr": [
          {
            "counter": {
              "packets": 22933,
              "bytes": 1253148
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 93,
        "expr": [
          {
            "jump": {
              "target": "custom-input"
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 94,
        "expr": [
          {
            "match": {
              "op": "in",
              "left": {
                "ct": {
                  "key": "state"
                }
              },
              "right": "invalid"
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 95,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "iifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "match": {
              "op": "==",
              "left": {
                "payload": {
                  "protocol": "udp",
                  "field": "dport"
                }
              },
              "right": 68
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 96,
        "expr": [
          {
            "match": {
              "op": "in",
              "left": {
                "ct": {
                  "key": "state"
                }
              },
              "right": [
                "established",
                "related"
              ]
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 97,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "iifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "l4proto"
                }
              },
              "right": "icmp"
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 98,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "iif"
                }
              },
              "right": "lo"
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 99,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "iifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "reject": {
              "type": "icmp",
              "expr": "host-prohibited"
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 100,
        "expr": [
          {
            "counter": {
              "packets": 1648,
              "bytes": 90088
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 112,
        "expr": [
          {
            "jump": {
              "target": "custom-input"
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 113,
        "expr": [
          {
            "match": {
              "op": "in",
              "left": {
                "ct": {
                  "key": "state"
                }
              },
              "right": "invalid"
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 114,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "iifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "match": {
              "op": "==",
              "left": {
                "payload": {
                  "protocol": "udp",
                  "field": "dport"
                }
              },
              "right": 68
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 115,
        "expr": [
          {
            "match": {
              "op": "in",
              "left": {
                "ct": {
                  "key": "state"
                }
              },
              "right": [
                "established",
                "related"
              ]
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 116,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "iifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "l4proto"
                }
              },
              "right": "icmp"
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 117,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "iif"
                }
              },
              "right": "lo"
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 118,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "iifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "reject": {
              "type": "icmp",
              "expr": "host-prohibited"
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "input",
        "handle": 119,
        "expr": [
          {
            "counter": {
              "packets": 947,
              "bytes": 51684
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "forward",
        "handle": 76,
        "expr": [
          {
            "jump": {
              "target": "custom-forward"
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "forward",
        "handle": 138,
        "expr": [
          {
            "jump": {
              "target": "qubes-routing-manager"
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "forward",
        "handle": 77,
        "expr": [
          {
            "match": {
              "op": "in",
              "left": {
                "ct": {
                  "key": "state"
                }
              },
              "right": "invalid"
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "forward",
        "handle": 78,
        "expr": [
          {
            "match": {
              "op": "in",
              "left": {
                "ct": {
                  "key": "state"
                }
              },
              "right": [
                "established",
                "related"
              ]
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "forward",
        "handle": 79,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "oifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "counter": {
              "packets": 105866,
              "bytes": 6788164
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "forward",
        "handle": 101,
        "expr": [
          {
            "jump": {
              "target": "custom-forward"
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "forward",
        "handle": 102,
        "expr": [
          {
            "match": {
              "op": "in",
              "left": {
                "ct": {
                  "key": "state"
                }
              },
              "right": "invalid"
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "forward",
        "handle": 103,
        "expr": [
          {
            "match": {
              "op": "in",
              "left": {
                "ct": {
                  "key": "state"
                }
              },
              "right": [
                "established",
                "related"
              ]
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "forward",
        "handle": 104,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "oifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "forward",
        "handle": 120,
        "expr": [
          {
            "jump": {
              "target": "custom-forward"
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "forward",
        "handle": 121,
        "expr": [
          {
            "match": {
              "op": "in",
              "left": {
                "ct": {
                  "key": "state"
                }
              },
              "right": "invalid"
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "forward",
        "handle": 122,
        "expr": [
          {
            "match": {
              "op": "in",
              "left": {
                "ct": {
                  "key": "state"
                }
              },
              "right": [
                "established",
                "related"
              ]
            }
          },
          {
            "accept": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "forward",
        "handle": 123,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "meta": {
                  "key": "oifgroup"
                }
              },
              "right": 2
            }
          },
          {
            "counter": {
              "packets": 0,
              "bytes": 0
            }
          },
          {
            "drop": null
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "dnat-dns",
        "handle": 88,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "payload": {
                  "protocol": "ip",
                  "field": "daddr"
                }
              },
              "right": "10.139.1.1"
            }
          },
          {
            "match": {
              "op": "==",
              "left": {
                "payload": {
                  "protocol": "udp",
                  "field": "dport"
                }
              },
              "right": 53
            }
          },
          {
            "dnat": {
              "addr": "10.250.7.2"
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "dnat-dns",
        "handle": 89,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "payload": {
                  "protocol": "ip",
                  "field": "daddr"
                }
              },
              "right": "10.139.1.1"
            }
          },
          {
            "match": {
              "op": "==",
              "left": {
                "payload": {
                  "protocol": "tcp",
                  "field": "dport"
                }
              },
              "right": 53
            }
          },
          {
            "dnat": {
              "addr": "10.250.7.2"
            }
          }
        ]
      }
    },
    {
      "rule": {
        "family": "ip",
        "table": "qubes",
        "chain": "qubes-routing-manager",
        "handle": 140,
        "expr": [
          {
            "match": {
              "op": "==",
              "left": {
                "payload": {
                  "protocol": "ip",
                  "field": "daddr"
                }
              },
              "right": "10.250.4.13"
            }
          },
          {
            "accept": null
          }
        ]
      }
    }
  ]
}
"""


def mock_collector():
    final_args = []

    class MockedPopen:
        def __init__(self, args, **kwargs):
            final_args.append(args)
            self.args = args
            self.returncode = 0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, value, traceback):
            pass

        def communicate(self, input=None, timeout=None):
            stdout = ALREADY_ADDED
            stderr = ""
            self.returncode = 1
            return stdout, stderr

        def poll(self):
            return 0

    return final_args, MockedPopen


def test_forwarding_does_not_add_twice():
    args, MockedPopen = mock_collector()
    expected = [
        ["nft", "-n", "-j", "list", "table", "ip", "qubes"],
    ]
    with mock.patch("subprocess.Popen", MockedPopen):
        setup_plain_forwarding_for_address("10.250.4.13", True, 4)

    assert args == expected