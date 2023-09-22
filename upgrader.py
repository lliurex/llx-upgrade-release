#!/bin/bash
sleep 1
service plymouth stop
service plymouth-start stop
llxup='/sbin/lliurex-up -u -s -n'
xinit $llxup $* -- :0 vt1 &
sleep 2
DISPLAY=:0 QT_QPA_PLATFORM=linuxfb kdialog --title "Lliurex Release Upgrade" --msgbox "Setting up things. Wait for Lliurex Up"
sleep 7
service plymouth stop
service plymouth-start stop
chvt 1
while [ ! -e /tmp/.updateEnd ] 
do
	echo "WAIT"
	sleep 10
done
kdialog --title "Lliurex Release Upgrade" --msgbox "Press to reboot"  
systemctl reboot
