#!/bin/bash
service plymouth stop
service plymouth-start stop
service apache2 stop
service network-manager stop
service systemd-networkd stop
systemctl stop network.target
LLXUP='/sbin/lliurex-up -u -s -n'
LLXUP_TOKEN="/var/run/disableMetaProtection.token"
LLXUP_SOURCES="/etc/apt/lliurexup_sources.list"
HOSTS=/etc/hosts
touch $LLXUP_TOKEN
UPGRADER="/usr/share/llx-upgrade-release/bkgfixer.py"

error()
{
	kdialog --title "Lliurex Release Upgrade" --msgbox "Upgrade ended with errors.<br>A terminal will be executed. Don't reboot till the system gets fixed"
	konsole || xterm
}

#Protect sources.list
cp /etc/apt/sources.list $LLXUP_SOURCES
#Fake host
#echo "127.0.0.1 lliurex.net" >> $HOSTS
xinit $UPGRADER -- :0 vt4 &
sleep 1
export DISPLAY=:0
KWIN=$(which kwin)
$KWIN &
$LLXUP
ERR=$?
if [[ $ERR -eq 0 ]]
then
	error 
fi
echo -n "" > /etc/apt/sources.list
repoman-cli -e 0 -y
cp /etc/apt/sources.list $LLXUP_SOURCES
rm /etc/apt/apt.conf 2>/dev/null
apt clean
kdialog --title "Lliurex Release Upgrade" --msgbox "Upgrade ended. Press to reboot"  && systemctl reboot 
