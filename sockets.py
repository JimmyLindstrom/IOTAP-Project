from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
from datetime import datetime
import threading
import serial.tools.list_ports
import serial
import sys
import os

try:
    import ibmiotf.device
except ImportError:
    import ibmiotf.device


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
                    print_out("Connected to " + p[0])
                    break
                except serial.SerialException:
                    print("Couldn't connect to " + p[0])

        if self.arduino is not None:
            self.arduino.close()  # In case the port is already open this closes it.
            self.arduino.open()  # Reopen the port.
            print_out('Arduino thread started')
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
                    print_out("Start receiving movements")
                    receive_movement.set()
                    with app.test_request_context('/'):
                        print_out('user connected')
                        socketio.emit('news', 'user connected')

                elif data == "Stop" and receive_movement.is_set():
                    print("Stop receiving movements!")
                    receive_movement.clear()
                    user_connect_sent.clear()
            print_out('EXITING ARDUINO THREAD')

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

        # Initialize the device deviceCli.
        try:
            # deviceCliOptions = {"org": organization, "type": deviceType, "id": deviceId, "auth-method": authMethod, "auth-token": authToken}
            path = os.path.join(sys.path[0], 'config.txt')
            deviceCliOptions = ibmiotf.device.ParseConfigFile(path)
            deviceCli = ibmiotf.device.Client(deviceCliOptions)
        except Exception as e:
            print("Caught exception connecting device: %s" % str(e))
            sys.exit()

        # Connect device to IBM Bluemix
        deviceCli.connect()
        deviceCli.commandCallback = myCommandCallback

        user = "123aa123aa12" # DeviceId of the smart wristband in proximity

        counter = 0;
        while self.running:
            if stop_running.is_set():
                self.running = False
                deviceCli.disconnect()
                print("Stoping bluemix thread ")
            else:
                if receive_movement.is_set():
                    if not user_connect_sent.is_set():
                        timestamp = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                        print(timestamp)
                        data = { 'user' : user, 'timestamp' : timestamp}
                        def myOnPublishCallback():
                            print("Confirmed event " + str(counter) +" received by IoTF\n" )
                        
                        success = deviceCli.publishEvent("user", "json", data, qos=0, on_publish=myOnPublishCallback)
                        if not success:
                            print("Not connected to IoTF")
                        user_connect_sent.set()

        print('EXITING BLUEMIX THREAD')


thread = None
thread_2 = None
"""  Events used to control the threads """
stop_running = threading.Event() # event if threads should stop running
receive_movement = threading.Event() # event if we should receive rmovements
user_connect_sent = threading.Event()  # event if user connect is sent to bluemix


@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('a user connected ')
    emit('my response', {'data': 'connected'})
       
    
@socketio.on('disconnect')
def handle_disconnect():
    print('a user disconnected ')

@socketio.on('exit')
def handle_exit(msg):
    print("Closing threads and server!")
    close_threads()
    socketio.stop()

def send_message(msg) :
    emit('news', msg)

def print_out(msg):
    print(msg)

def close_threads():
    print('In close threads!!!')
    stop_running.set()

if __name__ == '__main__':
    if thread == None:
        thread = Arduino()
        thread.deamon = True
        thread.start()
    if thread_2 == None:
        thread_2 = Bluemix()
        thread_2.deamon = True
        thread_2.start()
    socketio.run(app)
