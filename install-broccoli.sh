apt-get -q -y install python3 python3-pip git net-tools
/usr/bin/pip3 install pip --upgrade
mkdir -p /usr/local/src
rm -rf /usr/local/src/broccoli
git clone git@192.168.1.101:simonbowly/broccoli.git /usr/local/src/broccoli
/usr/local/bin/pip install /usr/local/src/broccoli --upgrade
broccoli-update master
