from .file_get_contents import file_get_contents

import re
import os.path
import logging
from pathlib import Path

from typing import Any, Dict, Type

from nornir.core.inventory import (
    Hosts,
    Groups,
    Host,
    Group,
    Inventory,
    Defaults,
    ConnectionOptions,
    HostOrGroup,
    ParentGroups
)

logger = logging.getLogger(__name__)


def _get_connection_options(data: Dict[str, Any]) -> Dict[str, ConnectionOptions]:
    return {cn: ConnectionOptions(
            hostname=c.get("hostname"),
            port=c.get("port"),
            username=c.get("username"),
            password=c.get("password"),
            platform=c.get("platform"),
            extras=c.get("extras"),
            ) for cn, c in data.items()}


def _get_defaults(data: Dict[str, Any]) -> Defaults:
    return Defaults(
        hostname=data.get("hostname"),
        port=data.get("port"),
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        data=data.get("data"),
        connection_options=_get_connection_options(data.get("connection_options", {})),
    )


def _get_inventory_element(
    typ: Type[HostOrGroup], data: Dict[str, Any], name: str, defaults: Defaults
) -> HostOrGroup:
    return typ(
        name=name,
        hostname=data.get("hostname"),
        port=data.get("port"),
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        data=data.get("data"),
        groups=data.get("groups"),
        defaults=defaults,
        connection_options=_get_connection_options(data.get("connection_options", {})),
    )


class RancidInventory():
    rancid_path = ""

    def __init__(self, **kwargs):
        # If the rancid path its not passed through, or it doesnt exist, bail out
        if "rancid_path" not in kwargs.keys() or os.path.exists(kwargs["rancid_path"]) is False:
            raise FileNotFoundError

        self.rancid_path = kwargs["rancid_path"]

    def load(self) -> Inventory:
        # Load the information from the rancid path
        rancid_inventory = self.load_rancid_data(self.rancid_path)
        defaults = {}

        return Inventory(hosts=rancid_inventory.hosts, groups=rancid_inventory.groups, defaults=defaults)

    def load_rancid_data(self, rancid_path):
        # Load the info from rancid_path/var/{group}/router.db
        rancid_config = self.process_rancid_config(rancid_path)

        # Load the info from cloginrc
        cloginrc = self.process_cloginrc(rancid_path / Path(".cloginrc"))

        hosts_dict = {}

        for host in cloginrc:
            if host in rancid_config["hosts"]:
                hosts_dict[host] = {**rancid_config["hosts"][host], **cloginrc[host]}

        hosts = Hosts()
        for n, h in hosts_dict.items():
            hosts[n] = _get_inventory_element(Host, h, n, {})

        groups = Groups()
        for group in rancid_config['groups']:
            groups[group] = _get_inventory_element(Group, {'name': group}, group, {})

        for g in groups.values():
            g.groups = ParentGroups([groups[g] for g in g.groups])

        for h in hosts.values():
            h.groups = ParentGroups([groups[g] for g in h.groups])

        return Inventory(hosts=hosts, groups=groups, defaults=Defaults)

    def process_rancid_config(self, rancid_path: Path):
        """Reads the rancid.conf config file and parses the groups. From there, it will walk through those groups and find their respective router.db file to import the devices themselves"""

        rancid_conf = rancid_path / Path("etc") / Path("rancid.conf")

        # Read that in to a variable
        config = file_get_contents(rancid_conf)

        # Initialize empty RANCID groups variable
        groups = {}

        # Initialize empty return value
        rancid_config = {}

        # Walk the rancid config for interesting things we care about
        for line in config:
            # The list of groups we need to monitor in the rancid.conf
            if "LIST_OF_GROUPS" in line:

                # Split out the key-value pair
                line_bits = line.split("=")
                # Remove some quotes, and split the value of line_bits (not key) by " " to return a list of groups
                groups_list = re.sub('"', "", line_bits[1]).split(" ")

                # convert to a dictionary
                for group in groups_list:
                    groups[group] = {'name': group}

        # Do we have any groups?
        if not groups:
            raise "Abort - Couldnt get the LIST_OF_GROUPS parsed from rancid.conf"

        rancid_config["hosts"] = {}
        rancid_config["groups"] = groups

        # Now that we have groups, now we have to walk through their router.db files to get the devices
        for group in groups:
            # Set a variable with the full file path
            group_file_path = rancid_path / Path("var") / Path(group) / Path("router.db")

            # Keep on moving if its false
            if os.path.exists(group_file_path) is False:
                continue

            # Contents of router.db file
            routersdb = file_get_contents(group_file_path)
            for router_line in routersdb:
                try:
                    router_info = router_line.split(";")
                    host = router_info[0]
                    platform = router_info[1]
                    status = router_info[2]
                except Exception as e:
                    print("Skipping this one " + router_line)
                    continue

                if self.process_platform_map(platform) and status == "up":
                    # If there is a platform do it, otherwise just get the hell out.. it will break!
                    rancid_config["hosts"][host] = {}
                    rancid_config["hosts"][host]["name"] = host
                    rancid_config["hosts"][host]["hostname"] = host
                    rancid_config["hosts"][host]["platform"] = self.process_platform_map(platform)
                    rancid_config["hosts"][host]["groups"] = []
                    rancid_config["hosts"][host]["groups"].append(group)

        return rancid_config

    def process_platform_map(self, platform):
        if platform == "juniper":
            return "junos"
        if platform == "cisco":
            return "ios"

        return False

    def process_cloginrc(self, cloginrc_filename):
        data = {}

        clogin_data = file_get_contents(cloginrc_filename)

        for line in clogin_data:
            newline = re.sub(" +", " ", line.replace("\t", " "))
            if "add user" in newline:
                line_bits = newline.split(" ")

                line_bits.reverse()

                add = line_bits.pop()
                user = line_bits.pop()
                host = line_bits.pop()
                username = line_bits.pop()

                if host not in data:
                    data[host] = {}
                    data[host]["hostname"] = host

                data[host]["username"] = username
            elif "add password" in newline:
                line_bits = newline.split(" ")

                line_bits.reverse()

                add = line_bits.pop()
                user = line_bits.pop()
                host = line_bits.pop()
                password = line_bits.pop()

                if host not in data:
                    data[host] = {}
                    data[host]["hostname"] = host

                data[host]["password"] = password

        return data
