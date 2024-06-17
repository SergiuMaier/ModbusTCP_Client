import socket
import ssl
import threading
import logging
import time
from logging.handlers import RotatingFileHandler
from modbus_protocol import *

class ModbusClient(object):
    
    def __init__(self, *params):
        self.__adu = ADU()
        self.__receivedata = bytearray()
        self.__last_transaction_id = 0
        #self.__adu.mbap_header.transaction_identifier = 0x0000
        self.__timeout = 5
        self.__tcpClientSocket = None
        self.__connected = False
        self.__logging_level = logging.INFO

        if (len(params) == 2) & isinstance(params[0], str) & isinstance(params[1], int):
            self.__tcpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__ipAddress = params[0]
            self.__port = params[1]
        else:
            raise AttributeError ('Argument must be "str, int" for ModbusTCP.')
        
        print("ModbusTCP client initialized.")
        logging.debug("ModbusTCP client initialized.")

    def connect(self):
        if self.__tcpClientSocket is not None:
            self.__tcpClientSocket.settimeout(5)

            ssl_context = ssl.create_default_context()
            self.__tcpClientSocket = ssl_context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname=self.__ipAddress)

            self.__tcpClientSocket.connect((self.__ipAddress, self.__port))
            self.__connected = True
            
            print(f"Modbus client connected to TCP network, IP Address: {self.__ipAddress}, Port: {self.__port}.")
            logging.info(f"Modbus client connected to TCP network, IP Address: {self.__ipAddress}, Port: {self.__port}.")

    def close(self):
        if self.__tcpClientSocket is not None:
            self.__stoplistening = True
            self.__tcpClientSocket.shutdown(socket.SHUT_RDWR)
            self.__tcpClientSocket.close()
            self.__connected = False
            print("\nModbus client connection closed.")
            logging.info("Modbus client connection closed.")

    def send_and_receive_data(self):
        if self.__tcpClientSocket is not None:
            self.__tcpClientSocket.sendall(self.__adu.build_modbus_tcp_frame())

            response = b""
            self.__tcpClientSocket.settimeout(1)  # Set a timeout for the recv method
            while True:
                try:
                    self.__receivedata = self.__tcpClientSocket.recv(1024)
                    if not self.__receivedata:
                        break
                    response += self.__receivedata
                except socket.timeout:  # Catch a timeout exception
                    break
            self.__adu.decode(bytearray(response))
        
    def execute_command(self, starting_address, quantity=0, function_code=FunctionCode.READ_HOLDING_REGISTERS, values=None):
        self.__last_transaction_id = (self.__last_transaction_id + 1) % 65536
        self.__adu.mbap_header.transaction_identifier = self.__last_transaction_id
        #self.__adu.mbap_header.transaction_identifier += 1
        
        if ((starting_address > 65535) | (quantity > 125)):
            raise ValueError("Starting address must be in between 0 - 0xFFFF; quantity must be in between 0 - 125")
        
        self.__adu.pdu.function_code = function_code
        self.__adu.mbap_header.length = 6
        
        if function_code == FunctionCode.WRITE_MULTIPLE_REGISTERS:
            self.__adu.mbap_header.length = 2 * len(values) + 7

        self.__adu.mbap_header.unit_identifier = 0xFF
        starting_address_lsb = starting_address & 0xFF
        starting_address_msb = (starting_address & 0xFF00) >> 8

        if function_code == FunctionCode.READ_HOLDING_REGISTERS:
            quantity_lsb = quantity & 0xFF
            quantity_msb = (quantity & 0xFF00) >> 8
            self.__adu.pdu.data = bytearray([starting_address_msb, starting_address_lsb, quantity_msb, quantity_lsb])
        elif function_code == FunctionCode.WRITE_SINGLE_REGISTER:
            value_lsb = values & 0xFF
            value_msb = (values & 0xFF00) >> 8
            self.__adu.pdu.data = bytearray([starting_address_msb, starting_address_lsb, value_msb, value_lsb])
        elif function_code == FunctionCode.WRITE_MULTIPLE_REGISTERS:
            quantity_lsb = len(values) & 0xFF
            quantity_msb = (len(values) & 0xFF00) >> 8
            value_to_write = list()
            
            for i in range(0, len(values)):
                value_to_write.append(values[i])
            
            self.__adu.pdu.data = bytearray([starting_address_msb, starting_address_lsb, quantity_msb,quantity_lsb])
            self.__adu.pdu.data.append(len(value_to_write) * 2) # bytecount
            
            for i in range(0, len(value_to_write)):
                self.__adu.pdu.data.append((value_to_write[i] & 0xFF00) >> 8)
                self.__adu.pdu.data.append(value_to_write[i] & 0xFF)

        self.send_and_receive_data()
      
    def log_and_print_registers_values(self, values):
        if values is not None:
            formatted_values = ' '.join([f"0x{value:04X}" for value in values])
            print(f"Response to Holding Registers (FC03), values: {formatted_values}")
            logging.info(f"Response to Holding Registers (FC03), values: {formatted_values}")   

    def read_holding_registers(self, starting_address, quantity):
        str_starting_address = f"0x{starting_address:04X}"
        print(f"\nRequest to Read Holding Registers (FC03), starting address: {str_starting_address}, quantity: {quantity}")
        logging.info(f"Request to Read Holding Registers (FC03), starting address: {str_starting_address}, quantity: {quantity}")
        
        self.execute_command(starting_address, quantity, FunctionCode.READ_HOLDING_REGISTERS)
        #self.log_and_print_registers_values(return_values)    

    def write_single_register(self, starting_address, value):
        str_starting_address = f"0x{starting_address:04X}"
        print(f"\nRequest to write single register (FC06), starting address: {str_starting_address}, value: {value}")
        logging.info(f"Request to write single register (FC06), starting address: {str_starting_address}, value: {value}")
        self.execute_command(starting_address, function_code=FunctionCode.WRITE_SINGLE_REGISTER, values=value)
    
    def write_multiple_registers(self, starting_address, values):
        str_starting_address = f"0x{starting_address:04X}"
        str_values = ' '.join([f"0x{value:04X}" for value in values])
        print(f"\nRequest to write multiple registers (FC16), starting address: {str_starting_address}, values: {str_values}")
        logging.info(f"Request to write multiple registers (FC16), starting address: {str_starting_address}, values: {str_values}")
        self.execute_command(starting_address, function_code=FunctionCode.WRITE_MULTIPLE_REGISTERS,values=values) 

    @property
    def port(self):
        """
        Gets the Port were the Modbus-TCP Server is reachable (Standard is 502)
        """
        return self.__port

    @port.setter
    def port(self, port):
        """
        Sets the Port were the Modbus-TCP Server is reachable (Standard is 502)
        """
        self.__port = port

    @property
    def ipaddress(self):
        """
        Gets the IP-Address of the Server to be connected
        """
        return self.__ipAddress

    @ipaddress.setter
    def ipaddress(self, ipAddress):
        """
        Sets the IP-Address of the Server to be connected
        """
        self.__ipAddress = ipAddress

    @property
    def timeout(self):
        """
        Gets the Timeout
        """
        return self.__timeout

    @timeout.setter
    def timeout(self, timeout):
        """
        Sets the Timeout
        """
        self.__timeout = timeout

    def is_connected(self):
        """
        Returns true if a connection has been established
        """
        return self.__connected    
   
    @property
    def debug(self):
        """
        Enables/disables debug mode
        """
        return self.__debug

    @debug.setter
    def debug(self, debug):
        """
        Enables/disables debug mode
        """
        self.__debug = debug
        if self.__debug:
            logging.getLogger().setLevel(self.__logging_level)
            # Add the log message handler to the logger
            handler1 = logging.handlers.RotatingFileHandler('logdata.txt', maxBytes=2000000, backupCount=5)
            logging.getLogger().addHandler(handler1)
            formatter1 = logging.Formatter("%(asctime)s;%(message)s","%Y-%m-%d %H:%M:%S")
            handler1.setFormatter(formatter1)

    @property
    def logging_level(self):
        """
        Sets the logging level - Default is logging.INFO
        """
        return self.__logging_level

    @logging_level.setter
    def logging_level(self, logging_level):
        """
        Sets the logging level - Default is logging.INFO
        """
        self.__logging_level = logging_level
        logging.getLogger().setLevel(self.__logging_level)

if __name__ == "__main__":
    modbus_client = ModbusClient('192.168.88.234', 502)
    