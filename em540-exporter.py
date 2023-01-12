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

device_dict = {
    0x06d0: 'EM530DINAV53XS1X',
    0x06d1: 'EM530DINAV53XS1PFA',
    0x06d2: 'EM530DINAV53XS1PFB',
    0x06d3: 'EM530DINAV53XS1PFC',
    0x06e0: 'EM540DINAV23XS1X',
    0x06e1: 'EM540DINAV23XS1PFA',
    0x06e2: 'EM540DINAV23XS1PFB',
    0x06e3: 'EM540DINAV23XS1PFC'
}

measuring_system_dict = {
    0: '3Pn',
    1: '3P',
    2: '2P'
}

measuring_mode_dict = {
    0: 'A mode (absolute)',
    1: 'B mode (counters accumulation by phase)',
    2: 'C mode (bidirectional)'
}

if __name__ == '__main__':
    print("EM540 exporter v0.2\n")
    serial_port = '/dev/ttyUSB_em540'
    baud_rate = 115200
    rs485_slave = 1
    server_port = 3725

    print("Serial port  :", str(serial_port))
    print("Port         :", str(server_port))

    client = ModbusSerialClient(port=serial_port, baudrate=baud_rate)

    response = client.read_holding_registers(0x000b, 1, rs485_slave)
    print("Device       :", device_dict[response.getRegister(0)])

    response = client.read_holding_registers(0x5000, 8, rs485_slave)
    decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.Big, wordorder=Endian.Little)

    print("Serial       :", decoder.decode_string(13).decode('ascii'))
    print("Year         :", response.getRegister(7))

    response = client.read_holding_registers(0x0302, 1, rs485_slave)
    fw_minor = response.getRegister(0) & 0x000f
    fw_major = (response.getRegister(0) & 0x00f0) >> 4
    revision = (response.getRegister(0) & 0xff00) >> 8
    print("Firmware     : {0}.{1}".format(fw_major, fw_minor))
    print("Revision     :", revision)

    response = client.read_holding_registers(0x1002, 1, rs485_slave)
    print("Meas. system :", measuring_system_dict[response.getRegister(0)])

    reponse = client.read_holding_registers(0x1103, 1, rs485_slave)
    print("Meas. mode   :", measuring_mode_dict[response.getRegister(0)])

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
