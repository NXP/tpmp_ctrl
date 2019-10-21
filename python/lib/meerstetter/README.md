**This directory tpmp-ctrl/python/lib/meerstetter should contain Python interface to discuss with Meerstetter equipment.**

# Implementation example

An example of implementation can be found here: [link to url!](https://github.com/spomjaksilp/pyMeCom)

## Use reference example
It can be used as a reference by doing following:
`cd tpmp-ctrl/python/lib/meerstetter`
`git clone https://github.com/spomjaksilp/pyMeCom`

## Prerequesites:
install python3 needed dependencies
`sudo apt-get install python3-serial`
`sudo apt-get install python3-pip`
`sudo pip3 install PyCRC`

# Testing
## Stand alone test
Set Peltier temperature on thermal bench:
`python3 ./tempcontrol.py tempvalueC`

Test Example, to set Temp to 20°C:
`python3 ./tempcontrol.py 20`

Script will execute, return current value until controller stabilized. Exit program when controller is stable.
## integration test
`python3 ./basicSerialAuto.py myboardconfig.ini`
`Enter command (help: 'cmdlist') or 'exit':readPeltier`
---  1: /dev/ttyUSB2         'FT230X Basic UART'
 'USB VID:PID=0403:6015 SER=DM00U05L LOCATION=1-2'
identify port by hwid:/dev/ttyUSB2
/dev/ttyUSB2
{'target object temperature': (35.0, 'degC'), 'loop status': (2, ''), 'object temperature': (34.99137878417969, 'degC'), 'sink temperature': (23.698699951171875, 'degC'), 'output voltage': (1.3371341228485107, 'V'), 'output current': (0.20631539821624756, 'A')}
Peltier temp is: 34.99


`Enter command (help: 'cmdlist') or 'exit':peltier`
set Peltier: 0403:6015
---  1: /dev/ttyUSB2         'FT230X Basic UART'
 'USB VID:PID=0403:6015 SER=DM00U05L LOCATION=1-2'
identify port by hwid:/dev/ttyUSB2
/dev/ttyUSB2
{'target object temperature': (35.0, 'degC'), 'loop status': (2, ''), 'object temperature': (35.00700378417969, 'degC'), 'sink temperature': (23.6549072265625, 'degC'), 'output voltage': (1.1300997734069824, 'V'), 'output current': (0.1637042611837387, 'A')}
None
query for loop stability, loop is not stable, obj temp: 35.01
query for loop stability, loop is not stable, obj temp: 34.95
query for loop stability, loop is not stable, obj temp: 34.34
.
.
query for loop stability, loop is not stable, obj temp: 31.16
query for loop stability, loop is not stable, obj temp: 30.78
query for loop stability, loop is not stable, obj temp: 30.48
exit program with stability status: is stable
{'target object temperature': (30.0, 'degC'), 'loop status': (2, ''), 'object temperature': (30.241012573242188, 'degC'), 'sink temperature': (27.37054443359375, 'degC'), 'output voltage': (-2.12154483795166, 'V'), 'output current': (-0.38007867336273193, 'A')}
Enter command (help: 'cmdlist') or 'exit':




