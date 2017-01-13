# IOTAP-project

Python code creating a IBMIOTF device. 
Thread that connects to an arduino through USB receiving distance information. 
Thread that connects to IBM Bluemix service receiving movement info from a eg. phone connected to a bracelet sending gestures.

# Running instructions using virtualenv
Requirements: virtualenv installed
Run the following steps:

1. `mkdir myproject && cd $_`
2. `virtualenv venv`
3. 
   * On mac: `. venv/bin/activate`
   * On windows: `venv\Scripts\activate`
4. `pip install -r requirements.txt`
5. Then you start with: `python sockets.py`
