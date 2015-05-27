LXC-manager
-----------------
lxc-ui.py is user interface for managing linux containers.  
It has simple design and a lot of functionality.
Using lxc-ui.py you can navigate through list of containers, create, stop, destroy,..
freeze, unfreeze, connect to terminal, rename or clone containers
UI is created using curses library and looks almost like midnight commander.
It can be used on server with very strict security policy. When external access is not allowed.  

INSTALATION
------------------
```
apt-get update
apt-get install python3-lxc
apt-get install git
git clone https://github.com/pymag09/lxc-ui.git
sudo ./lxc-ui.py
```

UNPRIVILEGED CONTAINERS
------------------
```
sudo apt-get update
sudo apt-get install -y cgmanager-utils lxc
mkdir ~/.config && mkdir ~/.config/lxc
```
Create default.conf file with the following content:
```
lxc.network.type = veth
lxc.network.link = lxcbr0
lxc.network.flags = up
lxc.network.hwaddr = 00:16:3e:xx:xx:xx
lxc.id_map = u 0 100000 65536
lxc.id_map = g 0 100000 65536
```
And /etc/lxc/lxc-usernet with:
```
<your username> veth lxcbr0 10
```
Next:
```
sudo cgm create all $USER
sudo cgm chown all $USER $(id -u) $(id -g)
cgm movepid all $USER $$
```

ENVIRONMENT
-----------------
Ubuntu is recommended for running lxc-ui.py.  
Tested on ubuntu 14.04. It has all that you need to run lxc manager in the repository.  


IMPORTANT
-----------------
If you have found any bugs please report it https://github.com/pymag09/lxc-ui/issues  
All previous commits are here: https://github.com/pymag09/lxc-ui/commits/master  
In case of serious problem with bugs don't hesitate to switch to previous commit