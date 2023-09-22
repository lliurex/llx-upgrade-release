#!/bin/bash
xinit lliurex-up $* -- :0 vt$XDG_VTNR 
while [ ! -e /tmp/.updateEnd ] 
do
	sleep 10
done

