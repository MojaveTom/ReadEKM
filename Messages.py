''' !
@file
@brief Header file describing EKM Omnimeter messages.

Structures are defined to access fields of messages.
Where messages have common parts, they are put into a super class from
which individual messages inherit.  To allow functions that process
multiple kinds of related messages, the messages are grouped into a union.

@author Thomas A. DeMay
@date 2015
@par    Copyright (C) 2015  Thomas A. DeMay
@par
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    any later version.
@par
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
@par
    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

'''
@file
@brief Source to initialize message globals.

Messages and parts of messages with known content are defined here.

@author Thomas A. DeMay
@date 2015
@par    Copyright (C) 2015  Thomas A. DeMay
@par
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    any later version.
@par
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
@par
    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

RequestMsgV3Def_fixedBegin = slice(0,2)
RequestMsgV3Def_meterId = slice(2,14)
RequestMsgV3Def_fixedEnd = slice(14,17)

RequestMsgV4Def_fixedBegin = slice(0,2)
RequestMsgV4Def_meterId = slice(2,14)
RequestMsgV4Def_reqType = slice(14,16)     # '\x30', '\x30' for Request A  OR  '\x30', '\x31' for Request B
RequestMsgV4Def_fixedEnd = slice(16,19)

#  Response fields common to V3 and V4
ResponseData_fixed02 = slice(0,1)                 # SQL offset   1
ResponseData_model = slice(1,3)                   # SQL offset   2
ResponseData_firmwareVer = slice(3,4)             # SQL offset   4
ResponseData_meterId = slice(4,16)                # SQL offset   5

ResponseV3Data_fixed02 = slice(0,1)                 # SQL offset   1
ResponseV3Data_model = slice(1,3)                   # SQL offset   2
ResponseV3Data_firmwareVer = slice(3,4)             # SQL offset   4
ResponseV3Data_meterId = slice(4,16)                # SQL offset   5
ResponseV3Data_totalKwh = slice(16,24)                # SQL offset  17
ResponseV3Data_time1Kwh = slice(24,32)                # SQL offset  25
ResponseV3Data_time2Kwh = slice(32,40)                # SQL offset  33
ResponseV3Data_time3Kwh = slice(40,48)                # SQL offset  41
ResponseV3Data_time4Kwh = slice(48,56)                # SQL offset  49
ResponseV3Data_totalRevKwh = slice(56,64)             # SQL offset  57
ResponseV3Data_time1RevKwh = slice(64,72)             # SQL offset  65
ResponseV3Data_time2RevKwh = slice(72,80)             # SQL offset  73
ResponseV3Data_time3RevKwh = slice(80,88)             # SQL offset  81
ResponseV3Data_time4RevKwh = slice(88,96)             # SQL offset  89
ResponseV3Data_volts1 = slice(96,100)                  # SQL offset  97
ResponseV3Data_volts2 = slice(100,104)                  # SQL offset 101
ResponseV3Data_volts3 = slice(104,108)                  # SQL offset 105
ResponseV3Data_amps1 = slice(108,113)                   # SQL offset 109
ResponseV3Data_amps2 = slice(113,118)                   # SQL offset 114
ResponseV3Data_amps3 = slice(118,123)                   # SQL offset 119
ResponseV3Data_watts1 = slice(123,130)                  # SQL offset 124
ResponseV3Data_watts2 = slice(130,137)                  # SQL offset 131
ResponseV3Data_watts3 = slice(137,144)                  # SQL offset 138
ResponseV3Data_wattsTotal = slice(144,151)              # SQL offset 145
ResponseV3Data_cos1 = slice(151,155)                    # SQL offset 152
ResponseV3Data_cos2 = slice(155,159)                    # SQL offset 156
ResponseV3Data_cos3 = slice(159,163)                    # SQL offset 160
ResponseV3Data_maxDemand = slice(163,171)               # SQL offset 164
ResponseV3Data_demandPeriod = slice(171,172)            # SQL offset 172
ResponseV3Data_meterDateTime = slice(172,186)             # SQL offset 173
ResponseV3Data_currentTransformer = slice(186,190)      # SQL offset 187
ResponseV3Data_pulseCount1 = slice(190,198)             # SQL offset 191
ResponseV3Data_pulseCount2 = slice(198,206)             # SQL offset 199
ResponseV3Data_pulseCount3 = slice(206,214)             # SQL offset 207
ResponseV3Data_pulseRatio1 = slice(214,218)             # SQL offset 215
ResponseV3Data_pulseRatio2 = slice(218,222)             # SQL offset 219
ResponseV3Data_pulseRatio3 = slice(222,226)             # SQL offset 223
ResponseV3Data_PulseState = slice(226,229)              # SQL offset 227
ResponseV3Data_reserved = slice(229,249)               # SQL offset 230
ResponseV3Data_fixedEnd = slice(249,253)                # SQL offset 250
ResponseV3Data_crc = slice(253,255)                     # SQL offset 254

#  V4 fields common to V4A and V4B
ResponseV4Data_fixed02 = slice(0,1)                 # SQL offset   1
ResponseV4Data_model = slice(1,3)                   # SQL offset   2
ResponseV4Data_firmwareVer = slice(3,4)             # SQL offset   4
ResponseV4Data_meterId = slice(4,16)                # SQL offset   5
ResponseV4Data_reserved = slice(16,233)              # SQL offset  17
ResponseV4Data_meterDateTime = slice(233,247)             # SQL offset 234
ResponseV4Data_msgType = slice(247,249)                 # SQL offset 248
ResponseV4Data_fixedEnd = slice(249,253)                # SQL offset 250
ResponseV4Data_crc = slice(253,255)                     # SQL offset 254

ResponseV4AData_fixed02 = ResponseV4Data_fixed02                 # SQL offset   1
ResponseV4AData_model = ResponseV4Data_model                   # SQL offset   2
ResponseV4AData_firmwareVer = ResponseV4Data_firmwareVer             # SQL offset   4
ResponseV4AData_meterId = ResponseV4Data_meterId                # SQL offset   5
ResponseV4AData_totalKwh = slice(16,24)                # SQL offset  17
ResponseV4AData_totalKVARh = slice(24,32)              # SQL offset  25
ResponseV4AData_totalRevKwh = slice(32,40)             # SQL offset  33
ResponseV4AData_totalKwhL1 = slice(40,48)              # SQL offset  41
ResponseV4AData_totalKwhL2 = slice(48,56)              # SQL offset  49
ResponseV4AData_totalKwhL3 = slice(56,64)              # SQL offset  57
ResponseV4AData_reverseKwhL1 = slice(64,72)            # SQL offset  65
ResponseV4AData_reverseKwhL2 = slice(72,80)            # SQL offset  73
ResponseV4AData_reverseKwhL3 = slice(80,88)            # SQL offset  81
ResponseV4AData_resettableTotalKwh = slice(88,96)      # SQL offset  89
ResponseV4AData_resettableReverseKwh = slice(96,104)    # SQL offset  97
ResponseV4AData_volts1 = slice(104,108)                  # SQL offset 105
ResponseV4AData_volts2 = slice(108,112)                  # SQL offset 109
ResponseV4AData_volts3 = slice(112,116)                  # SQL offset 113
ResponseV4AData_amps1 = slice(116,121)                   # SQL offset 117
ResponseV4AData_amps2 = slice(121,126)                   # SQL offset 122
ResponseV4AData_amps3 = slice(126,131)                   # SQL offset 127
ResponseV4AData_watts1 = slice(131,138)                  # SQL offset 132
ResponseV4AData_watts2 = slice(138,145)                  # SQL offset 139
ResponseV4AData_watts3 = slice(145,152)                  # SQL offset 146
ResponseV4AData_wattsTotal = slice(152,159)              # SQL offset 153
ResponseV4AData_cos1 = slice(159,163)                    # SQL offset 160
ResponseV4AData_cos2 = slice(163,167)                    # SQL offset 164
ResponseV4AData_cos3 = slice(167,171)                    # SQL offset 168
ResponseV4AData_varL1 = slice(171,178)                   # SQL offset 172
ResponseV4AData_varL2 = slice(178,185)                   # SQL offset 179
ResponseV4AData_varL3 = slice(185,192)                   # SQL offset 186
ResponseV4AData_varL123 = slice(192,199)                 # SQL offset 193
ResponseV4AData_frequency = slice(199,203)               # SQL offset 200
ResponseV4AData_pulseCount1 = slice(103,211)             # SQL offset 204
ResponseV4AData_pulseCount2 = slice(211,219)             # SQL offset 212
ResponseV4AData_pulseCount3 = slice(219,227)             # SQL offset 220
ResponseV4AData_pulseState = slice(227,228)              # SQL offset 228
ResponseV4AData_currentDir123 = slice(228,229)           # SQL offset 229
ResponseV4AData_outState = slice(229,230)                # SQL offset 230
ResponseV4AData_kwhDecimals = slice(230,231)             # SQL offset 231
ResponseV4AData_reserved = slice(231,233)                # SQL offset 232
ResponseV4AData_meterDateTime = ResponseV4Data_meterDateTime             # SQL offset 234
ResponseV4AData_msgType = ResponseV4Data_msgType                 # SQL offset 248
ResponseV4AData_fixedEnd = ResponseV4Data_fixedEnd                # SQL offset 250
ResponseV4AData_crc = ResponseV4Data_crc                     # SQL offset 254

ResponseV4BData_fixed02 = ResponseV4Data_fixed02                 # SQL offset   1
ResponseV4BData_model = ResponseV4Data_model                   # SQL offset   2
ResponseV4BData_firmwareVer = ResponseV4Data_firmwareVer             # SQL offset   4
ResponseV4BData_meterId = ResponseV4Data_meterId                # SQL offset   5
ResponseV4BData_time1Kwh = slice(16,24)                # SQL offset  17
ResponseV4BData_time2Kwh = slice(24,32)                # SQL offset  25
ResponseV4BData_time3Kwh = slice(32,40)                # SQL offset  33
ResponseV4BData_time4Kwh = slice(40,48)                # SQL offset  41
ResponseV4BData_time1RevKwh = slice(48,56)             # SQL offset  49
ResponseV4BData_time2RevKwh = slice(56,64)             # SQL offset  57
ResponseV4BData_time3RevKwh = slice(64,72)             # SQL offset  65
ResponseV4BData_time4RevKwh = slice(72,80)             # SQL offset  73
ResponseV4BData_volts1 = slice(80,84)                  # SQL offset  81
ResponseV4BData_volts2 = slice(84,88)                  # SQL offset  85
ResponseV4BData_volts3 = slice(88,92)                  # SQL offset  89
ResponseV4BData_amps1 = slice(92,97)                   # SQL offset  93
ResponseV4BData_amps2 = slice(97,102)                   # SQL offset  98
ResponseV4BData_amps3 = slice(102,107)                   # SQL offset 103
ResponseV4BData_watts1 = slice(107,114)                  # SQL offset 108
ResponseV4BData_watts2 = slice(114,121)                  # SQL offset 115
ResponseV4BData_watts3 = slice(121,128)                  # SQL offset 122
ResponseV4BData_wattsTotal = slice(128,135)              # SQL offset 129
ResponseV4BData_cos1 = slice(135,139)                    # SQL offset 136
ResponseV4BData_cos2 = slice(139,143)                    # SQL offset 140
ResponseV4BData_cos3 = slice(143,147)                    # SQL offset 144
ResponseV4BData_maxDemand = slice(147,155)               # SQL offset 148
ResponseV4BData_demandPeriod = slice(155,156)            # SQL offset 156
ResponseV4BData_PRatio1 = slice(156,160)                 # SQL offset 157
ResponseV4BData_PRatio2 = slice(160,164)                 # SQL offset 161
ResponseV4BData_PRatio3 = slice(164,168)                 # SQL offset 165
ResponseV4BData_CTRatio = slice(168,172)                 # SQL offset 169
ResponseV4BData_autoResetMaxDemand = slice(172,173)      # SQL offset 173
ResponseV4BData_CFRatio = slice(173,177)                 # SQL offset 174
ResponseV4BData_reserved = slice(177,233)               # SQL offset 178
ResponseV4BData_meterDateTime = ResponseV4Data_meterDateTime             # SQL offset 234
ResponseV4BData_msgType = ResponseV4Data_msgType                 # SQL offset 248
ResponseV4BData_fixedEnd = ResponseV4Data_fixedEnd                # SQL offset 250
ResponseV4BData_crc = ResponseV4Data_crc                     # SQL offset 254

MeterDateTime_year = slice(0,2)
MeterDateTime_month = slice(2,4)
MeterDateTime_day = slice(4,6)
MeterDateTime_weekday = slice(6,8)
MeterDateTime_hour = slice(8,10)
MeterDateTime_minute = slice(10,12)
MeterDateTime_second = slice(12,14)

SetTimeMsg_SOH = slice(0,1)
SetTimeMsg_preamble = slice(1,9)
SetTimeMsg_meterDateTime = slice(9,23)
SetTimeMsg_fixedSeparator = slice(23,24)
SetTimeMsg_ETX = slice(24,25)
SetTimeMsg_crc = slice(25,27)

OutputControl_SOH = slice(0,1)
OutputControl_preamble = slice(1,7)
OutputControl_relayNum = slice(7,8)
OutputControl_fixedSeparator = slice(8,9)
OutputControl_newState = slice(9,10)
OutputControl_newStateDuration = slice(10,14)
OutputControl_postamble = slice(14,16)
OutputControl_crc = slice(16,18)

SetPasswordMsg_SOH = slice(0,1)
SetPasswordMsg_preamble = slice(1,9)
SetPasswordMsg_password = slice(9,17)
SetPasswordMsg_postamble = slice(17,19)
SetPasswordMsg_crc = slice(19,21)

SendPasswordMsg_SOH = slice(0,1)
SendPasswordMsg_preamble = slice(1,5)
SendPasswordMsg_password = slice(5,13)
SendPasswordMsg_postamble = slice(13,15)
SendPasswordMsg_crc = slice(15,17)

CrcCalc = slice(1,-2)
CrcField = slice(-2, 1025)  # end index must be larger than the length of any message.

CloseMsg =   bytearray(b'\x01\x42\x30\x03\x75')

RequestMsgV3 =  bytearray(b'\x2f\x3f\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x21\x0d\x0a')

RequestMsgV4 =  bytearray(b'\x2f\x3f\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x21\x0d\x0a')
RequestMsgV4ReqTypeA = bytearray(b'\x30\x30')
RequestMsgV4ReqTypeB = bytearray(b'\x30\x31')

Output1OnMsg =  bytearray(b'\x01\x57\x31\x02\x30\x30\x38\x31\x28\x31\x30\x30\x30\x30\x29\x03\x31\x61')
                                
Output1OffMsg = bytearray(b'\x01\x57\x31\x02\x30\x30\x38\x31\x28\x30\x30\x30\x30\x30\x29\x03\x21\x21')
                                 
Output2OnMsg =  bytearray(b'\x01\x57\x31\x02\x30\x30\x38\x32\x28\x31\x30\x30\x30\x30\x29\x03\x25\x11')

Output2OffMsg = bytearray(b'\x01\x57\x31\x02\x30\x30\x38\x32\x28\x30\x30\x30\x30\x30\x29\x03\x35\x51')

SetTimeMsg =    bytearray(b'\x01\x57\x31\x02\x30\x30\x36\x30\x28\x31\x35\x30\x39\x30\x31\x30\x33\x31\x30\x30\x36\x32\x30\x29\x03\x55\x62')

SetPasswordMsg = bytearray(b'\x01\x57\x31\x02\x30\x30\x32\x30\x28\x30\x30\x30\x30\x30\x30\x30\x30\x29\x03\x55\x62')

SendPasswordMsg = bytearray(b'\x01\x50\x31\x02\x28\x30\x30\x30\x30\x30\x30\x30\x30\x29\x03\x32\x44')
SendPasswordMsg_preamble = slice(0,5)
SendPasswordMsg_postamble = slice(-4,-3)

ResponseAck =   bytearray(b'\x06')

ResponseNak =   bytearray(b'\x15')

ReadTableMsg = bytearray(b'\x01\x51\x31\x02\x30\x30\x30\x30\x03\x00\x00')
ReadTableMsg_SOH = slice(0,1)
ReadTableMsg_preamble = slice(1,4)
ReadTableMsg_tableId = slice(4,8)
ReadTableMsg_postamble = slice(8,9)
ReadTableMsg_crc = slice(9,11)

RespondTable_STX = slice(0,1)
RespondTable_tableId = slice(1,5)
RespondTable_preamble = slice(5,6)
RespondTable_body = slice(6,-3)
RespondTable_postamble = slice(-3,-2)
RespondTablepreamble = bytearray(b'\x28')
RespondTablepostamble = bytearray(b'\x29')

ResponseMsg =   bytearray(255)

ResponseV3_STX    = slice(0,1)
ResponseV3_model  = slice(1,3)
ResponseV3_FWver  = slice(3,4)
ResponseV3_meterNo = slice(4,16)
ResponseV3_body   = slice(16,229)
ResponseV3_time   = slice(172,186)
ResponseV3_reserved = slice(229,249)
ResponseV3_postamble    = slice(249,253)
ResponseV3postamble  = bytearray(b'\x21\x0d\x0a\x03')

SOH    = bytearray(b'\x01')
STX    = bytearray(b'\x02')

ResponseV4model  = bytearray(b'\x10\x24')
ResponseV4FWver  = bytearray(b'\x15')

ResponseV3model  = bytearray(b'\x10\x17')
ResponseV3FWver  = bytearray(b'\x13')

ResponseV4_STX    = slice(0,1)
ResponseV4_model  = slice(1,3)
ResponseV4_FWver  = slice(3,4)
ResponseV4_meterNo = slice(4,16)
ResponseV4_body   = slice(16,233)
ResponseV4_time     = slice(233,247)
ResponseV4_respKind = slice(247,249)
ResponseV4_postamble    = slice(249,253)
ResponseV4postamble  = bytearray(b'\x21\x0d\x0a\x03')



#  Common beginning of all set commands
SetCmdHeader =  bytearray(b'\x01\x57\x31\x02')
SetCmdHeader_discriminator = slice(0,4)

#  Common beginning of all read commands
ReadCmdHeader = bytearray(b'\x01\x51\x31\x02')
ReadCmdHeader_discriminator = slice(0,4)

#  Common beginning of all request commands
RequestCmdHeader = bytearray(b'\x2f\x3f')
RequestMsg_fixedBegin = slice(0,2)

RequestCmdEnding = bytearray(b'\x21\x0d\x0a')
#RequestCmdEnding_discriminator = slice(-3)  ## negative start indices don't work with slice function