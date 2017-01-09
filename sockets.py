from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from time import sleep
from threading import Thread
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
socketio = SocketIO(app)
thread = None
thread_2 = None

receive_movement = False

""" -----------------------------------------------
 Class that handles Arduino connection
in a seperate thread, connecting and communicating 
---------------------------------------------------
"""
class Arduino (Thread):
    arduino = None
    def __init__(self):
        Thread.__init__(self)
        self.running = True

    def end(arg):
        running = False
        

    def run(self):
        print_out('Arduino thread started')
        arduino = None
        for p in list(serial.tools.list_ports.comports()):
            print_out(p[0])
            if "Arduino" in p[1]:
                try:
                    arduino = serial.Serial(p[0], 9600, timeout=10)
                    print_out("Connected to " + p[0])
                    break
                except serial.SerialException:
                    print("Couldn't connect to " + p[0])

        if arduino is not None:
            arduino.close()  # In case the port is already open this closes it.
            arduino.open()  # Reopen the port.
            moves = ['up', 'down', 'right', 'left', 'tilt-right', 'tilt-left']
            count = 0
            while self.running:
                data = arduino.readline()[:-2]
                data = str(data)
                if data == "Receive":
                    global receive_movement
                    receive_movement = True
                    sleep(1)
                    # print_out(moves[count])
                    # old_count = count;
                    # count = (count + 1) % len(moves)
                    # with app.test_request_context('/'):
                    #     print_out('before emit!!!')
                    #     socketio.emit('news', moves[old_count])


                elif data == "Stop":
                    # print_out("Stop receiving movements")
    
                    sleep(1)


class Bluemix (Thread):

    def __init__(self):
        Thread.__init__(self)
        self.running = True

    def end(arg):
        running = False
        
    def run(self):
        print('Bluemix thread started')

        organization = "zx1tf2"
        deviceType = "Computer"
        deviceId = "112233445566"
        authMethod = "token"
        authToken = "aOj?zxZY+KtZdUix+C"

        def myCommandCallback(cmd):
            print_out("Command received: %s" % cmd.data['d'])
            data = cmd.data['d']
            print(cmd)
            for key in data.keys():
                print('key= ', key)
            try:
                print_out(data['movement'])
            except KeyError:
                print("KEYERROR!!")

            if cmd.command == "setInterval":
                if 'interval' not in cmd.data:
                    print_out("Error - command is missing required information: 'interval'")
                else:
                    interval = cmd.data['interval']
            elif cmd.command == "print":
                if 'message' not in cmd.data:
                    print_out("Error - command is missing required information: 'message'")
                else:
                    print_out(cmd.data['message'])
            elif 'movement' in data.keys():
                print_out("WE HAVE MOVEMENTS!!!!!!!!")
                with app.test_request_context('/'):
                    print('before emit!!!')
                    socketio.emit('news', data['movement'])

        # Initialize the device deviceCli.
        try:
            deviceCliOptions = {"org": organization, "type": deviceType, "id": deviceId, "auth-method": authMethod, "auth-token": authToken}
            deviceCli = ibmiotf.device.Client(deviceCliOptions)
        except Exception as e:
            print_out("Caught exception connecting device: %s" % str(e))
            sys.exit()

        # Connect and sends a user event 5 times 
        deviceCli.connect()
        deviceCli.commandCallback = myCommandCallback

        users = ['jimmy', 'william', 'elias', 'dennis', 'mikael']

        counter = 0;
        # success = False
        while self.running:
           
            data = { 'user' : users[counter], 'x' : counter}
            def myOnPublishCallback():
                print_out("Confirmed event " + str(counter) +" received by IoTF\n" )

            # global success
            # if not success:
            success = deviceCli.publishEvent("user", "json", data, qos=0, on_publish=myOnPublishCallback)
            sleep(2)
            if not success:
                print("Not connected to IoTF")

            counter = (counter + 1) % len(users)




@app.route('/')
def index():
    
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    global thread
    global thread_2
    if thread == None:
        thread = Arduino()
        thread.deamon = True
        thread.start()
    if thread_2 == None:
        thread_2 = Bluemix()
        thread_2.start()
    print('a user connected ')
    
    emit('my response', {'data': 'connected'})
       
    
@socketio.on('disconnect')
def handle_disconnect():
    print('a user disconnected ')

@socketio.on('exit')
def handle_exit(msg):
    print('exit pressed')
    thread.running = False
    thread_2.runnin = False
    sys.exit()
    

def send_message(msg) :
    emit('news', msg)

def print_out(msg):
    print(msg)


if __name__ == '__main__':
    
    socketio.run(app)