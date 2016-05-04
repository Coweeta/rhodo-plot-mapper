import serial
import pynmea2

class TruPulseException(Exception):
    """Something wrong from the TruPulse."""


def parse_list_result(match_list, raw_list):
    if len(match_list) != len(raw_list):
        raise Exception('len("{}") != len("{}") ({}, {})'.format(match_list, data_list, len(match_list), len(raw_list)))

    res = {}
    for idx, match in enumerate(match_list):
        data = raw_list[idx]
        if isinstance(match, list):
             key, conv_fn = match
             res[key] = conv_fn(data)
        else:
            if match != data:
                raise Exception('"{}" != "{}" ({})'.format(match, data, idx))

    return res


class TruPulseInterface(object):


    def __init__(self, dev_name, trace=False, timeout=10.0):
        self.timeout = timeout
        self.ser = serial.Serial(port=dev_name, baudrate=38400, timeout=self.timeout)
        self.trace = trace


    def _send_command(self, cmd, expect_okay=True):
        self.ser.flush()

        text = "${}\r\n".format(cmd)

        if self.trace:
            self.ser.timeout = 0.0
            left = self.ser.read(10000)
            if left:
                print "XXX", left
            self.ser.timeout = self.timeout
            print ">>>", text.strip()

        self.ser.write(text)

        if expect_okay:
            ack = self._readline()
            assert ack == "$OK"


    def _readline(self):
        text = self.ser.readline().strip()
        if self.trace:
            print "<<<", text
        return text


    def set_horiz_vector_mode(self):
        self.expected = [
            'T', 'HV',
            ['horz_dist', float], 'M',
            ['azimuth', float], 'D',
            ['incline', float], 'D',
            ['slope', float], 'M'
            ]
        self._send_command('MM,0')

    def set_height_mode(self):
        self.expected = [
            'T', 'HT',
            ['height', float], 'M',
            ]
        self._send_command('MM,4')

    def set_declination(self, dec):
        command = 'DE,{:1.1f}'.format(dec)
        self._send_command(command)

    def set_defaults(self):
        self._send_command('AU,0')  # angles in degrees
        self._send_command('DU,0')  # distances in meters


    def get_voltage(self):
        self._send_command('BV', expect_okay=False)  # angles in degrees
        raw_output = self._readline()
        out_list = raw_output.split(',')
        assert out_list[0] == '$BV'

        return float(out_list[1]) / 1000.0


    def turn_off(self):
        self._send_command('PO', expect_okay=False)
        self.ser.close()

    def get_reading(self):
        self._send_command('GO')
        raw_output = self._readline()
        msg = pynmea2.parse(raw_output)
        return parse_list_result(self.expected, msg.data)


    def stop_measurement(self):
        self._send_command('ST')

if __name__ == "__main__":
    dev_name = "/dev/rfcomm0"
    tp = TruPulseInterface(dev_name, trace=True)
    tp.set_horiz_vector_mode()
    while True:
        inp = raw_input("#: ")
        r = tp.get_reading()
        print r


"""
    def parse_hv_result(msg):

        return parse_lti_result(msg, match)

def parse_id_result(msg):
    match = ['T', 'ID', ['model', str], 'M', ['version', str]]
    return parse_lti_result(msg, match)


def request_
def measure_hv(con):
    ser.flush()
    send_req('GO')
    ser.readline()




    In [16]: s.readline()
Out[16]: '$ID,TP360 MAIN,3.28,07-28-2011\r\n'

In [17]: s.readline()
Out[17]: '$OK\r\n'

In [18]: s.readline()
Out[18]: '$PLTIT,HV,3.00,M,136.60,D,-0.20,D,3.00,M*4A\r\n'

In [19]: s.write('$GO\r\n')
Out[19]: 5

In [20]: s.readline()
Out[20]: '$OK\r\n'

In [21]: s.readline()
Out[21]: '$PLTIT,HV,3.10,M,141.10,D,4.50,D,3.10,M*63\r\n'

s = serial.Serial(dev_name ,38400)

def send(s, cmd):
    s.write('${}\r\n'.format(cmd))

send(s, 'ID')
s.write('$GO')
s.readline()
s.write('$ID')
s.write('$ID\r\n')
s.write('$ID\r\n')
s.readline()
s.write('$GO\r\n')
s.readline()
s.readline()
s.readline()
s.write('$GO\r\n')

data = '$PLTIT,HV,3.00,M,136.60,D,-0.20,D,3.00,M*4A\r\n'


In [23]: msg = pynmea2.parse(data)

In [24]: msg
Out[24]: <ProprietarySentence() data=['T', 'HV', '3.00', 'M', '136.60', 'D', '-0.20', 'D', '3.00', 'M']>

"""
