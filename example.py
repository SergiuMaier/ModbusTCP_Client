import modbus_client
import logging

client = modbus_client.ModbusClient('192.168.88.100', 502)
client.connect()

modbus_client.debug = True
modbus_client.logging_level = logging.DEBUG

client.read_holding_registers(0x01FF, 3)
client.read_holding_registers(0x0200, 3)
client.write_multiple_registers(0x01FF, [0XAABB, 0XCCDD, 0XEEFF])

client.close()

#numar = 0x0032
#hex_string = "0x{0:04X}".format(numar)
#print("hex:", hex_string)

#starting_address = 0x0087
#quantity = 3
#starting_address = "0x{0:04X}".format(starting_address)
#print("Request to Read Holding Registers (FC03), starting address: {0}, quantity: {1}" .format(str(starting_address), str(quantity)))

#return_value = [0x0032, 0x1023, 0x0432]        
#hex_values = ["0x{0:04X}".format(value) for value in return_value]
#formatted_values = ' '.join(hex_values)
#print("\nResponse to Holding Registers (FC03), values: {0}".format(str(formatted_values)))