#source ./venv/bin/activate
source .setenv
cd src
python3 -V
python3 chart.py ${1} ${2} ${3} ${4} ${5} ${6}
