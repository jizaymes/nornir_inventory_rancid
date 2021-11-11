# nornir-rancid_inventory

This is a really basic plugin for [nornir](https://github.com/nornir-automation/nornir) to use an existing [RANCID](https://www.shrubbery.net/rancid/) installation as inventory for nornir. It will assemble the info from the various rancid router.db files, as well as basic authentication info out of .cloginrc

It gets initialized in the nornir `config.yaml` passing in the path to rancid. An example structure is included in the rancid folder.

```
inventory:
    plugin: "rancid_inventory.rancid_inventory.RancidInventory"
    options:
        rancid_path: "rancid"
```

The included `rancid.py` is an example to walk through your rancid inventory, detecting what groups to look for devices in by checking the rancid_path/etc/rancid.conf config variable `LIST_OF_GROUPS`, ex. `LIST_OF_GROUPS="routers switches firewalls"`
