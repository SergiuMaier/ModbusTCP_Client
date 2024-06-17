import modbus_client
import time
import logging

SERVER_NAME = '192.168.88.234'
SERVER_PORT = 502

def main():

    try:
        client = modbus_client.ModbusClient(SERVER_NAME, SERVER_PORT)
        #client.debug = True
        #client.logging_level = logging.DEBUG

        client.connect()

        for i in range(0, 10):
            client.read_holding_registers(0x0097, 4)
            #client.write_multiple_registers(0x01FF, [0XAABB, 0XCCDD, 0XEEFF])
        
        client.close()
    
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()

