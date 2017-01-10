# IOTAP-project

Python code creating a IBMIOTF device. 
Thread that connects to an arduino through USB receiving distance information. 
Thread that connects to IBM Bluemix service receiving movement info from a eg. phone connected to a bracelet sending gestures.

# Running instructions using virtualenv
Requirements: virtualenv installed
Run the following steps:

1. mkdir myproject
2. cd myproject
3. virtualenv venv
4. On mac:
    . venv/bin/activate
   On Windows:
    venv\Scripts\activate

5. pip install -r requirements.txt

6 Then you start with: 
    python sockets.py 