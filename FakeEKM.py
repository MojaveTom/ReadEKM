#!/usr/bin/env python3

from sqlalchemy import create_engine, text
import pymysql as mysql
import pymysql.err as Error
import time
import datetime
from datetime import date
from datetime import timedelta
from datetime import datetime
import os
import argparse
import sys
import random
import configparser
import logging
import logging.config
import logging.handlers
import json
import serial
import binascii
from binascii import a2b_hex, b2a_hex
from urllib.parse import urlsplit
from urllib.error import URLError
import socket
import threading
import socketserver
import Messages     # My message definitions -- has messages as bytearrays.

from ekmmeters import calc_crc16

# GLOBAL DEFINITIONS
DBConn = None
minutesOffset = 1.0
myMeterId = '000000000000'
meterAtable = 'NotARealTableIHope'
meterBtable = 'NotARealTableIHope'
anyMeterOk = True

# Configuration parameters without which we can do nothing.
RequiredConfigParams = frozenset((
    'viewer_host', 'viewer_schema', 'viewer_port', 'viewer_user',
    'viewer_password', 'meter_id', 'meter_table_a_suffix',
    'meter_table_b_suffix', 'meter_serial_port'
))

# Define logging
ProgFile = os.path.basename(sys.argv[0])
ProgName, ext = os.path.splitext(ProgFile)
ProgPath = os.path.dirname(os.path.realpath(sys.argv[0]))
logConfFileName = os.path.join(ProgPath, ProgName + '_loggingconf.json')
if os.path.isfile(logConfFileName):
    try:
        with open(logConfFileName, 'r') as logging_configuration_file:
            config_dict = json.load(logging_configuration_file)
        if 'log_file_path' in config_dict:
            logPath = os.path.expandvars(config_dict['log_file_path'])
            os.makedirs(logPath, exist_ok=True)
        else:
            logPath = ""
        for p in config_dict['handlers'].keys():
            if 'filename' in config_dict['handlers'][p]:
                logFileName = os.path.join(
                    logPath, config_dict['handlers'][p]['filename'])
                config_dict['handlers'][p]['filename'] = logFileName
        logging.config.dictConfig(config_dict)
    except Exception as e:
        print("loading logger config from file failed.")
        print(e)
        pass

logger = logging.getLogger(__name__)
logger.info('logger name is: "%s"', logger.name)

# LOCAL FUNCTIONS

def GetConfigFilePath():
    fp = os.path.join(ProgPath, 'secrets.ini')
    if not os.path.isfile(fp):
        fp = os.environ['PrivateConfig']
        if not os.path.isfile(fp):
            logger.error('No configuration file found: %s', fp)
            sys.exit(1)
    logger.info('Using configuration file at: %s', fp)
    return fp

def GetDatabaseV4AData(MeterId):
    #  Presumably won't get here if database tables don't exist.
    query = 'SELECT MeterData FROM {tableName} WHERE computerTime >= timestampadd(minute, {mins}, NOW()) LIMIT 1'.format(tableName = meterAtable, mins=minutesOffset)
    logger.debug('Getting Meter A data from database with query: %s'%query)
    try:
        result = DBConn.execute(text(query))
        logger.debug('Result from database query is %s'%result, flush = True)
        for r in result:
            logger.debug('Returning result: %s'%r[0])
            return bytearray(r[0])         # Just return the first result
    except:
        raise
    else:
        return GenerateFakeV4AData(MeterId)

def GetDatabaseV4BData(MeterId):
    #  Presumably won't get here if database tables don't exist.
    query = 'SELECT MeterData FROM {tableName} WHERE computerTime >= timestampadd(minute, {mins}, NOW()) LIMIT 1'.format(tableName = meterBtable, mins=minutesOffset)
    logger.debug('Getting Meter B data from database with query: %s'%query)
    try:
        result = DBConn.execute(text(query))
        logger.debug('Result from database query is %s'%result)
        for r in result:
            logger.debug('Returning result: %s'%r[0])
            return bytearray(r[0])         # Just return the first result
    except:
        raise
    else:
        return GenerateFakeV4BData(MeterId)

def makeEkmDateTime(theTime=datetime.now()):
    ekmTime=bytearray(a2b_hex(theTime.strftime('%y%m%d  %H%M%S').encode('ascii').hex()))
    ekmTime[Messages.MeterDateTime_weekday]=a2b_hex(('%02x'%theTime.isoweekday()).encode('ascii').hex())
    return ekmTime

def GenerateV4AData(MeterId = bytearray(b'\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30')):
    if (minutesOffset > 0) or ((MeterId.decode('ascii') != myMeterId) and not anyMeterOk):
        return GenerateFakeV4AData(MeterId)
    else:
        Messages.ResponseMsg = GetDatabaseV4AData(MeterId)
        if Messages.ResponseMsg is None:
            return GenerateFakeV4AData(MeterId)
        Messages.ResponseMsg[Messages.ResponseV4_meterNo] = MeterId
        Messages.ResponseMsg[Messages.CrcField] = a2b_hex(calc_crc16(Messages.ResponseMsg[Messages.CrcCalc]))
        return Messages.ResponseMsg


def GenerateV4BData(MeterId = bytearray(b'\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30')):
    if (minutesOffset > 0) or ((MeterId.decode('ascii') != myMeterId) and not anyMeterOk):
        return GenerateFakeV4BData(MeterId)
    else:
        Messages.ResponseMsg = GetDatabaseV4BData(MeterId)
        if Messages.ResponseMsg is None:
            return GenerateFakeV4BData(MeterId)
        Messages.ResponseMsg[Messages.ResponseV4_meterNo] = MeterId
        Messages.ResponseMsg[Messages.CrcField] = a2b_hex(calc_crc16(Messages.ResponseMsg[Messages.CrcCalc]))
        return Messages.ResponseMsg

def GenerateFakeV4AData(MeterId):
    Messages.ResponseMsg = bytearray(255)
    #  Fill the message with random digits
    for i in range(len(Messages.ResponseMsg)):
        Messages.ResponseMsg[i] = random.randint(0x30,0x39)
    # Put in known fields
    Messages.ResponseMsg[Messages.ResponseV4_STX] = Messages.STX
    Messages.ResponseMsg[Messages.ResponseV4_model] = Messages.ResponseV4model
    Messages.ResponseMsg[Messages.ResponseV3_FWver] = Messages.ResponseV4FWver
    Messages.ResponseMsg[Messages.ResponseV4_meterNo] = MeterId
    Messages.ResponseMsg[Messages.ResponseV4_postamble] = Messages.ResponseV4postamble
    Messages.ResponseMsg[Messages.ResponseV4_time] = makeEkmDateTime()
    Messages.ResponseMsg[Messages.ResponseV4_respKind] =Messages.RequestMsgV4ReqTypeB
    Messages.ResponseMsg[Messages.ResponseV4AData_kwhDecimals] = b'\x32'
    Messages.ResponseMsg[Messages.CrcField] = a2b_hex(calc_crc16(Messages.ResponseMsg[Messages.CrcCalc]))
    return Messages.ResponseMsg

def GenerateFakeV4BData(MeterId):
    Messages.ResponseMsg = GenerateV4AData(MeterId)
    Messages.ResponseMsg[Messages.ResponseV4_respKind] = Messages.RequestMsgV4ReqTypeB
    Messages.ResponseMsg[Messages.CrcField] = a2b_hex(calc_crc16(Messages.ResponseMsg[Messages.CrcCalc]))
    return Messages.ResponseMsg

def GenerateV3Data(MeterId=bytearray(b'\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30')):
    Messages.ResponseMsg = bytearray(255)
    #  Fill the message with random digits
    for i in range(len(Messages.ResponseMsg)):
        Messages.ResponseMsg[i] = random.randint(0x30,0x39)
    # Put in known fields
    Messages.ResponseMsg[Messages.ResponseV3_STX] = Messages.STX
    Messages.ResponseMsg[Messages.ResponseV3_model] = Messages.ResponseV3model
    Messages.ResponseMsg[Messages.ResponseV3_FWver] = Messages.ResponseV3FWver
    Messages.ResponseMsg[Messages.ResponseV3_meterNo] = MeterId
    Messages.ResponseMsg[Messages.ResponseV3_time] = makeEkmDateTime()
    Messages.ResponseMsg[Messages.ResponseV3_reserved] = bytearray(len(Messages.ResponseMsg[Messages.ResponseV3_reserved]))
    Messages.ResponseMsg[Messages.ResponseV3_postamble] = Messages.ResponseV3postamble
    Messages.ResponseMsg[Messages.CrcField] = a2b_hex(calc_crc16(Messages.ResponseMsg[Messages.CrcCalc]))
    return Messages.ResponseMsg

def GenerateRandomDataTable(tableId=b'\x30\x30\x30\x30'):
    Messages.ResponseMsg = bytearray(255)
    Messages.ResponseMsg[Messages.RespondTable_STX] = Messages.STX
    Messages.ResponseMsg[Messages.RespondTable_tableId] = tableId
    Messages.ResponseMsg[Messages.RespondTable_preamble] = Messages.RespondTablepreamble
    for i in range(len(Messages.ResponseMsg[Messages.RespondTable_body])):
        Messages.ResponseMsg[Messages.RespondTable_body][i]=random.randint(0x30,0x39)
    Messages.ResponseMsg[Messages.RespondTable_postamble] = Messages.RespondTablepostamble
    Messages.ResponseMsg[Messages.CrcField]=a2b_hex(calc_crc16(Messages.ResponseMsg[Messages.CrcCalc]))
    return Messages.ResponseMsg

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        '''
            result = conn.execute("SELECT MeterData, MeterTime FROM `"+schema+"`.`"+meterAtable +
                                "` WHERE ComputerTime > timestampadd(minute, -12, now()) ORDER BY idRawMeterData LIMIT 2")
            for r in result:
                meterData = r[0]
                meterTime = r[1]
                logger.debug('Meter data record from time %s is %s bytes long of class %s.' % (
                    meterTime, len(meterData), meterData.__class__))
                sp.write(meterData)
                logger.debug('Wrote meter data to serialPort.')
                Messages.ResponseMsg = sp.getResponse()
                logger.debug('Read %s bytes from serialPort' % len(Messages.ResponseMsg))
            pass
            logger.debug('Write "close" string to EKM meter.')
            sp.write("0142300375")
            logger.debug('Read the close string back again.')
            Messages.ResponseMsg = sp.getResponse(maxBytes=5)
            logger.debug('The received close string is: %s' %
                        Messages.ResponseMsg.encode().hex())
        '''

        cur_thread_name = threading.current_thread().name
        logger.debug('\n\nThread:  %s begins.'%cur_thread_name)
        while True:
            data = self.request.recv(1024)
            logger.debug('%s: Handling received message: %s'%(cur_thread_name, data))
            if len(data) == 0:
                logger.debug('Got empty message: close connection.')
                time.sleep(1)
                break
            response = Messages.ResponseNak      #### default response to unknown or malformed messages is NAK
            if data[Messages.RequestMsg_fixedBegin] == Messages.RequestCmdHeader:
                #  handle request messages
                logger.debug('Handling request message.')
                if (len(data) == len(Messages.RequestMsgV3)) and (data[-3:] == Messages.RequestCmdEnding):
                    logger.debug('Handling V3 request message.')
                    response = GenerateV3Data(data[Messages.RequestMsgV3Def_meterId])
                elif (len(data) == len(Messages.RequestMsgV4)) and (data[-3:] == Messages.RequestCmdEnding):
                    if data[Messages.RequestMsgV4Def_reqType] == Messages.RequestMsgV4ReqTypeA:
                        logger.debug('Handling V4A request message.')
                        response = GenerateV4AData(data[Messages.RequestMsgV4Def_meterId])
                    elif data[Messages.RequestMsgV4Def_reqType] == Messages.RequestMsgV4ReqTypeB:
                        logger.debug('Handling V4B request message.')
                        response = GenerateV4BData(data[Messages.RequestMsgV4Def_meterId])
                    else:   # Unknown data kind
                        logger.critical('Got unknown V4 request message.')
                        pass        #  send default ResponseNak
                else:   #  Ill formed request message
                    logger.critical('Got unknown request message.')
                    pass        #  send default ResponseNak
            elif data == Messages.CloseMsg:      #  CloseMsg doesn't have a valid CRC (looks like last byte is only part of a CRC)
                # received termination code
                logger.debug('Got Close message.')
                #  If FakeEKM was a state machine, we would set the state back to beginning.
                continue           #  Don't respond; DON'T close connection
            elif data[Messages.CrcField] != a2b_hex(calc_crc16(data[Messages.CrcCalc])):      # Crc must be correct for all other messages
                logger.warning('Got message with incorrect CRC.')
                logger.info('Message CRC: %s, calc CRC is: %s'%(data[Messages.CrcField], a2b_hex(calc_crc16(data[Messages.CrcCalc]))))
                pass        #  send default ResponseNak
            elif data[Messages.SendPasswordMsg_preamble] == Messages.SendPasswordMsg[Messages.SendPasswordMsg_preamble]:
                logger.debug('Got Password message.')
                response = Messages.ResponseAck      # Any password is ok
            elif data[Messages.SetCmdHeader_discriminator] == Messages.SetCmdHeader:
                logger.debug('Got Set command.')
                response = Messages.ResponseAck      # swallow all set commands without doing anything
            elif data[Messages.ReadCmdHeader_discriminator] == Messages.ReadCmdHeader:
                logger.debug('Got Read request.')
                response = GenerateRandomDataTable(data[Messages.ReadTableMsg_tableId])
            else:
                logger.warning('Got unrecognized message.')
                pass
            logger.debug('Sending response: %s'%response)
            self.request.sendall(response)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass



# MAIN
def main():
    global DBConn, minutesOffset, myMeterId, meterAtable, meterBtable, anyMeterOk
    # Determine the complete file paths for the config file and the graph definitions file.
    config = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation())
    configFile = GetConfigFilePath()
    # configFileDir = os.path.dirname(configFile)

    # Open up the configuration file and extract some parameters.
    config.read(configFile)
    cfgSection = ProgFile + "/"+os.environ['HOST']
    logger.info("INI file cofig section is: %s", cfgSection)
    # logger.debug('Config section has options: %s'%set(config.options(cfgSection)))
    # logger.debug('Required options are: %s'%RequiredConfigParams)
    if not config.has_section(cfgSection):
        logger.critical('Config file "%s", has no section "%s".',
                        configFile, cfgSection)
        sys.exit(2)
    if len(RequiredConfigParams - set(config.options(cfgSection))) > 0:
        logger.critical('Config  section "%s" does not have all required params: "%s", it has params: "%s".',
                        cfgSection, RequiredConfigParams, set(config.options(cfgSection)))
        logger.debug('The missing params are: %s' %
                     (RequiredConfigParams - set(config.options(cfgSection)),))
        sys.exit(3)
    anyMeterOk = config.getboolean(cfgSection, 'use_database_for_any_meter', fallback=True)

    cfg = config[cfgSection]

    parser = argparse.ArgumentParser(
        description='Display graphs of home parameters.\nDefaults to show all.')
    parser.add_argument("-s", "--serial_port", dest="serialPort", action="store",
                        default=cfg['meter_serial_port'], help="The serial port to which the EKM meter is connected.")
    parser.add_argument("-i", "--meterId", dest="meterId", action="store",
                        default=cfg['meter_id'], help="Numeric Id of EKM meter.")
    parser.add_argument("-t", "--start", dest="startTime", action="store",
                        default=None, help="Date/time at which to start retrieving database data.")
    parser.add_argument("-o", "--offsetHours", dest="hourOffset", action="store", default=None,
        help="Time offset from NOW to retrieve send data to client.  Negative values access database, positive values send random digits.")
    parser.add_argument("-a", "--anyMeter", dest="anyMeter", action="store_true",
                        default=None, help="Accept any meter Id.")
    parser.add_argument("-v", "--verbosity", dest="verbosity",
                        action="count", help="increase output verbosity", default=0)
    args = parser.parse_args()
    Verbosity = args.verbosity
    startTime = None
    minutesOffset = None
    if (args.hourOffset is None) and (args.startTime is None):
        minutesOffset = -1440       # default 1 day ago
    elif args.startTime is not None:
        try:
            startTime = datetime.strptime(args.startTime, '%Y-%m-%d %H:%M:%S')
        except ValueError as e:
            logger.exception(e)
            logger.warning('Argument for -t (--start) could not be parsed.  Using default time offset of 1 day.')
    if startTime is not None:
        logger.debug('Computing minutes offset from now() and startTime.')
        minutesOffset = (startTime - datetime.now()) / timedelta(minutes=1)
    else:
        if (minutesOffset is None) and (args.hourOffset is not None):
            minutesOffset = float(args.hourOffset) * 60
        else:
            minutesOffset = -1440       # default 1 day ago
    logger.debug('Using minutesOffset of: %s'%minutesOffset)

    if args.anyMeter is not None:
        anyMeterOk = args.anyMeter
    logger.debug('Any meter is OK? %s'%anyMeterOk)
    # setup "serial" port
    '''Extract pipe file name (port) from an URL string;
        set mode to "client" or "server"'''
    try:
        parts = urlsplit(args.serialPort)
    except URLError:
        logger.critical('The serial port parameter is not a URL, FakeEKM.py connot proceed.')
        raise
    if parts.scheme != "socket":
        raise Exception('expected a string in the form "socket://<host>:<port>[?logging={debug|info|warning|error}]": not starting with socket:// (%r)' % (parts.scheme,))

    # setup database connection
    user = cfg['viewer_user']
    pwd = cfg['viewer_password']
    host = cfg['viewer_host']
    port = cfg['viewer_port']
    schema = cfg['viewer_schema']
    logger.info("user %s" % (user,))
    logger.info("pwd %s" % (pwd,))
    logger.info("host %s" % (host,))
    logger.info("port %s" % (port,))
    logger.info("schema %s" % (schema,))

    # need meterId both as integer and as 12 char string
    myMeterIdInt = int(args.meterId)
    myMeterId = '%012d' % myMeterIdInt

    logger.debug('MeterId as int is %s; as str "%s"' % (myMeterIdInt, myMeterId))
    if myMeterIdInt < 300000000:
        logger.critical('EKM V3 meters are not supported for database as data source.')
        minutesOffset = 1       #  => always generate random data

    if minutesOffset < 0:       #  Verify that database tables are available
        meterAtable = myMeterId + cfg['meter_table_a_suffix']
        meterBtable = myMeterId + cfg['meter_table_b_suffix']
        logger.debug('meterAtable is "%s"' % meterAtable)
        logger.debug('meterBtable is "%s"'%meterBtable)

        connstr = 'mysql+pymysql://{user}:{pwd}@{host}:{port}/{schema}'.format(
            user=user, pwd=pwd, host=host, port=port, schema=schema)
        logger.debug("database connection string: %s" % (connstr,))
        Eng = create_engine(connstr, echo=True if Verbosity >=
                            2 else False, logging_name=logger.name)
        logger.debug(Eng)
        try:
            with Eng.connect() as DBConn, DBConn.begin():
                logger.info("Viewer connection to database established.")
                query = "SHOW TABLES LIKE '%s%%'"%myMeterId
                logger.debug('Checking database for message tables with query: %s'%query)
                result = DBConn.execute(text(query))
                requiredTables = [meterAtable, meterBtable]
                for r in result:
                    logger.debug('Checking if %s is a required table.' % r[0])
                    if r[0] in requiredTables:
                        requiredTables.remove(r[0])
                        logger.debug('Table %s is in the database.' % (r[0],))
                        if len(requiredTables) == 0:
                            break
                if len(requiredTables) != 0:
                    logger.critical('Not all required tables are in the database; only random messages will be generated.')
                    minutesOffset = 1       #  => always generate random data
                else:
                    logger.debug('Found all required tables in database.')

                with ThreadedTCPServer((parts.hostname, parts.port), ThreadedTCPRequestHandler) as server:
                    ip, port = server.server_address
                    logger.debug('TCP server started at address "%s:%s"'%(ip, port))
                    # Start a thread with the server -- that thread will then start one
                    # more thread for each request
                    server_thread = threading.Thread(target=server.serve_forever)
                    # Exit the server thread when the main thread terminates
                    server_thread.daemon = False                # was True
                    server_thread.start()
                    logger.debug("Server loop running in thread:  %s"%server_thread.name)
                    response = "keep going"
                    while response.lower().find("quit") < 0:
                        response = input('Type "quit" to terminate FakeEKM server: ')
                    logger.info('Server quits.')
                    server.shutdown()
        finally:
            pass

    logger.info('             ##############   FakeEKM  All Done   #################')


if __name__ == "__main__":
    main()
    pass
