#!/bin/bash
service plymouth stop
service plymouth-start stop
service apache2 stop
service network-manager stop
service systemd-networkd stop
LLXUP='/sbin/lliurex-up -u -s -n'

KWIN=$(which kwin)
xinit $KWIN -- :0 vt1 &
export DISPLAY=:0
sleep 3
/usr/share/llx-upgrade-release/bkgimg.py &
hostname lliurex.net
/usr/share/llx-upgrade-release/fakenet.py &
hostname lliurex.net
echo $(date)>/home/lliurex/up.log
$LLXUP 
echo $?>>/home/lliurex/up.log
echo "------">>/home/lliurex/up.log

rm /etc/apt/apt.conf 2>/dev/null
echo -n "" > /etc/apt/sources.list
apt clean
repoman-cli -e 0 -y
kdialog --title "Lliurex Release Upgrade" --msgbox "Upgrade ended. Press to reboot"  && systemctl reboot 
