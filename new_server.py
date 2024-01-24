import serial
import time
import threading
from time import sleep
from gpiozero import InputDevice
from datetime import datetime
import firestore as fire
from model import db,app, Edge
import requests
import smbus
import numpy as np
import pandas as pd
import joblib
import RPi.GPIO as GPIO
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings


warnings.filterwarnings("ignore", category=UserWarning)
stop_flag = False

def monitor_earthquakes():
    global stop_flag
    bus = smbus.SMBus(1)
    Device_Address = 0x68 

    def read_acceleration():
        PWR_MGMT_1 = 0x6B
        ACCEL_XOUT_H = 0x3B
        ACCEL_YOUT_H = 0x3D
        ACCEL_ZOUT_H = 0x3F
        bus.write_byte_data(Device_Address, PWR_MGMT_1, 0x00)
        raw_data_x = bus.read_word_data(Device_Address, ACCEL_XOUT_H)
        raw_data_y = bus.read_word_data(Device_Address, ACCEL_YOUT_H)
        raw_data_z = bus.read_word_data(Device_Address, ACCEL_ZOUT_H)
        acc_x = raw_data_x / 16384.0
        acc_y = raw_data_y / 16384.0
        acc_z = raw_data_z / 16384.0
        return acc_x, acc_y, acc_z

    def setup_vibration_sensor():
        VIBRATION_SENSOR_PIN = 4
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(VIBRATION_SENSOR_PIN, GPIO.IN)

    random_forest_model = joblib.load('../finalized_model.pkl')
    data = pd.read_csv('../Data.csv')
    training_data = data.drop(data.columns[data.columns.str.contains('Unnamed')], axis=1)
    X_train = training_data.drop(columns=['Result'])
    scaler = StandardScaler()
    scaler.fit(X_train)

    setup_vibration_sensor()

    while not stop_flag:
        acc_x, acc_y, acc_z = read_acceleration()
        vibration_detected = GPIO.input(4)
        accelerometer_data = np.array([[acc_x, acc_y, acc_z]])
        accelerometer_data_scaled = scaler.transform(accelerometer_data)
        ml_prediction = random_forest_model.predict(accelerometer_data_scaled)

        if ml_prediction == 1 and vibration_detected == 1:
            print("Earthquake detected!")
            stop_flag = True
            break


def send_command(ser, command):
    if isinstance(command, str):
        command = command.encode()
    ser.write(command)
    response = ser.readline().decode().strip()
    print("Response:", response)

def read_responses(ser):
    while True:
        response = ser.readline().decode().strip()
        if response:
            if response.startswith('radio_rx'):
                received_data = ''.join([chr(int(response[i:i+2], 16)) for i in range(10, len(response), 2)])
                storeInDB(received_data)
            else:
                print("Response:", response)
            break

def setup_lora(ser):
    send_command(ser, 'sys reset\r\n')
    send_command(ser, 'radio set mod lora\r\n')
    send_command(ser, 'radio set freq 915000000\r\n')
    send_command(ser, 'radio set pwr 20\r\n')
    send_command(ser, 'radio set sf sf12\r\n')
    send_command(ser, 'radio set rxbw 250\r\n')
    return ser

def send_lora_message(ser, message):
    hex_message = "".join(hex(ord(c))[2:] for c in message)
    print(message)
    send_command(ser, 'mac pause\r\n')
    send_command(ser, f'radio tx {hex_message}\r\n')
    read_responses(ser)
    send_command(ser, 'mac resume\r\n')

def receive_data(ser):
    print("Now receiving Data")
    send_command(ser,'mac pause\r\n')
    send_command(ser,'radio rx 0\r\n')
    read_responses(ser)

def storeInDB(data):

    # Define the URL for the Flask server
    url = 'http://172.20.10.2:5000/add_data'

    timestamp, edge_name, data = data.split(',')


    # Now you have three separate variables
    # print("Timestamp:", timestamp)
    # print("Edge Name:", edge_name)
    # print("Data:", data)

    # Data for the new Edge
    new_edge_data = {
        'data': data,
        'device_id': edge_name,
        'timestamp': timestamp  # Use the desired timestamp value
    }

    # Send a POST request to add the new Edge
    response = requests.post(url, json=new_edge_data)

    # Print the response
    print(response.json())



def monitor_and_break_on_rain(pin):
    global stop_flag
    sensor = InputDevice(pin)

    while not stop_flag:
        if sensor.is_active:
            print('Dry')
            time.sleep(5)
        else:
            print("Rain detected. Breaking loop.")
            stop_flag = True
            break

def sync_data():
    index = 1 
    time.sleep(30)
    while True:
        print("in sync:  ",index)

        index = fire.fetchFromDB(index)
        
        time.sleep(10)


if __name__ == "__main__":
    earthquake_thread = threading.Thread(target=monitor_earthquakes)
    rain_thread = threading.Thread(target=monitor_and_break_on_rain, args=(17,)) 
    
    
    earthquake_thread.start()
    rain_thread.start()

    earthquake_thread.join()
    rain_thread.join()

    ser = serial.Serial('/dev/ttyUSB0', 57600) 
    lora_ser = setup_lora(ser)
    command = 'Trigger'
    send_lora_message(ser, command)

    sync_thread =threading.Thread(target=sync_data)
   
    sync_thread.start()
    while True:
        receive_data(ser)
    sync_thread.join()
        

