import socket
import threading
import logging
import time
from logging.handlers import RotatingFileHandler
from modbus_protocol import *

class ModbusClient(object):
    
    def __init__(self, *params):
        self.__adu = ADU()
        self.__receivedata = bytearray()
        self.__transactionIdentifier = 0
        self.__unitIdentifier = 0xFF
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
        
        print("ModbusTCP client class initialized")
        logging.debug("ModbusTCP client class initialized")

    def connect(self):
        if self.__tcpClientSocket is not None:
            self.__tcpClientSocket.settimeout(5)
            self.__tcpClientSocket.connect((self.__ipAddress, self.__port))
            self.__connected = True
            self.__thread = threading.Thread(target=self.__listen, args=())
            self.__thread.start()
            print(f"Modbus client connected to TCP network, IP Address: {self.__ipAddress}, Port: {self.__port}.")
            logging.info(f"Modbus client connected to TCP network, IP Address: {self.__ipAddress}, Port: {self.__port}.")

    def __listen(self):
        self.__stoplistening = False
        self.__receivedata = bytearray()
        try:
            while not self.__stoplistening:
                if len(self.__receivedata) == 0:
                    self.__receivedata = bytearray()
                    if self.__tcpClientSocket is not None:
                        self.__receivedata = self.__tcpClientSocket.recv(256)
        except socket.timeout:
            self.__receivedata = None

    def close(self):
        if self.__tcpClientSocket is not None:
            self.__stoplistening = True
            self.__tcpClientSocket.shutdown(socket.SHUT_RDWR)
            self.__tcpClientSocket.close()
        self.__connected = False
        print("Modbus client connection closed.")
        logging.info("Modbus client connection closed.")

    def execute_command(self, starting_address, quantity=0, function_code=FunctionCode.READ_HOLDING_REGISTERS, values=None):
        self.__adu.mbap_header.transaction_identifier += 1
        
        if ((starting_address > 65535) | (quantity > 125)) & (function_code == FunctionCode.READ_HOLDING_REGISTERS):
            raise ValueError("Starting address must be 0 - 65535; quantity must be 0 - 125")
        
        self.__adu.pdu.function_code = function_code
        self.__adu.mbap_header.length = 6
        
        if function_code == FunctionCode.WRITE_MULTIPLE_REGISTERS:
            self.__adu.mbap_header.length = len(values) * 2 + 7

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

        if self.__tcpClientSocket is not None:
            self.__tcpClientSocket.send(self.__adu.build_modbus_tcp_frame())
            self.__receivedata = bytearray()
            try:
                while len(self.__receivedata) == 0:
                    time.sleep(0.001)
            except Exception:
                raise Exception('Read Timeout')
            self.__adu.decode(bytearray(self.__receivedata))
        
        if function_code == FunctionCode.READ_HOLDING_REGISTERS:
            return_value = list()
            for i in range(0, quantity):
                return_value.append((self.__adu.pdu.data[i * 2 + 1] << 8) + self.__adu.pdu.data[i * 2 + 2])
            return return_value
        
    def read_holding_registers(self, starting_address, quantity):
        starting_address = f"0x{starting_address:04X}"
        print(f"Request to Read Holding Registers (FC03), starting address: {starting_address}, quantity: {quantity}")
        logging.info(f"Request to Read Holding Registers (FC03), starting address: {starting_address}, quantity: {quantity}")
        
        return_value = self.execute_command(starting_address, quantity, FunctionCode.READ_HOLDING_REGISTERS)
        formatted_values = ' '.join([f"0x{value:04X}" for value in return_value])
        print(f"Response to Holding Registers (FC03), values: {formatted_values}")
        logging.info(f"Response to Holding Registers (FC03), values: {formatted_values}")
        return return_value       
    
    def write_single_register(self, starting_address, value):
        starting_address = f"0x{starting_address:04X}"
        print(f"Request to write single register (FC06), starting address: {starting_address}, value: {value}")
        logging.info(f"Request to write single register (FC06), starting address: {starting_address}, value: {value}")
        return_value = self.execute_command(starting_address, function_code=FunctionCode.WRITE_SINGLE_REGISTER, values=value)
        return return_value
    
    def write_multiple_registers(self, starting_address, values):
        starting_address = f"0x{starting_address:04X}"
        print(f"Request to write multiple registers (FC16), starting address: {starting_address}, values: {values}".format(str(starting_address)), str(hex(values)))
        logging.info(f"Request to write multiple registers (FC16), starting address: {starting_address}, values: {values}".format(str(starting_address), str(hex(values))))
        return_value = self.execute_command(starting_address, function_code=FunctionCode.WRITE_MULTIPLE_REGISTERS,values=values)
        return return_value
    
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

    @property
    def debug(self):
        """
        Enables/disables debug mode
        """
        return self.__debug

    def is_connected(self):
        """
        Returns true if a connection has been established
        """
        return self.__connected    

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
    modbus_client = ModbusClient('192.168.88.100', 502)
    #modbus_client.debug = True
    #modbus_client.logging_level = logging.DEBUG
    #modbus_client.connect()
    #counter = 0
    #while (1):
    #    counter = counter + 1
    #    modbus_client.unitidentifier = 1
    #    registers = [1,2,3,4,5,6,7,8,9]
    #    modbus_client.write_multiple_registers(1, registers)
    #    modbus_client.write_single_coil(1,1)
    #    modbus_client.write_single_coil(8, 0)
    #    modbus_client.write_single_register(8, 4711)
    #    modbus_client.write_multiple_registers(8, [4711, 4712])
    #    modbus_client.write_multiple_coils(2, [True, True])
    #    print(modbus_client.read_discreteinputs(1, 1))
    #    print(modbus_client.read_coils(0, 14))
    #    print(modbus_client.read_holdingregisters(0, 14))
    #modbus_client.close()