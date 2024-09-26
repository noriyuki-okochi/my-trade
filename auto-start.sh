#source ./venv/bin/activate
source .setenv
cd src
python3 -V
#
#  main.py  trade <exchane> <side> <symbol> <size>
#
python3 main.py ${1} ${2} ${3} ${4} ${5} ${6}
