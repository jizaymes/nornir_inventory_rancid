# Example script using the nornir rancid_inventory plugin. This will get the config and save it in backups/

from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir_inventory_rancid.rancid_inventory import RancidInventory

if __name__ == '__main__':    
    # Register the Plugin
    InventoryPluginRegister.register('RancidInventory', RancidInventory)

    # Initialize nornir
    nr = InitNornir(config_file="config.yaml")

    print(f"{nr.inventory.hosts}")
    print(f"{nr.inventory.groups}")    