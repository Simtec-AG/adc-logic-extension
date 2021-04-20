# High Level Analyzer - Air Data Simtec
# 
# Decodes frames sent following the swiss air data format.
#
# Details about the format  used can be found in devices Interface Control Document
#
# This library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Simtec AG has no obligation to provide maintenance, support,  updates, enhancements, or modifications.

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting
import struct

#Map of SOH1 LABEL
SOH1_LABELS = {
    0x1: 'Qc',
    0x2: 'Ps',
    0x3: 'AoA',
    0x4: 'AoS',
    0x5: 'CAS',
    0x6: 'TAS',
    0x7: 'Hp',
    0x8: 'Ma',
    0x9: 'SAT',
    0xA: 'TAT',
    0xB: 'dp1',
    0xC: 'dp2',
    0xD: 'PCB',
    # 0xE: 'QNH cmd',
}

#Map of SOH2 LABEL
SOH2_LABELS = {
    0x1: 'CR',
    0x2: 'PT',
    0x5: 'CAS-rate',
    0x6: 'TAS-rate',
    0x7: 'Hbaro',
    0xC: 'DTR',
    0xD: 'HTR',
    0xE: 'CUR',
}

#Map of SOH3 LABEL
SOH3_LABELS = {
    0x1: 'Qc raw',
    0x2: 'Ps raw',
    0x3: 'dPaoa',
    0x4: 'dPaos',
    0x5: 'IAT',
    0x6: 'BAT',
}

#Map of SOH3 LABEL
SOH5_LABELS = {
    0x1: 'Qc*',
    0x2: 'Ps*',
    0x3: 'Hp*',
    0x4: 'H baro*',
    0x5: 'CAS*',
    0x6: 'TAS*',
    0x7: 'CR*',

}

#Map of all ADC data labels
DATA_LABELS = {
    0x01: SOH1_LABELS,
    0x02: SOH2_LABELS,
    0x03: SOH3_LABELS,
    0x05: SOH5_LABELS,
}

#Map of the different flags and their values
DATA_FLAG = {
    0x00: 'valid',
    0x10: 'above',
    0x20: 'below',
    0x30:' invalid +',
    0x40: 'invalid -',
    0x50: 'invalid',
}

# Position of the marker bit in the label byte
MARKER_BIT = 0x80

class StatusPacket:
    # Start of header and label defining a status packet
    SOH = 0x01
    LABEL = 0xF

    def __init__(self):
        self.int_value = None
        self.is_finish = False

        self.__data = []
    
    def __parse_data(self, int_value):
        ch = chr(int_value)
        if ((ch < '0' or ch > '9') and (ch < 'A' or ch > 'F')):
            return "Non hexadecimal value detected"

    def __parse_end_of_message(self):
        try:
            string_value = "".join(map(chr,self.__data[1:5]))
            bytes_object = bytes.fromhex(string_value)
            self.int_value = struct.unpack('>H', bytes_object)[0]

        except :
            return "Could not parse status msg"

    def parse_byte(self, int_value):
        self.__data.append(int_value)

        #header byte
        if len(self.__data) == 1:
            return

        #data byte
        elif len(self.__data) > 1 and len(self.__data) < 6:
            return self.__parse_data(int_value)

        #end of message
        elif len(self.__data) == 6 and chr(int_value) == '\r':
            self.is_finish = True
            return self.__parse_end_of_message()

        #error
        else:
            return "Wrong message length"

    @classmethod
    def is_status_packet(cls, soh, header):
        if (soh == cls.SOH) and (header == (cls.LABEL | MARKER_BIT)):
            return True
        else:
            return False

#Representing a data sent by the air data controller
class DataPacket:
    def __init__(self, soh):
        self.flag = None
        self.label = None
        self.float_value = None
        self.is_finish = False

        self.__data = []
        self.__soh = soh
        
    def __parse_header(self, int_value):
        if int_value & MARKER_BIT == 0:
            #marker bit not set
            return "Marker bit not set"
        
        try:
            self.flag = DATA_FLAG[int_value & 0x70]
            self.label = DATA_LABELS[self.__soh][int_value & 0x0F]
        except KeyError:
            return "Data ID not valid: "

    def __parse_data(self, int_value):
        ch = chr(int_value)
        if ((ch < '0' or ch > '9') and (ch < 'A' or ch > 'F')):
            return "Non hexadecimal value detected"

    def __parse_end_of_message(self):
        try:
            string_value = "".join(map(chr,self.__data[1:9]))
            bytes_object = bytes.fromhex(string_value)
            self.float_value = struct.unpack('>f', bytes_object)[0]
        except:
            return "Could not convert hex value in float"

    def parse_byte(self, int_value):

        self.__data.append(int_value)

        #header byte
        if len(self.__data) == 1:
            return self.__parse_header(int_value)

        #data byte
        elif len(self.__data) > 1 and len(self.__data) < 10:
            return self.__parse_data(int_value)
        
        #end of message
        elif len(self.__data) == 10 and chr(int_value) == '\r':
            self.is_finish = True
            return self.__parse_end_of_message()
        
        #error
        else:
            return "Wrong message length"

class AirDataPacket():
    def __init__(self, start_time, soh):
        self.start_time = start_time
        self.stop_time = None
        self.soh = soh
        self.error = None
        self.content = None

    def __packet_error(self, byte_stop_time, error_msg):
        self.error = error_msg
        self.stop_time = byte_stop_time
    
    def parse_byte(self, int_value, byte_stop_time):
        ''' 
        parse a byte and decode it
        '''
        if self.content is None:
            if StatusPacket.is_status_packet(self.soh, int_value):
                self.content = StatusPacket()
            else:
                self.content = DataPacket(self.soh)

        error_msg = self.content.parse_byte(int_value)

        if error_msg is not None:
            self.__packet_error(byte_stop_time, error_msg)
        
        if self.content.is_finish == True:
            self.stop_time = byte_stop_time


class AirDataAnalyser(HighLevelAnalyzer):
    #List of types that this analyzer produces
    result_types = {
        'error': {'format': "ERROR: {{data.error_msg}}"},
        'data': {'format': "{{data.label}}: {{data.value}}"},
        'status': {'format': "Status = {{data.hex_value}}"}
    }

    def __init__(self):
        self.current_packet = None

    def decode(self, frame: AnalyzerFrame):
        '''
        Process a frame from the input analyzer, and return a single `AnalyzerFrame`

        The type and data values in `frame` will depend on the input analyzer.
        '''
        if not 'error' in frame.data:
            int_value = frame.data['data'][0]
            
            #Test if a new start of header as been detected
            if int_value in DATA_LABELS:
                self.current_packet = AirDataPacket(frame.start_time, int_value)

            elif self.current_packet is not None:
                self.current_packet.parse_byte(int_value, frame.end_time)

                if self.current_packet.stop_time is not None:

                    if self.current_packet.error is not None:
                        returned_frame = AnalyzerFrame(
                            'error', self.current_packet.start_time, self.current_packet.stop_time, {'error_msg': self.current_packet.error})

                    elif isinstance(self.current_packet.content, StatusPacket):
                        returned_frame = AnalyzerFrame(
                            'status', self.current_packet.start_time, self.current_packet.stop_time, {'hex_value': hex(self.current_packet.content.int_value)})

                    else:
                        returned_frame = AnalyzerFrame(
                            'data', self.current_packet.start_time, self.current_packet.stop_time, {
                                'label': self.current_packet.content.label,
                                'flag': self.current_packet.content.flag,
                                # Logic SW crash when NaN is returned, as a workaround we need to convert the float in string
                                'value': str(round(self.current_packet.content.float_value, 3))
                            })

                    self.current_packet = None
                    return returned_frame
