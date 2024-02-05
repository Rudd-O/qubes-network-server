#!/usr/bin/python3

import json
import logging
import subprocess

from typing import TypedDict, Any, cast, Literal


ADDRESS_FAMILIES = Literal["ip"] | Literal["ip6"]


class Chain(TypedDict):
    name: str
    family: str
    table: str
    handle: int
    type: str
    hook: str
    prio: int
    policy: str


class Table(TypedDict):
    family: str
    name: str
    handle: int


class Metainfo(TypedDict):
    version: str
    release_name: str
    json_schema_version: int


class Rule(TypedDict):
    family: str
    table: str
    chain: str
    handle: int
    expr: list[dict[str, Any]]


class ChainContainer(TypedDict):
    chain: Chain


class MetainfoContainer(TypedDict):
    metainfo: Metainfo


class TableContainer(TypedDict):
    table: Table


class RuleContainer(TypedDict):
    rule: Rule


class NFTablesOutput(TypedDict):
    nftables: list[ChainContainer | MetainfoContainer | TableContainer | RuleContainer]


ADDRESS_FAMILY_IPV6 = "ip6"
ADDRESS_FAMILY_IPV4 = "ip"
TABLE_NAME = "qubes"
FORWARD_CHAIN_NAME = "forward"
ROUTING_MANAGER_CHAIN_NAME = "qubes-routing-manager"
NFTABLES_CMD = "nft"
ADD_RULE_AFTER_THIS_RULE = "custom-forward"


def get_table(address_family: ADDRESS_FAMILIES, table: str) -> NFTablesOutput:
    return cast(
        NFTablesOutput,
        json.loads(
            subprocess.check_output(
                [NFTABLES_CMD, "-n", "-j", "list", "table", address_family, table],
                text=True,
            )
        ),
    )


def add_chain(address_family: ADDRESS_FAMILIES, table: str, chain: str) -> None:
    subprocess.check_output(
        [
            NFTABLES_CMD,
            "-n",
            "-j",
            "add",
            "chain",
            address_family,
            table,
            chain,
        ],
        text=True,
    )


def append_rule_at_end(
    address_family: ADDRESS_FAMILIES, table: str, chain: str, *rest: str
) -> None:
    subprocess.check_output(
        [
            NFTABLES_CMD,
            "-n",
            "-j",
            "add",
            "rule",
            address_family,
            table,
            chain,
        ]
        + list(rest),
        text=True,
    )


def append_counter_at_end(
    address_family: ADDRESS_FAMILIES, table: str, chain: str, *rest: str
) -> None:
    subprocess.check_output(
        [
            NFTABLES_CMD,
            "-n",
            "-j",
            "add",
            "rule",
            address_family,
            table,
            chain,
            "counter",
        ]
        + list(rest),
        text=True,
    )


def append_rule_after(
    address_family: ADDRESS_FAMILIES, table: str, chain: str, handle: int, *rest: str
) -> None:
    subprocess.check_output(
        [
            NFTABLES_CMD,
            "-n",
            "-j",
            "add",
            "rule",
            address_family,
            table,
            chain,
            "position",
            str(handle),
        ]
        + list(rest),
        text=True,
    )


def delete_rule(
    address_family: ADDRESS_FAMILIES, table: str, chain: str, handle: int
) -> None:
    subprocess.check_output(
        [
            NFTABLES_CMD,
            "-n",
            "-j",
            "delete",
            "rule",
            address_family,
            table,
            chain,
            "handle",
            str(handle),
        ],
        text=True,
    )


def setup_plain_forwarding_for_address(source: str, enable: bool, family: int) -> None:
    logging.info("Handling forwarding for address %s family %s.", source, family)

    af = cast(
        ADDRESS_FAMILIES,
        ADDRESS_FAMILY_IPV6 if family == 6 else ADDRESS_FAMILY_IPV4,
    )

    # table ip qubes {
    #     set downstream {
    #         type ipv4_addr
    #         elements = { 10.137.0.10, 10.250.4.13 }
    #     }
    #     ...
    existing_table_output = get_table(af, TABLE_NAME)
    existing_table_items = existing_table_output["nftables"]

    existing_chains = [x["chain"] for x in existing_table_items if "chain" in x]  # type: ignore
    existing_rules = [x["rule"] for x in existing_table_items if "rule" in x]  # type: ignore

    try:
        forward_chain = [x for x in existing_chains if x["name"] == FORWARD_CHAIN_NAME][
            0
        ]
    except IndexError:
        logging.warn(
            "No forward chain in table %s, not setting up forwarding", TABLE_NAME
        )
        return

    qubes_routing_manager_chain: None | Chain = None
    try:
        qubes_routing_manager_chain = [
            x for x in existing_chains if x["name"] == ROUTING_MANAGER_CHAIN_NAME
        ].pop()
    except IndexError:
        pass

    if not qubes_routing_manager_chain:
        logging.info(
            "Adding %s chain to table %s", ROUTING_MANAGER_CHAIN_NAME, TABLE_NAME
        )
        add_chain(af, TABLE_NAME, ROUTING_MANAGER_CHAIN_NAME)

    qubes_routing_manager_rule: None | Rule = None
    try:
        qubes_routing_manager_rule = [
            x
            for x in existing_rules
            if x["chain"] == forward_chain["name"]
            and x["family"] == af
            and len(x["expr"]) == 1
            and x["expr"][0].get("jump", {}).get("target") == ROUTING_MANAGER_CHAIN_NAME
        ].pop()
    except IndexError:
        pass

    if not qubes_routing_manager_rule:
        try:
            custom_forwarding_rule = [
                x
                for x in existing_rules
                if x["chain"] == forward_chain["name"]
                and len(x["expr"]) == 1
                and x["expr"][0].get("jump", {}).get("target")
                == ADD_RULE_AFTER_THIS_RULE
            ][0]
        except IndexError:
            logging.warn(
                "No state forwarding rule in chain %s of table %s, not setting up forwarding",
                forward_chain["name"],
                TABLE_NAME,
            )
        logging.info(
            "Adding rule to jump to %s to table %s after jump to %s",
            ROUTING_MANAGER_CHAIN_NAME,
            TABLE_NAME,
            ADD_RULE_AFTER_THIS_RULE,
        )
        append_rule_after(
            af,
            TABLE_NAME,
            forward_chain["name"],
            custom_forwarding_rule["handle"],
            "jump",
            ROUTING_MANAGER_CHAIN_NAME,
        )
        append_counter_at_end(
            af,
            TABLE_NAME,
            ROUTING_MANAGER_CHAIN_NAME,
        )

    address_rules = [
        x
        for x in existing_rules
        if x["chain"] == ROUTING_MANAGER_CHAIN_NAME
        and len(x["expr"]) == 2
        and x["expr"][0].get("match", {}).get("op", {}) == "=="
        and x["expr"][0]["match"].get("left", {}).get("payload", {}).get("protocol", "")
        == af
        and x["expr"][0]["match"]["left"]["payload"].get("field", "") == "daddr"
        and x["expr"][0].get("match", {}).get("right", []) == source
        and "accept" in x["expr"][1]
    ]

    if enable and not address_rules:
        logging.info(
            "Adding accept rule on chain %s to allow traffic to %s.",
            ROUTING_MANAGER_CHAIN_NAME,
            source,
        )
        append_rule_at_end(
            af,
            TABLE_NAME,
            ROUTING_MANAGER_CHAIN_NAME,
            af,
            "daddr",
            source,
            "accept",
        )
    elif not enable and address_rules:
        logging.info(
            "Removing %s accept rules from chain %s to stop traffic to %s.",
            len(address_rules),
            ROUTING_MANAGER_CHAIN_NAME,
            source,
        )
        for rule in reversed(sorted(address_rules, key=lambda r: r["handle"])):
            delete_rule(af, TABLE_NAME, ROUTING_MANAGER_CHAIN_NAME, rule["handle"])
