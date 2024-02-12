#! /bin/bash
echo ${1}
#convert WSL-path to Win-path 
file=`echo ${1}| sed -e "s/^file:\/\///"`
echo $(wslpath -w ${file})
#MicrosoftEdge
#/mnt/c/Users/USER/AppData/Local/Microsoft/WindowsApps/MicrosoftEdge.exe $(wslpath -w ${file})
#cmd=$(wslpath 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')
#echo ${cmd}
#${cmd} $(wslpath -w ${file})
/mnt/c/"Program Files (x86)"/Microsoft/Edge/Application/msedge.exe $(wslpath -w ${file})
