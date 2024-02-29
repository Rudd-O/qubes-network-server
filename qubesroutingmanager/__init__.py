#!/usr/bin/python3

import json
import logging
import subprocess

from typing import TypedDict, Any, cast, Literal, Union


ADDRESS_FAMILIES = Union[Literal["ip"], Literal["ip6"]]


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
POSTROUTING_CHAIN_NAME = "postrouting"
ROUTING_MANAGER_CHAIN_NAME = "qubes-routing-manager"
ROUTING_MANAGER_POSTROUTING_CHAIN_NAME = "qubes-routing-manager-postrouting"
NFTABLES_CMD = "nft"


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


def _append_or_insert_rule(
    where: Literal["add"] | Literal["insert"],
    address_family: ADDRESS_FAMILIES,
    table: str,
    chain: str,
    handle: int,
    *rest: str,
) -> None:
    subprocess.check_output(
        [
            NFTABLES_CMD,
            "-n",
            "-j",
            where,
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


def append_rule_after(
    address_family: ADDRESS_FAMILIES, table: str, chain: str, handle: int, *rest: str
) -> None:
    _append_or_insert_rule("add", address_family, table, chain, handle, *rest)


def insert_rule_before(
    address_family: ADDRESS_FAMILIES, table: str, chain: str, handle: int, *rest: str
) -> None:
    _append_or_insert_rule("insert", address_family, table, chain, handle, *rest)


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
        postrouting_chain = [
            x for x in existing_chains if x["name"] == POSTROUTING_CHAIN_NAME
        ][0]
    except IndexError:
        logging.warn(
            "No forward or postrouting chains in table %s, not setting up forwarding",
            TABLE_NAME,
        )
        return

    for chain_name in [
        ROUTING_MANAGER_CHAIN_NAME,
        ROUTING_MANAGER_POSTROUTING_CHAIN_NAME,
    ]:
        chain: None | Chain = None
        try:
            chain = [x for x in existing_chains if x["name"] == chain_name].pop()
        except IndexError:
            pass

        if not chain:
            logging.info(
                "Adding %s chain to table %s and counter to chain",
                chain_name,
                TABLE_NAME,
            )
            add_chain(af, TABLE_NAME, chain_name)
            append_counter_at_end(
                af,
                TABLE_NAME,
                chain_name,
            )

    def is_oifgroup_2(rule):
        return (
            rule["chain"] == forward_chain["name"]
            and len(rule["expr"]) == 3
            and (
                rule["expr"][0].get("match", {}).get("op") == "=="
                and rule["expr"][0]
                .get("match", {})
                .get("left", {})
                .get("meta", {})
                .get("key")
                == "oifgroup"
                and rule["expr"][0].get("match", {}).get("right") == 2
            )
            and (rule["expr"][-1].get("drop", "not none") is None)
        )

    def is_postrouting_masquerade(rule):
        return (
            rule["chain"] == postrouting_chain["name"]
            and len(rule["expr"]) == 1
            and "masquerade" in rule["expr"][0]
        )

    for parent_chain, child_chain_name, previous_rule_detector, insertor in [
        (
            forward_chain,
            ROUTING_MANAGER_CHAIN_NAME,
            is_oifgroup_2,
            insert_rule_before,
        ),
        (
            postrouting_chain,
            ROUTING_MANAGER_POSTROUTING_CHAIN_NAME,
            is_postrouting_masquerade,
            insert_rule_before,
        ),
    ]:
        jump_rule: None | Rule = None
        try:
            jump_rule = [
                x
                for x in existing_rules
                if x["chain"] == parent_chain["name"]
                and x["family"] == af
                and len(x["expr"]) == 1
                and x["expr"][0].get("jump", {}).get("target") == child_chain_name
            ].pop()
        except IndexError:
            pass

        if not jump_rule:
            try:
                previous_rule = [
                    x for x in existing_rules if previous_rule_detector(x)
                ][0]
            except IndexError:
                logging.warn(
                    "Cannot find appropriate previous rule in chain %s of table %s, not setting up forwarding",
                    parent_chain["name"],
                    TABLE_NAME,
                )
            logging.info(
                "Adding rule to jump from chain %s to chain %s in table %s",
                parent_chain["name"],
                child_chain_name,
                TABLE_NAME,
            )
            insertor(
                af,
                TABLE_NAME,
                parent_chain["name"],
                previous_rule["handle"],
                "jump",
                child_chain_name,
            )

    def detect_ip_rule(rule: Rule, chain_name: str, ip: str, mode: str):
        return (
            rule["chain"] == chain_name
            and len(rule["expr"]) == 2
            and rule["expr"][0].get("match", {}).get("op", {}) == "=="
            and rule["expr"][0]["match"]
            .get("left", {})
            .get("payload", {})
            .get("protocol", "")
            == af
            and rule["expr"][0]["match"]["left"]["payload"].get("field", "") == mode
            and rule["expr"][0].get("match", {}).get("right", []) == ip
            and "accept" in rule["expr"][1]
        )

    for chain_name, mode in [
        (ROUTING_MANAGER_CHAIN_NAME, "daddr"),
        (ROUTING_MANAGER_POSTROUTING_CHAIN_NAME, "saddr"),
    ]:
        address_rules = [
            x for x in existing_rules if detect_ip_rule(x, chain_name, source, mode)
        ]

        if enable and not address_rules:
            logging.info(
                "Adding accept rule on chain %s for %s.",
                chain_name,
                source,
            )
            append_rule_at_end(
                af,
                TABLE_NAME,
                chain_name,
                af,
                mode,
                source,
                "accept",
            )
        elif not enable and address_rules:
            logging.info(
                "Removing %s accept rules from chain %s for %s.",
                len(address_rules),
                chain_name,
                source,
            )
            for rule in reversed(sorted(address_rules, key=lambda r: r["handle"])):
                delete_rule(af, TABLE_NAME, chain_name, rule["handle"])
