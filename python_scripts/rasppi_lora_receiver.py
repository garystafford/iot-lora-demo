import logging
import time
from argparse import ArgumentParser
from datetime import datetime

import serial
from colr import color as colr


# LoRa Wi-Fi IoT Sensor Demo
# REYAX RYLR896 transceiver module
# http://reyax.com/wp-content/uploads/2020/01/Lora-AT-Command-RYLR40x_RYLR89x_EN.pdf
# Author: Gary Stafford
# Requirements: python3 -m pip install --user -r requirements.txt
# To Run: python3 ./rasppi_lora_receiver.py /dev/ttyAMA0 115200


def main():
    logging.basicConfig(filename='output.log', filemode='w', level=logging.DEBUG)
    args = get_args()  # get args
    payload = ""

    print("Connecting to REYAX RYLR896 transceiver module...\n")
    serial_conn = serial.Serial(
        port=args.tty,
        baudrate=int(args.baud_rate),
        timeout=5,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )

    if serial_conn.isOpen():
        set_lora_config(serial_conn)
        check_lora_config(serial_conn)

        while True:
            serial_payload = serial_conn.readline()  # read data from serial port
            if len(serial_payload) > 0:
                try:
                    payload = serial_payload.decode(encoding="ASCII")
                except UnicodeDecodeError:  # receiving corrupt data?
                    logging.error("UnicodeDecodeError: {}".format(serial_payload))

                payload = payload[:-2]
                print("\n----------")
                print("Date/Time: {}".format(datetime.now()))
                print("Payload: {}".format(payload))
                try:
                    data = parse_payload(payload)
                    print("Sensor Data: {}".format(data))
                    display_temperature(data[0])
                    display_humidity(data[1])
                    display_pressure(data[2])
                    display_color(data[3], data[4], data[5], data[6])
                except IndexError:
                    logging.error("IndexError: {}".format(payload))
                except ValueError:
                    logging.error("ValueError: {}".format(payload))

            # time.sleep(2) # transmission frequency set on IoT device


def eight_bit_color(value):
    return int(round(value / (4097 / 255), 0))


def celsius_to_fahrenheit(value):
    return (value * 1.8) + 32


def display_color(r, g, b, a):
    print("12-bit Color values (r,g,b,a): {},{},{},{}".format(r, g, b, a))
    r = eight_bit_color(r)
    g = eight_bit_color(g)
    b = eight_bit_color(b)
    a = eight_bit_color(a)  # ambient light intensity

    print(" 8-bit Color values (r,g,b,a): {},{},{},{}".format(r, g, b, a))
    print("RGB Color")
    print(colr("\t\t", fore=(127, 127, 127), back=(r, g, b)))
    print("Light Intensity")
    print(colr("\t\t", fore=(127, 127, 127), back=(a, a, a)))


def display_pressure(value):
    print("Barometric Pressure: {} kPa".format(round(value, 2)))


def display_humidity(value):
    print("Humidity: {}%".format(round(value, 2)))


def display_temperature(value):
    temperature = celsius_to_fahrenheit(value)
    print("Temperature: {}°F".format(round(temperature, 2)))


def get_args():
    arg_parser = ArgumentParser(description="BLE IoT Sensor Demo")
    arg_parser.add_argument("tty", help="serial tty", default="/dev/ttyAMA0")
    arg_parser.add_argument(
        "baud_rate", help="serial baud rate", default=115200)
    args = arg_parser.parse_args()
    return args


def parse_payload(payload):
    # input: +RCV=116,29,23.94|37.71|99.89|16|38|53|80,-61,56
    # output: [23.94, 37.71, 99.89, 16.0, 38.0, 53.0, 80.0]

    payload = payload.split(",")
    payload = payload[2].split("|")
    payload = [float(i) for i in payload]
    return payload


def set_lora_config(serial_conn):
    """Set the AES-128 32 hex digit password for the REYAX RYLR896 transceiver module"""

    serial_conn.write(str.encode(
        "AT+CPIN=92A0ECEC9000DA0DCF0CAAB0ABA2E0EF\r\n"))
    time.sleep(1)
    serial_payload = (serial_conn.readline())[:-2]
    print("AES128 password set?", serial_payload.decode(encoding="utf-8"))


def check_lora_config(serial_conn):
    """Prints out the REYAX RYLR896 transceiver module's configuration"""

    serial_conn.write(str.encode("AT?\r\n"))
    serial_payload = (serial_conn.readline())[:-2]
    print("Module responding?", serial_payload.decode(encoding="utf-8"))

    serial_conn.write(str.encode("AT+ADDRESS?\r\n"))
    serial_payload = (serial_conn.readline())[:-2]
    print("Address:", serial_payload.decode(encoding="utf-8"))

    serial_conn.write(str.encode("AT+VER?\r\n"))
    serial_payload = (serial_conn.readline())[:-2]
    print("Firmware version:", serial_payload.decode(encoding="utf-8"))

    serial_conn.write(str.encode("AT+NETWORKID?\r\n"))
    serial_payload = (serial_conn.readline())[:-2]
    print("Network Id:", serial_payload.decode(encoding="utf-8"))

    serial_conn.write(str.encode("AT+IPR?\r\n"))
    serial_payload = (serial_conn.readline())[:-2]
    print("UART baud rate:", serial_payload.decode(encoding="utf-8"))

    serial_conn.write(str.encode("AT+BAND?\r\n"))
    serial_payload = (serial_conn.readline())[:-2]
    print("RF frequency", serial_payload.decode(encoding="utf-8"))

    serial_conn.write(str.encode("AT+CRFOP?\r\n"))
    serial_payload = (serial_conn.readline())[:-2]
    print("RF output power", serial_payload.decode(encoding="utf-8"))

    serial_conn.write(str.encode("AT+MODE?\r\n"))
    serial_payload = (serial_conn.readline())[:-2]
    print("Work mode", serial_payload.decode(encoding="utf-8"))

    serial_conn.write(str.encode("AT+PARAMETER?\r\n"))
    serial_payload = (serial_conn.readline())[:-2]
    print("RF parameters", serial_payload.decode(encoding="utf-8"))

    serial_conn.write(str.encode("AT+CPIN?\r\n"))
    serial_payload = (serial_conn.readline())[:-2]
    print("AES128 password of the network",
          serial_payload.decode(encoding="utf-8"))


if __name__ == "__main__":
    main()
