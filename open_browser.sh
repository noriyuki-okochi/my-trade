#! /bin/bash
#convert WSL-path to Win-path 
file=`echo ${1}| sed -e "s/^file:\/\///"`
#echo $(wslpath -w ${file})
#MicrosoftEdge
/mnt/c/Users/USER/AppData/Local/Microsoft/WindowsApps/MicrosoftEdge.exe $(wslpath -w ${file})