# How to set up a SOL VM using Vagrant

1. Run `vagrant up` in this directory
2. After vagrant completes, run `vagrant ssh` to make sure you can access the VM
and see onos and gurobi folders
3. Go to gurobi.com, make an account and request academic license. You will get
a key
4. On the VM, run `grbgetkey <your key here>`
5. `cd /sol` and make sure you see all the SOL files
6. Install SOL in dev mode using `pip install -e .`
