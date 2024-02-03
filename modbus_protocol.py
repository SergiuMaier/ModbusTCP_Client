from dataclasses import dataclass
from enum import *
import modbus_exception as Exceptions
import logging

class FunctionCode(IntEnum):
    READ_HOLDING_REGISTERS = 3
    WRITE_SINGLE_REGISTER = 6
    WRITE_MULTIPLE_REGISTERS = 16

class MBAPHeader:
    transaction_identifier: int = 0
    protocol_identifier: int = 0
    length: int = 0
    unit_identifier: int = 0xFF

    def build_frame(self):
        transaction_identifier_lsb = self.transaction_identifier & 0xFF
        transaction_identifier_msb = (self.transaction_identifier & 0xFF00) >> 8
        protocol_identifier_lsb = self.protocol_identifier & 0xFF
        protocol_identifier_msb = ((self.protocol_identifier & 0xFF00) >> 8) 
        length_lsb = self.length & 0xFF
        length_msb = (self.length & 0xFF00) >> 8

        return bytearray([transaction_identifier_msb, transaction_identifier_lsb, protocol_identifier_msb, protocol_identifier_lsb, 
                          length_msb, length_lsb, self.unit_identifier])
    
    def decode(self, data: bytearray):
        self.transaction_identifier = data[1] | (data[0] << 8)
        self.protocol_identifier = data[3] | (data[2] << 8)
        self.transaction_identifier = data[5] | (data[4] << 8)
        self.unit_identifier = data[6]
        
class PDU:
    function_code: FunctionCode = FunctionCode.READ_HOLDING_REGISTERS
    data: bytearray = bytearray()

    def build_frame(self):
        return_value = bytearray()
        return_value.append(self.function_code)
        return_value.extend(self.data)
        return return_value

    def decode(self, data):
        self.function_code = data[0]
        if self.function_code >= 128:
            exception_code = data[1]
            try:
                if exception_code == Exceptions.ExceptionCodes.ILLEGAL_FUNCTION:
                    raise Exceptions.ModbusException("Exception code 01: ILLEGAL FUNCTION. The function code received in the query is not an allowable action for the slave.")
                if exception_code == Exceptions.ExceptionCodes.ILLEGAL_DATA_ADDRESS:
                    raise Exceptions.ModbusException("Exception code 02: ILLEGAL DATA ADDRESS.The data address received in the query is not an allowable address for the slave.")
                if exception_code == Exceptions.ExceptionCodes.ILLEGAL_DATA_VALUE:
                    raise Exceptions.ModbusException("Exception code 03: ILLEGAL DATA VALUE. A value contained in the query data field is not an allowable value for the slave.")
                if exception_code == Exceptions.ExceptionCodes.SLAVE_DEVICE_FAILURE:
                    raise Exceptions.ModbusException("Exception code 04: SLAVE DEVOCE FAILURE. An unrecoverable error occurred while the slave was attempting to perform the requested action.")
            except Exceptions.ModbusException as e:
                print(e.message)
        self.data = data[1:len(data)]

class ADU:
    mbap_header: MBAPHeader = MBAPHeader()
    pdu: PDU = PDU()

    def build_modbus_tcp_frame(self):
        return_value = bytearray()
        return_value.extend(self.mbap_header.build_frame())
        return_value.extend(self.pdu.build_frame())
        print(f"----->Request frame: {return_value.hex(' ').upper()}")
        logging.debug(f"----->Request frame: {return_value.hex(' ').upper()}")
        return return_value
    
    def decode(self, data: bytearray):
        print(f"----->Request frame: {data.hex(' ').upper()}")
        logging.debug(f"----->Request frame: {data.hex(' ').upper()}")
        self.mbap_header.decode(data)
        self.pdu.decode(data[7:len(data)])
