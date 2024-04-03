from flask import Flask, Response, render_template
from flask_cors import CORS
import serial
import threading
from threading import Thread
import json
import time
import numpy as np
import socket

app = Flask(__name__)
CORS(app)

serial_port = None
status = 0
current_status = 0

def open_serial_port():
    global serial_port
    serial_port = serial.Serial('com3', 230400, timeout=10, stopbits=1)

def close_serial_port():
    global serial_port
    if serial_port:
        serial_port.close()
        serial_port = None

def read_serial_data():
    global serial_port
    global status
    global current_status
    if not serial_port:
        open_serial_port()
    print(serial_port)
    while True:
        try:
            data = serial_port.readline().decode('utf-8').strip()
            if data == "STOP":
                status = 1
                current_status = 1
            elif data == "BALANCE":
                status = 0
                current_status = 0
            elif data == "UNBALANCE":
                status = 0
                current_status = 2
            yield f'data: {json.dumps({"data": data})}\n\n'
        except serial.serialutil.SerialException as e:
            print(f"Error reading from serial port: {e}")
            close_serial_port()
            open_serial_port()

def get_network_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        network_ip = s.getsockname()[0]
        s.close()
        return network_ip
    except Exception as e:
        return None

@app.route('/')
def index():
    network_ip = get_network_ip()
    return render_template('main_dashboard.html', network_ip=network_ip)

@app.route('/data')
def serial_data():
    return Response(read_serial_data(), content_type='text/event-stream')

def generate_time_dependent_cosine_values():
    x_values = np.arange(1, 25)
    global status
    while True:
        current_time = time.time()
        if status == 1:
            y_values = np.zeros_like(x_values)
        elif status == 0:
            y_values = np.cos(x_values + current_time)
                            
        data_dict = {"x": x_values.tolist(), "y": y_values.tolist()}
        json_data = json.dumps(data_dict)
        yield f"data: {json_data}\n\n"
        time.sleep(1)
            
@app.route('/graph')
def graph():
    return Response(generate_time_dependent_cosine_values(), content_type='text/event-stream')

def current_graph():
    xValues = [0,10,30,40,50]
    global current_status
    while True:
        if current_status == 1:
            yValues = [0, 0, 0, 0, 0]
        elif current_status == 0:
            yValues = [0.16, 0.16, 0.16, 0.16, 0.16]
        elif current_status == 2:
            yValues = [0.20, 0.20, 0.20, 0.20, 0.20]
        current_dict = {"x": xValues, "y": yValues}
        json_current = json.dumps(current_dict)
        yield f"data: {json_current}\n\n"
        time.sleep(1)

@app.route('/currentgraph')
def currentgraph():
    return Response(current_graph(), content_type='text/event-stream')

@app.route('/input')
def input_data():
    def generate():
        while True:
            data = serial_port.readline().decode('utf-8').strip()
            if data == "BALANCE":
                yield f'data: {json.dumps({"voltage": 36.0, "current": 0.16})}\n\n'
            elif data == "UNBALANCE":
                yield f'data: {json.dumps({"voltage": 36.0, "current": 0.20})}\n\n'
            elif data == "STOP":
                yield f'data: {json.dumps({"voltage": 36.0, "current": 0.00})}\n\n'
            time.sleep(1)

    return Response(generate(), content_type='text/event-stream')


@app.route('/speed')
def speed_data():
    def generate():
        while True:
            data = serial_port.readline().decode('utf-8').strip()
            if data == "BALANCE":
                yield f'data: {json.dumps({"speed": 1500})}\n\n'
            elif data == "UNBALANCE":
                yield f'data: {json.dumps({"speed": 1490})}\n\n'
            elif data == "STOP":
                yield f'data: {json.dumps({"speed": 0})}\n\n'
            time.sleep(1)

    return Response(generate(), content_type='text/event-stream')

if __name__ == '__main__':
    serial_thread = threading.Thread(target=read_serial_data)
    serial_thread.daemon = True
    serial_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)