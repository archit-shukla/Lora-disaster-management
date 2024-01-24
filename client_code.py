import serial
import time
import threading
from queue import Queue
from datetime import datetime

def read_serial_port(port, data_queue, edge_name, baud_rate=115200,sleep_time=1 ):
    
    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
        # print(f"Connected to {port} at {baud_rate} baud")
        while True:
            data = ser.readline().decode('utf-8', 'ignore').strip()
            if data is not '':
                # print(data)
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                formatted_data = f"{timestamp} - {edge_name} - {data}"
                data_queue.put(formatted_data)
                print(f"Data from {port}: {formatted_data}")
            time.sleep(sleep_time)
    except serial.SerialException as e:
        print(f"Error: {e}")
    finally:
        ser.close()

def create_read_thread(port, queue, edge_name, baud_rate=115200,sleep_time=1):
    thread = threading.Thread(target=read_serial_port, args=(port, queue, edge_name, baud_rate,sleep_time))
    thread.start()
    return thread

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
            print("Response:", response)
            if response.startswith('radio_rx'):
                received_data = ''.join([chr(int(response[i:i+2], 16)) for i in range(10, len(response), 2)])
                print("Received data:", received_data)
            break

def read_trigger(ser):
    while True:
        print("Infiinite wait")
        send_command(ser, 'mac pause\r\n')
        send_command(ser, f'radio rx 0\r\n')
        response = ser.readline().decode().strip()
        if response:
            print("Response:", response)
            if response.startswith('radio_rx'):
                received_data = ''.join([chr(int(response[i:i+2], 16)) for i in range(10, len(response), 2)])
                print("Received data:", received_data)
                break

def setup_lora(com_port):
    ser = serial.Serial(com_port, 57600)
    send_command(ser, 'sys reset\r\n')
    send_command(ser, 'radio set mod lora\r\n')
    send_command(ser, 'radio set freq 915000000\r\n')
    send_command(ser, 'radio set pwr 14\r\n')
    send_command(ser, 'radio set sf sf12\r\n')
    send_command(ser, 'radio set rxbw 125\r\n')
    return ser

def send_lora_message(ser, message):
    hex_message = "".join(hex(ord(c))[2:] for c in message)
    print(message)
    send_command(ser, 'mac pause\r\n')
    send_command(ser, f'radio tx {hex_message}\r\n')
    read_responses(ser)
    send_command(ser, 'mac resume\r\n')

def send_messages_from_queue(data_queue, ser):
    if not data_queue.empty():
        message = data_queue.get()
        # print(message)
        send_lora_message(ser, message)
   

if __name__ == "__main__":
    serial_port1 = '/dev/ttyUSB3'
    serial_port2 = '/dev/ttyACM1'
    com_port = '/dev/ttyUSB1' 
    data_queue1 = Queue()
    data_queue2 = Queue()
    
     
    lora_ser = setup_lora(com_port)
    read_trigger(lora_ser)

    create_read_thread(serial_port1, data_queue1, "Edge 1")
    create_read_thread(serial_port2, data_queue2, "Edge 2",9600,3)

     # Update with the correct serial port
    
    while True:
        # print(data_queue1)
        send_messages_from_queue(data_queue1, lora_ser)
        send_messages_from_queue(data_queue2, lora_ser)
      
