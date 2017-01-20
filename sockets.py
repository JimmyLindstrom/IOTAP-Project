from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
from datetime import datetime
import threading
import serial.tools.list_ports
import serial
import sys
import os

import ibmiotf.device
import ibmiotf.application



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')


""" -----------------------------------------------
 Class that handles Arduino connection
in a seperate thread, connecting and communicating 
---------------------------------------------------
"""
class Arduino (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.arduino = None

    def run(self):
        for p in list(serial.tools.list_ports.comports()):
            if "Arduino" in p[1]:
                try:
                    self.arduino = serial.Serial(p[0], 9600, timeout=10)
                    print("Connected to " + p[0])
                    break
                except serial.SerialException:
                    print("Couldn't connect to " + p[0])

        if self.arduino is not None:
            self.arduino.close()  # In case the port is already open this closes it.
            self.arduino.open()  # Reopen the port.
            print('Arduino thread started')
            while self.running:
                if stop_running.is_set():
                    self.arduino.close()
                    self.arduino = None
                    self.running = False
                    print("Stoping arduino thread ")
                if self.arduino is not None:
                    data = self.arduino.readline()[:-2]
                data = str(data)
                if data == "Receive" and not receive_movement.is_set():
                    print("Start receiving movements")
                    receive_movement.set()
                    with app.test_request_context('/'):
                        print('user connected')
                        socketio.emit('my response', 'user connected')

                elif data == "Stop" and receive_movement.is_set():
                    print("Stop receiving movements!")
                    receive_movement.clear()
                    user_connect_sent.clear()
            print('EXITING ARDUINO THREAD')

""" -----------------------------------------------
 Class that handles IBM Bluemix connection
in a seperate thread, connecting and communicating 
---------------------------------------------------
"""
class Bluemix (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        
    def run(self):
        print('Bluemix thread started')


        """ method handling the command callbacks from BlueMix """
        def myCommandCallback(cmd):
            print("Command received: %s" % cmd.data['d'])
            data = cmd.data['d']
     
            if 'movement' in data.keys():
                with app.test_request_context('/'):
                    socketio.emit('news', data['movement'])

        # Initialize the device deviceCli. Fetches credentials from config.txt.
        try:
            path = os.path.join(sys.path[0], 'config.txt')
            deviceCliOptions = ibmiotf.device.ParseConfigFile(path)
            deviceCli = ibmiotf.device.Client(deviceCliOptions)
        except Exception as e:
            print("Caught exception connecting device: %s" % str(e))
            sys.exit()

        # Connect device to IBM Bluemix
        deviceCli.connect()
        deviceCli.commandCallback = myCommandCallback

        # User credentials hardcodeded, shold be received by user in proximity
        # in the future!!
        user = "123aa123aa12"

        while self.running:
            if stop_running.is_set():
                self.running = False
                deviceCli.disconnect()
                print("Stoping bluemix thread ")
            else:
                if receive_movement.is_set():
                    if not user_connect_sent.is_set():
                        timestamp = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                        data = { 'user' : user, 'timestamp' : timestamp}
                        def myOnPublishCallback():
                            print("Confirmed event received by IoTF\n" )
                        
                        success = deviceCli.publishEvent("user", "json", data, qos=0, on_publish=myOnPublishCallback)
                        user_connect_sent.set()
                        if not success:
                            print("Not connected to IoTF")

        print('EXITING BLUEMIX THREAD')


"""  Events used to control the threads """
stop_running = threading.Event() # event if threads should stop running
receive_movement = threading.Event() # event if we should receive rmovements
user_connect_sent = threading.Event()  # event if user connect is sent to bluemix


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    global connected_users
    global thread
    global thread_2
    connected_users = connected_users + 1
    print('user %s is connected!' %(connected_users))
    if thread == None:
        thread = Arduino()
        thread.deamon = True
        thread.start()
    if thread_2 == None:
        thread_2 = Bluemix()
        thread_2.deamon = True
        thread_2.start()
    emit('my response', {'data': 'connected'})
       
    
@socketio.on('disconnect')
def handle_disconnect():
    print("IN DISCONNECT!!!!!!!")
    global connected_users
    print('user %s is disconnected!' %(connected_users))
    connected_users = connected_users -1
    if connected_users < 1:
        close_threads()


@socketio.on('exit')
def handle_exit(msg):
    print("Closing threads and server!")
    close_threads()
    socketio.stop()


def send_message(msg) :
    emit('news', msg)


def close_threads():
    print('In close threads!!!')
    stop_running.set()
    global thread
    global thread_2
    thread = None
    thread_2 = None


if __name__ == '__main__':
    thread = None #Arduino thread!
    thread_2 = None # Bluemix thread
    connected_users = 0
    # if thread == None:
    #     thread = 
    #     thread.deamon = True
    #     thread.start()
    # if thread_2 == None:
    #     thread_2 = Bluemix()
    #     thread_2.deamon = True
    #     thread_2.start()
    socketio.run(app)

