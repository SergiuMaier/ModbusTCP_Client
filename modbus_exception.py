
from enum import *

class ExceptionCodes(IntEnum):
    ILLEGAL_FUNCTION = 1
    ILLEGAL_DATA_ADDRESS = 2
    ILLEGAL_DATA_VALUE = 3
    SLAVE_DEVICE_FAILURE = 4
    ACKNOWLEDGE = 5
    SLAVE_DEVICE_BUSY = 6
    GATEWAY_PATH_UNAVAILABLE = 10

class ModbusException(Exception):
    
    def __init__(self, message):
        """ Exception to be thrown if Modbus Server returns error code "Function Code not executed".
        Attributes:
            message -- explanation of the error
        """
        self.message = message

class ConnectionException(ModbusException):

    def __init__(self, message):
        """ Exception to be thrown if Connection to Modbus device failed.
        Attributes:
            message -- explanation of the error
        """
        self.message = message


class IllegalFunctionCodeException(ModbusException):

    def __init__(self, message):
        """ Exception to be thrown if Modbus Server returns error code "Function code not supported".
        Attributes:
            message -- explanation of the error
        """
        self.message = message

class IllegalDataAddressException(ModbusException):

    def __init__(self, message):
        """ Exception to be thrown if Modbus Server returns error code "starting adddress and quantity invalid".
        Attributes:
            message -- explanation of the error
        """
        self.message = message

class IllegalDataValueException(ModbusException):

    def __init__(self, message):
        """ Exception to be thrown if Modbus Server returns error code "quantity invalid".
        Attributes:
            message -- explanation of the error
        """
        self.message = message

class TimeoutError(ModbusException):
    
    def __init__(self, message):
        """ Exception to be thrown if read times out.
        Attributes:
            message -- explanation of the error
        """
        self.message = message



