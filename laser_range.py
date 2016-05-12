"""Interface to Laser Technologies Inc. TruPulse 360R laser range finder.

Allows control and interrogation of the 360R.

Works with the Bluetooth interface; may work with the RS232 interface too.

Requires the pynmea2 module to decypher the NMEA0183 compliant response strings.
Requires the pyserial module to access the serial interface.

The URL for the product is:
http://www.lasertech.com/TruPulse-Laser-Rangefinder.aspx

The interface is defined in the LTI TruPulse 360R User's Manual
(First Edition (c) 2011 p/n 0144860); "LTI TruPulse 360 R UM.1.pdf"
In particular Section 8 - Serial Data Interface, page 42


"""
import re
import serial
import pynmea2

class TruPulseException(Exception):
    """Something wrong from the TruPulse."""


def parse_list_result(match_list, raw_list):
    """Checks that a list of values matches the form specified in a format list.

    Entries in the match_list can either be tuples or single values.  If a
    single value, e.g. a string or integer, then the corresponding entry in the
    raw_list must match exactly.  For tuple items, the corresponding raw_list
    entry is converted and added to the results dictionary that is returned.

    Tuple entries consist of two elements: the key name to be used in the result
    and the function to call to convert the raw_list item.

    Example:
    parse_list_result(
        ['first:', ('1st', int), 'second:', ('2nd', float)],
        ['first:', '555', 'second:', '1.23']
        )
    would return {'1st': 555, '2nd': 1.23}.
    If elements 0 and 2 were not 'first:' and 'second:' respectively then an
    exception is thrown.  Exceptions thrown by the conversion functions are not
    caught.
    """
    if len(match_list) != len(raw_list):
        raise Exception('len("{}") != len("{}") ({}, {})'.format(match_list, data_list, len(match_list), len(raw_list)))

    res = {}
    for idx, match in enumerate(match_list):
        data = raw_list[idx]
        if isinstance(match, tuple):
             key, conv_fn = match
             res[key] = conv_fn(data)
        else:
            if match != data:
                raise Exception('"{}" != "{}" ({})'.format(match, data, idx))

    return res


class TruPulseInterface(object):


    def __init__(self, dev_name, trace=False, timeout=20.0):
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
            ('horz_dist', float), 'M',
            ('azimuth', float), 'D',
            ('incline', float), 'D',
            ('slope', float), 'M'
            ]
        self._send_command('MM,0')

    def set_height_mode(self):
        """Tell instrument to switch to height measuring mode.

        When get_reading() is run the returned result will be a dictionary with
        the single entry, 'height', which is the computed height of the target
        in meters.
        """
        self.expected = [
            'T', 'HT',
            ('height', float), 'M',
            ]
        self._send_command('MM,4')

    def set_declination(self, dec):
        """Program the angle between True North and Magnetic North.

        This is given as the number of degrees that Magnetic North is west of
        True North (for the current location).
        """
        command = 'DE,{:1.1f}'.format(dec)
        self._send_command(command)


    def set_defaults(self):
        """Specify we use meters and degrees for all measurements."""
        self._send_command('TM,0')  # Target Mode is "normal" (single shot).
        self._send_command('AU,0')  # angles in degrees
        self._send_command('DU,0')  # distances in meters


    def get_voltage(self):
        """Reads the battery voltage from the unit.

        Returns the potential in volts as a float.

        The warning level is 2.15V.
        """
        self._send_command('BV', expect_okay=False)  # angles in degrees
        raw_output = self._readline()
        out_list = raw_output.split(',')
        assert out_list[0] == '$BV'

        return float(out_list[1]) / 1000.0


    def turn_off(self):
        """Instruct the range finder to shutdown.

        Also closes the serial port.
        """
        self._send_command('PO', expect_okay=False)
        self.ser.close()


    def get_reading(self):
        """Trigger a measurement and read the result.

        Requires that one of set_height_mode() or set_horiz_vector_mode() has
        been called.

        Returns a dictionary containing the results fields.
        
        If the unit errors, then returns None
        """
        self._send_command('GO')
        raw_output = self._readline()
        if raw_output == "$E01":
            return None
        msg = pynmea2.parse(raw_output)
        return parse_list_result(self.expected, msg.data)


    def stop_measurement(self):
        self._send_command('ST')
        
        
    def get_firmware_version(self):
        self._send_command('PLTIT,RQ,ID', expect_okay=False)
        raw_output = self._readline()
        msg = re.split(',|\\*', raw_output)
        return parse_list_result(
            ['$ID', ('model', str), ('version', float), ('cksum', str)],
            msg
            )

if __name__ == "__main__":

    import sys

    def user_command(command_list):
        inp = raw_input("option: ").upper()
        if inp[0] in ['H', '?']:
            for idx, entry in enumerate(command_list):
                print "{:2}: {}".format(idx, entry[0])
            print " Q: quit"
            print " ?: help"
            return True
        if inp[0] == 'Q':
            return False
        try:
            idx = int(inp)
            entry = command_list[idx]
        except:
            print "Bad command"
            return True

        command = entry[1]
        result = command()
        print result
        return True


    dev_name = sys.argv[1]
    "/dev/rfcomm0"
    tp = TruPulseInterface(dev_name, trace=True)
    tp.set_horiz_vector_mode()

    commands = [
        ('get_voltage', tp.get_voltage),
        ('set_horiz_vector_mode', tp.set_horiz_vector_mode),
        ('set_height_mode', tp.set_height_mode),
        ('get_reading', tp.get_reading),
        ('set_defaults', tp.set_defaults),
        ('turn_off', tp.turn_off),
        ('stop_measurement', tp.stop_measurement),
        ('get_firmware_version', tp.get_firmware_version)]

    cont = True
    while cont:
        cont = user_command(commands)
