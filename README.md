## List Inventory Hosts
ansible-inventory -i inventories/windows.csv.yaml --list

## Run command against Group of Hosts
ansible -i inventories/windows.csv.yaml -m ping orange
