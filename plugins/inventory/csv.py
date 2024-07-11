# csv.py - Ansible Inventory Plugin for CSV files
# Docs: https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html

from ansible.plugins.inventory import (
    BaseInventoryPlugin,
    Constructable,
    expand_hostname_range,
    detect_range,
)
# from ansible.inventory.group import to_safe_group_name
import csv


DOCUMENTATION = """
    name: name.inventory.csv
    plugin_type: inventory
    short_description: Use a CSV file as an inventory source
    description:
        - Use a CSV file as an inventory source
    extends_documentation_fragment:
      - constructed
    options:
        column_replace:
            description: Replace a column name in the csv with an alternate name
            type: dict
        defaults:
            description: Assign attributes to hosts when not in the CSV file
            type: dict
        plugin:
            description: token that ensures this is a source file for the 'csv' plugin
            required: True
            choices: ['csv']
        vars:
            description: Use variables to provide CSV values
            type: dict
"""
EXAMPLES = """
# sample CSV file
# host,os,ansible_user,ansible_password,ansible_become_pass,site,groups
# nxos101,nxos,vars:ansible_user,vars:ansible_password,vars:ansible_become_pass,my_lab,red blue
# nxos102,nxos,vars:ansible_user,vars:ansible_password,vars:ansible_become_pass,my_lab,blue yellow
# nxos103,nxos,vars:ansible_user,vars:ansible_password,vars:ansible_become_pass,my_lab,red blue
# nxos104,nxos,vars:ansible_user,vars:ansible_password,vars:ansible_become_pass,my_lab,blue yellow
# eos10[1:4],eos,vars:ansible_user,vars:ansible_password,vars:ansible_become_pass,my_lab,orange red
# vyos10[1:4],vyos,vars:ansible_user,vars:ansible_password,vars:ansible_become_pass,my_lab,orange red


# nmake_inventory_csv.yaml

plugin: csv
source: "/home/user/github/test_csv_inventory/inventory.csv"

# add an attribute to each host based on a conditional
compose:
  ansible_become: ansible_network_os == "eos"

# build dynamic groups based on csv columns
keyed_groups:
  - key: site
    prefix: site
  - key: ansible_network_os
    prefix: ""
    separator: ""

# allow the csv to contain `vars:xxx` values which reference these
vars:
  ansible_user: "{{ lookup('env', 'ansible_user') }}"
  ansible_password: "{{ lookup('env', 'ansible_password') }}"
  ansible_become_pass: "{{ lookup('env', 'ansible_become_pass') }}"

# add an attribute to each host if it's not in the csv
defaults:
  ansible_connection: network_cli

# in case the CSV columns don't match what we need
column_replace:
  os: ansible_network_os
 """


class InventoryModule(BaseInventoryPlugin, Constructable):

    NAME = "csv"

    def verify_file(self, path):
        """ return true/false if this is possibly a valid file for this plugin to consume """
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(
                ("csv.yaml", "csv.yml")
            ):
                valid = True
        return valid

    # @staticmethod
    # def custom_sanitization(self, name):
    #     return to_safe_group_name(name, replacer='')

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path, cache)

        # self._sanitize_group_name = self.custom_sanitization

        config = self._read_config_data(path)
        strict = self.get_option("strict")

        input_file = csv.DictReader(open(config["source"]))

        # For each entry in the CSV file
        for entry in input_file:
            hostvars = {}
            groups = []

            # Expand hostname ranges, Example: vyos10[1:4]
            if detect_range(entry["HostName"]):
                hosts = expand_hostname_range(entry["HostName"])
            else:
                hosts = [entry["HostName"]]

            # Will be a single host, or multiple hosts if a range
            for host in hosts:
                self.inventory.add_host(host) # Add the host to the inventory

                # For each column in the CSV entry
                # k = column name, v = column value
                for k, v in entry.items():
                    # If the column is not 'HostName', or additional Keys, add it to the hostvars
                    if k not in ["HostName"]:
                        if v.startswith("vars:"):
                            varval = v.split("vars:")[1]
                            v = config["vars"].get(varval)
                        if k in config.get("column_replace", {}):
                            add_key = config["column_replace"][k]
                        else:
                            add_key = k
                        hostvars[add_key] = v

                    # If the column is 'groups', split the value into a list
                    if k == "AdditionalGroups":
                        groups = v.split(" ")

                for k, v in config.get("defaults", {}).items():
                    if k not in hostvars:
                        hostvars[k] = v

                for k, v in hostvars.items():
                    self.inventory.set_variable(host, k, v)

                # Create variables using Jinja2 expressions
                self._set_composite_vars(
                    self.get_option("compose"), hostvars, host, strict=strict
                )
                self._add_host_to_composed_groups(
                    self.get_option("groups"), hostvars, host, strict=strict
                )
                self._add_host_to_keyed_groups(
                    self.get_option("keyed_groups"),
                    hostvars,
                    host,
                    strict=strict,
                )

                for group in groups:
                    self.inventory.add_group(group=group)
                    self.inventory.add_host(group=group, host=host)
