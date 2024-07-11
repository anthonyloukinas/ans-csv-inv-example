# Ansible CSV Inventory Plugin Example

## Requirements

- ansible >= 2.12

## Usage

### List Inventory Hosts
ansible-inventory -i inventories/windows.csv.yaml --list

### Run command against Group of Hosts
ansible -i inventories/windows.csv.yaml -m ping orange

### Debugging options

Add `-vvvv` to your commands to get debugging information about which line you're having errors with.
