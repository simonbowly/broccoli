apt-get -y install python3 python3-pip git net-tools
mkdir -p /usr/local/src
rm -rf /usr/local/src/broccoli
git clone git@192.168.1.101:simonbowly/broccoli.git /usr/local/src/broccoli
pip3 install /usr/local/src/broccoli --upgrade
broccoli-update master
