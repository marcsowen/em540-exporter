#!/usr/bin/python3 -u

import time

from prometheus_client import start_http_server, Gauge
from pymodbus.client import ModbusSerialClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

volts_l_n = Gauge('em540_volts_l_n', 'Volts line to neutral', ['phase'])
volts_l_l = Gauge('em540_volts_l_l', 'Volts line to line', ['phase'])
amps = Gauge('em540_amps', 'Amps line', ['phase'])
watts = Gauge('em540_watts', 'Watts line', ['phase'])
va = Gauge('em540_va', 'VA line', ['phase'])
var = Gauge('em540_var', 'Var line', ['phase'])
pf = Gauge('em540_pf', 'Power factor line', ['phase'])
wh = Gauge('em540_wh', 'Energy (Wh)', ['phase'])
freq = Gauge('em540_hz', 'Line frequency')

if __name__ == '__main__':
    print("EM540 exporter v0.2\n")
    serial_port = '/dev/ttyUSB_em540'
    baud_rate = 115200
    rs485_slave = 1
    server_port = 3725

    print("Serial port: " + str(serial_port))
    print("Port       : " + str(server_port) + "\n")

    client = ModbusSerialClient(port=serial_port, baudrate=baud_rate)
    start_http_server(server_port)

    while True:
        response = client.read_holding_registers(0x0000, 50, rs485_slave)
        decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.Big, wordorder=Endian.Little)

        volts_l_n.labels(phase='L1').set(decoder.decode_32bit_int() / 10)
        volts_l_n.labels(phase='L2').set(decoder.decode_32bit_int() / 10)
        volts_l_n.labels(phase='L3').set(decoder.decode_32bit_int() / 10)

        volts_l_l.labels(phase='L1').set(decoder.decode_32bit_int() / 10)
        volts_l_l.labels(phase='L2').set(decoder.decode_32bit_int() / 10)
        volts_l_l.labels(phase='L3').set(decoder.decode_32bit_int() / 10)

        amps.labels(phase='L1').set(decoder.decode_32bit_int() / 1000)
        amps.labels(phase='L2').set(decoder.decode_32bit_int() / 1000)
        amps.labels(phase='L3').set(decoder.decode_32bit_int() / 1000)

        watts.labels(phase='L1').set(decoder.decode_32bit_int() / 10)
        watts.labels(phase='L2').set(decoder.decode_32bit_int() / 10)
        watts.labels(phase='L3').set(decoder.decode_32bit_int() / 10)

        va.labels(phase='L1').set(decoder.decode_32bit_int() / 10)
        va.labels(phase='L2').set(decoder.decode_32bit_int() / 10)
        va.labels(phase='L3').set(decoder.decode_32bit_int() / 10)

        var.labels(phase='L1').set(decoder.decode_32bit_int() / 10)
        var.labels(phase='L2').set(decoder.decode_32bit_int() / 10)
        var.labels(phase='L3').set(decoder.decode_32bit_int() / 10)

        volts_l_n.labels(phase='sys').set(decoder.decode_32bit_int() / 10)
        volts_l_l.labels(phase='sys').set(decoder.decode_32bit_int() / 10)
        watts.labels(phase='sys').set(decoder.decode_32bit_int() / 10)
        va.labels(phase='sys').set(decoder.decode_32bit_int() / 10)
        var.labels(phase='sys').set(decoder.decode_32bit_int() / 10)

        pf.labels(phase='L1').set(decoder.decode_16bit_int() / 1000)
        pf.labels(phase='L2').set(decoder.decode_16bit_int() / 1000)
        pf.labels(phase='L3').set(decoder.decode_16bit_int() / 1000)

        response = client.read_holding_registers(0x0500, 28, rs485_slave)
        decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.Big, wordorder=Endian.Little)

        wh.labels(phase='sys').set(decoder.decode_64bit_int())
        decoder.skip_bytes(24)
        wh.labels(phase='L1').set(decoder.decode_64bit_int())
        wh.labels(phase='L2').set(decoder.decode_64bit_int())
        wh.labels(phase='L3').set(decoder.decode_64bit_int())

        response = client.read_holding_registers(0x053c, 2, rs485_slave)
        decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.Big, wordorder=Endian.Little)

        freq.set(decoder.decode_32bit_int() / 1000)

        time.sleep(1)
