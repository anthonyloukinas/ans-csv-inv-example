# Ansible CSV Inventory Plugin Example

A simple example of using python's CSV library combined with an Ansible Inventory Plugin, to parse CSV files to build out dynamic inventories. This can be used ad-hoc, in a Playbook, or added as an `Inventory Source` in AWX/AAP.

## Requirements

- ansible >= 2.12
- python >= 3.9

## Quick Start

1. Clone the repository
2. (Optional): Add your own .csv file to `inventories/`, also create an Ansible Inventory file (plugin configuration)

```yml
---
plugin: csv
source: "inventories/windows.csv"

# add an attribute to each host based on a conditional
compose:
  ansible_become: ansible_network_os == "eos" # if ansible_network_os == "eos" then ansible_become: true

# build dynamic groups based on csv columns
keyed_groups:
  # {{ PREFIX}} {{ SEPARATOR }} {{ KEY }}
  - key: ServerTeam
    prefix: ""
    separator: ""
  - key: OS
    prefix: ""
    separator: ""

# allow the csv to contain `vars:xxx` values which reference these
vars:
  ansible_user: "{{ lookup('env', 'ansible_user') }}"
  ansible_password: "{{ lookup('env', 'ansible_password') }}"
  ansible_become_pass: "{{ lookup('env', 'ansible_become_pass') }}"

# add an attribute to each host if it's not in the csv
defaults:
  ansible_connection: local # Remove this line if you want to connect to the hosts

# in case the CSV columns don't match what we need
# Example: ColumnValue: AnsibleVariableName
# column_replace:
  # OS: ansible_host
...
```

3. Update ansible.cfg to Enable the new CSV inventory plugin
```ini
[inventory]
enable_plugins = csv
```

4. Check your inventory
```sh
ansible-inventory -i inventories/windows.csv.yaml --list
```

You should see a similar result:

```
{
    "IIS": {
        "hosts": [
            "hcv444ppmsdaa02"
        ]
    },
    "MSSQL": {
        "hosts": [
            "hcv444ppmsdaa03"
        ]
    },
    "ST6": {
        "hosts": [
            "hcv444ppmsdaa02",
            "hcv444ppmsdaa03"
        ]
    },
    "_meta": {
        "hostvars": {
            "hcv444ppmsdaa02": {
                "AdditionalGroups": "IIS",
                "Agency": "Transportation",
                "CMDB-Support": "EOC-DOC Server Team 6",
                "Environment": "Production",
                "Owner": "aloukinas",
                "ServerTeam": "ST6",
                "Status": "Operational",
                "System": "ATMS",
                "ansible_connection": "local",
                "ansible_host": "Windows"
            },
            "hcv444ppmsdaa03": {
                "AdditionalGroups": "MSSQL",
                "Agency": "Transportation",
                "CMDB-Support": "EOC-DOC Server Team 6",
                "Environment": "Production",
                "Owner": "aloukinas",
                "ServerTeam": "ST6",
                "Status": "Operational",
                "System": "ATMS",
                "ansible_connection": "local",
                "ansible_host": "Windows"
            }
        }
    },
    "all": {
        "children": [
            "ungrouped",
            "ST6",
            "IIS",
            "MSSQL"
        ]
    }
}
```

5. (Optional): Try out a playbook using a limit

example.yml
```yml
---
- name: Example playbook
  hosts: all
  gather_facts: false

  tasks:
    - name: Print the hostname
      ansible.builtin.debug:
        msg: "Hostname is {{ inventory_hostname }}"
...
```

```
ansible-playbook -i inventories/windows.csv.yaml -l IIS playbooks/example.yml
```

Result:
```
PLAY [Example playbook] *****************************

TASK [Print the hostname] ***************************
ok: [hcv444ppmsdaa02] => {
    "msg": "Hostname is hcv444ppmsdaa02"
}

PLAY RECAP ******************************************
hcv444ppmsdaa02            : ok=1    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

## Usage

```sh
# List inventory hosts and groups
ansible-inventory -i inventories/windows.csv.yaml --list

# Run ping against Group of Hosts
ansible -i inventories/windows.csv.yaml -m ping ST6

# Run command against All Windows hosts, EXCEPT those in the IIS group
ansible -i inventories/windows.csv.yaml -m command -a "cat /etc/redhat-release" 'Windows:!IIS'

# Run command against specific hosts
ansible -i inventories/windows.csv.yaml -m command -a "cat /etc/redhat-release" host1,host2,host3

# Run command against multiple groups
ansible -i inventories/windows.csv.yaml -m command -a "cat /etc/redhat-release" IIS:MSSQL

# Run command against an intersection of groups: All hosts in ST6 that are ALSO in MSSQL
ansible -i inventories/windows.csv.yaml -m command -a "cat /etc/redhat-release" 'ST6:&MSSQL'
```

### Debugging options

Add `-vvvv` to your commands to get debugging information about which line you're having errors with.

## Additional Documentation

- Ansible Limit Patterns: https://docs.ansible.com/ansible/latest/inventory_guide/intro_patterns.html#common-patterns
- Ansible Inventory Plugins: https://docs.ansible.com/ansible/latest/plugins/inventory.html
- Ansible Inventory Plugin Development: 
- Ansible.cfg Configuration Options: https://docs.ansible.com/ansible/latest/reference_appendices/config.html

## Credits

- Original repository example: https://github.com/nmake/inventory
- Modified by: Anthony Loukinas @ Red Hat
