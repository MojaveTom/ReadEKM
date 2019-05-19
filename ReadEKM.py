#!/usr/bin/env python3

'''
High level program flow:
1   Setup logging
2   Read some parameters from secrets file (for command line arg defaults)
3   Process command line arguments
4   get parameters for serial connection
5   get parameters for database
6   get parameters for MQTT
7   Test database for tables associated with meter id
8   Init database connection, serial connection, meter access
9       wait till next "top of the minute"
10      Loop the number of times specified
11          set state of water valve based on magic water valve
                (as a by-product, A data is read)
12          log raw A data to database
13          update database to reflect new valve state
14          publish selected/computed A data to MQTT
15          if "time to read B"
16              update "time to read B"
17              read B data
18              log raw B data to database
19          if it is a new day
20              set local standard time to meter
21          if magic shutdown file exists, exit loop, cleanup and exit
22          wait till next time to read A

'''
import pymysql.err as Error
import time
import datetime
# from datetime import date, datetime, timedelta, timezone
import os
import argparse
import sys
import configparser
import logging
import logging.config
import logging.handlers
import json
import serial
from ekmmeters import *
import binascii
from binascii import a2b_hex

#from Messages import *
import pymysql

import paho.mqtt.publish as publish

#############   STASH UNUSED CODE
'''
        
        result = conn.execute("SELECT MeterData, MeterTime FROM `"+schema+"`.`"+meterAtable+"` WHERE ComputerTime > timestampadd(minute, -12, now()) ORDER BY idRawMeterData LIMIT 2")
        for r in result:
            meterData = r[0]
            meterTime = r[1]
            logger.debug('Meter data record from time %s is %s bytes long of class %s.'%(meterTime, len(meterData), meterData.__class__))
            sp.write(meterData)
            logger.debug('Wrote meter data to serialPort.')
            ResponseMsg = sp.getResponse()
            logger.debug('Read %s bytes from serialPort'%len(ResponseMsg))
        pass
        logger.debug('Write "close" string to EKM meter.')
        sp.write("0142300375")
        logger.debug('Read the close string back again.')
        ResponseMsg = sp.getResponse(maxBytes=5)
        logger.debug('The received close string is: %s'%ResponseMsg.encode().hex())

    # need meterId both as integer and as 12 char string
            flatten meterIds list
    meterIds = [num for elem in args.meterId for num in elem]
    meterIdInts = [int(i) for i in meterIds]
    meterIds = ['%012d'%i for i in meterIdInts]

    logger.debug('MeterId as int is %s; as str "%s"'%(meterIdInts, meterIds))
    if len(meterIds) > 1:
        logger.debug('Multiple meters not yet supported.  Using only the first.')
    meterId = meterIds[0]
    meterIdInt = meterIdInts[0]

'''

#######################  GLOBAL DEFINITIONS

# Configuration parameters without which we can do nothing.
RequiredConfigParams = frozenset((
    'inserter_host'
  , 'inserter_schema'
  , 'inserter_port'
  , 'inserter_user'
  , 'inserter_password'
  , 'meter_id'
  , 'meter_table_a_suffix'
  , 'meter_table_b_suffix'
  , 'mqtt_topic'
  , 'mqtt_host'
  , 'mqtt_port'
  , 'meter_serial_port'
))

# GLOBALS
DBConn = None
myMeterId = '000000000000'
meterAtable = 'NotARealTableIHope'
meterBtable = 'NotARealTableIHope'
dontWriteDb = True

#  Some state saving variables for computing differences.
# Used in publishMeterData
prevTimeNow = None
prevCuFtWater = None
prevWaterWh = None


#####  Define logging
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
            logPath=""
        for p in config_dict['handlers'].keys():
            if 'filename' in config_dict['handlers'][p]:
                logFileName = os.path.join(logPath, config_dict['handlers'][p]['filename'])
                config_dict['handlers'][p]['filename'] = logFileName
        logging.config.dictConfig(config_dict)
    except Exception as e:
        print("loading logger config from file failed.")
        print(e)
        pass

logger = logging.getLogger(__name__)
logger.info('logger name is: "%s"', logger.name)

#  Generate a timezone for  LocalStandardTime
#  Leaving off zone name from timezone creator generates UTC based name which may be more meaningful.
localStandardTimeZone = datetime.timezone(-datetime.timedelta(seconds=time.timezone))
logger.debug('LocalStandardTime ZONE is: %s'%localStandardTimeZone)

####  LOCAL FUNCTIONS
def ekm_logger(output_string):
    """ Simple print predefined module level logging callback.

    Args:
        output_string (str): string to output.

    Returns:

    """
    logger.debug(output_string)
    pass

ekm_set_log(ekm_logger)
ekm_set_log_level(10)       # log EVERYTHING

def GetConfigFilePath():
    fp = os.path.join(ProgPath, 'secrets.ini')
    if not os.path.isfile(fp):
        fp = os.environ['PrivateConfig']
        if not os.path.isfile(fp):
            logger.error('No configuration file found: %s', fp)
            sys.exit(1)
    logger.info('Using configuration file at: %s', fp)
    return fp

def getDatetimeFromEKM(estr='19051605223500'):
    #  Meter is always set to local standard time - avoids time change problems.
    logger.debug('Getting datetime from EKM string "%s"'%estr)
    return datetime.datetime(int(estr[0:2])+2000,
        int(estr[2:4]),
        int(estr[4:6]),
        hour = int(estr[8:10]),
        minute = int(estr[10:12]),
        second = int(estr[12:14]),
        tzinfo = localStandardTimeZone)

def makeMeterDataMsg(myMeter = None):
    global prevTimeNow, prevCuFtWater, prevWaterWh

    # Compute inteval in seconds since last time we were called
    timeNow = time.time()
    if prevTimeNow is None: prevTimeNow = timeNow - 60  # Ensure we don't divide by zero
    timeInterval = timeNow - prevTimeNow
    logger.debug('Now is %s, prev was %s, diff is %s'%(timeNow, prevTimeNow, timeInterval))
    prevTimeNow = timeNow

    meterTime = getDatetimeFromEKM(myMeter.getFieldA(Field.Meter_Time))
    logger.debug('Pulse count 3 (as str): "%s"; (as int) %s'%(myMeter.getFieldA(Field.Pulse_Cnt_3), myMeter.getFieldANative(Field.Pulse_Cnt_3)))
    cuFtWater          = myMeter.getFieldANative(Field.Pulse_Cnt_3) * 0.1
    waterSysKwh        = myMeter.getFieldANative(Field.Pulse_Cnt_1) + myMeter.getFieldANative(Field.Pulse_Cnt_2)
    #  waterSysKwh is actually WattHours at this point.
    #  compute some differences
    if prevCuFtWater is None: prevCuFtWater = cuFtWater
    if prevWaterWh is None:   prevWaterWh = waterSysKwh

    GPM = (cuFtWater - prevCuFtWater) / timeInterval
    prevCuFtWater = cuFtWater
    GPM = GPM * 60      # convert from Ft^3 / S to Ft^3 / M
    GPM = GPM * 7.4805194703778 # convert from Ft^3 to Gallons

    # waterSysKwh andd prevWaterWh both in Watt-Hours; divide difference by timeInterval in hours
    waterSysWatts = (waterSysKwh - prevWaterWh) / (timeInterval / 3600)
    prevWaterWh = waterSysKwh
    waterSysKwh = waterSysKwh / 1000    # convert from Watt-Hours to KiloWatt-Hours

    """ Pulse output state at time of read.  V4 Omnimeters.
    Relay1/Relay2           Relay2 controls water valve
    =======  =    -1 =
    OffOff   1      0
    OffOn    2      1
    OnOff    3      2
    OnOn     4      3
    =======  =      =
        subtract 1 from given value; then relay1 is the "2" bit, and relay2 is the "1" bit.
            For my setup, the water valve is OFF if the relay is ON.
    """

    MainWaterValveState = 'OFF' if ((myMeter.getFieldANative(Field.State_Out) - 1) & 1) == 1 else 'ON'

    outputDict = {}
    outputDict["ComputerTime"]      = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
    outputDict["MeterTime"]         = meterTime.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    outputDict["MeterId"]           = myMeter.getFieldA(Field.Meter_Address)
    outputDict["MeterType"]         = myMeter.getFieldA(Field.Model)
    outputDict["HouseKWH"]          = round(myMeter.getFieldANative(Field.kWh_Tot), 3)
    outputDict["HouseWatts"]        = round(myMeter.getFieldANative(Field.RMS_Watts_Tot), 0)
    outputDict["CuFtWater"]         = round(cuFtWater, 2)
    outputDict["GalPerMin"]         = round(GPM, 3)
    outputDict["WaterKWH"]          = round(waterSysKwh, 3)
    outputDict["WaterWatts"]        = round(waterSysWatts, 1)
    outputDict["MainWaterValve"]    = MainWaterValveState
    outMsg = json.JSONEncoder().encode(outputDict)
    logger.debug('Publishing meter data: "%s"'%outMsg)
    return outMsg


##########################   MAIN
def main():

    global DBConn, myMeterId, meterAtable, meterBtable, dontWriteDb, localStandardTimeZone

    ## Determine the complete file paths for the config file and the graph definitions file.
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    configFile = GetConfigFilePath()
    # configFileDir = os.path.dirname(configFile)

    ##  Open up the configuration file and extract some parameters.
    config.read(configFile)
    cfgSection = ProgFile+"/"+os.environ['HOST']
    logger.info("INI file cofig section is: %s", cfgSection)
    # logger.debug('Config section has options: %s'%set(config.options(cfgSection)))
    # logger.debug('Required options are: %s'%RequiredConfigParams)
    if not config.has_section(cfgSection):
        logger.critical('Config file "%s", has no section "%s".', configFile, cfgSection)
        sys.exit(2)
    if len( RequiredConfigParams - set(config.options(cfgSection))) > 0:
        logger.critical('Config  section "%s" does not have all required params: "%s", it has params: "%s".', cfgSection, RequiredConfigParams, set(config.options(cfgSection)))
        logger.debug('The missing params are: %s'%(RequiredConfigParams - set(config.options(cfgSection)),))
        sys.exit(3)

    cfg = config[cfgSection]

    parser = argparse.ArgumentParser(description = 'Display graphs of home parameters.\nDefaults to show all.')
    parser.add_argument("-m","--meterId", dest="meterId", action="store", default=cfg['meter_id'], help="Numeric Id of EKM meter to read.")
    parser.add_argument("-i", "--interval", dest="interval", action="store", default='1', help="The interval in munutes between successive meter reads.")
    parser.add_argument("-r", "--repeatCount", dest="repeatCount", action="store", default='0', help="Number of times to read meters; 0 => forever.")
    parser.add_argument("-n", "--a_to_b_ratio", dest="aToBRatio", action="store", default='15', help="Number of times to read A data from V4 meters before reading B data.\n"
                                                                                                    "If zero don't read B data.")
    parser.add_argument("-s", "--serial_port", dest="serialPort", action="store", default=cfg['meter_serial_port'], help="The serial port to which the EKM meter is connected.")
    parser.add_argument("-W", "--dontWriteToDB", dest="noWriteDb", action="store_false", default=True, help="Don't write to database [during debug defaults to True].")
    parser.add_argument("-v", "--verbosity", dest="verbosity", action="count", help="increase output verbosity", default=0)
    args = parser.parse_args()
    # Verbosity = args.verbosity
    dontWriteDb = args.noWriteDb
    logger.debug('Write to DB? %s'%(not dontWriteDb))

    logger.debug('Connecting to meter on serial port: %s'%args.serialPort)

    myMeterIdInt = int(args.meterId)
    myMeterId = '%012d'%myMeterIdInt
    logger.debug('myMeterId is: %s'%myMeterId)
    if 0 < myMeterIdInt < 300000000:
        logger.critical('EKM V3 meters are not supported!')
        exit(2)

    meterAtable = myMeterId + cfg['meter_table_a_suffix']
    meterBtable = myMeterId + cfg['meter_table_b_suffix']
    logger.debug('meterAtable is "%s"'%meterAtable)
    logger.debug('meterBtable is "%s"'%meterBtable)

    #  Prepare MQTT parameters
    mqttTopic  = cfg['mqtt_topic']
    mqttPort   = int(cfg['mqtt_port'])
    mqttHost   = cfg['mqtt_host']

    ############  setup database connection
    user = cfg['inserter_user']
    pwd  = cfg['inserter_password']
    host = cfg['inserter_host']
    port = int(cfg['inserter_port'])
    schema = cfg['inserter_schema']
    logger.info("user %s"%(user,))
    logger.info("pwd %s"%(pwd,))
    logger.info("host %s"%(host,))
    logger.info("port %d"%(port,))
    logger.info("schema %s"%(schema,))

    DBConn = pymysql.connect(host=host, port=port, user=user, password=pwd, database=schema, binary_prefix=True, charset='utf8mb4')
    logger.debug('DBConn is: %s'%DBConn)

    ###  Connect to database and check to see if tables exist.
    with DBConn.cursor() as cursor:
        logger.info("Insertion connection to database established.")
        query = "SHOW TABLES LIKE '%s%%'"%myMeterId
        logger.debug('Checking database for message tables with query: %s'%query)
        cursor.execute(query)
        requiredTables = [meterAtable.lower(), meterBtable.lower()]
        for r in cursor:
            logger.debug('Checking if %s is a required table.' % r[0])
            if r[0].lower() in requiredTables:
                requiredTables.remove(r[0].lower())
                logger.debug('Table %s is in the database.' % (r[0],))
                if len(requiredTables) == 0:
                    break
        if len(requiredTables) > 0:
            logger.warning('Not all required tables are in the database; creating missing tables.')
            for ntn in requiredTables:
                logger.debug('Creating table: %s'%ntn)
                try:
                    query = 'CREATE TABLE `{schema}`.`{newTableName}` LIKE `{schema}`.`RawMeterData`'.format(schema=schema, newTableName=ntn)
                    if dontWriteDb:
                        logger.debug('NOT creating table with query: "%s"'%query)
                    else:
                        logger.debug('Creating table with query: "%s"'%query)
                        conn.execute(text(query))
                except:
                    raise
            logger.debug('Created required database tables.')
        else:
            logger.debug('Found all required tables in database.')

    #  Generate a timezone for  LocalStandardTime
    #  Leaving off zone name from timezone creator generates UTC based name which may be more meaningful.
    localStandardTimeZone = datetime.timezone(-datetime.timedelta(seconds=time.timezone))
    logger.debug('LocalStandardTime ZONE is: %s'%localStandardTimeZone)

####    9       wait till next "top of the minute"
    intervalSec = int(args.interval) * 60
    if intervalSec < 60:
        logger.warning('Looping intervals less than 1 minute not supported.  Set to 1 minute.')
        intervalSec = 60
    secSinceEpoch = time.time()
    sleepLength = intervalSec - secSinceEpoch % intervalSec
    bIntervalSec = intervalSec * int(args.aToBRatio)
    nextBTime = int(secSinceEpoch + (bIntervalSec - secSinceEpoch  % bIntervalSec)) - 10        # 10 sec fudge factor
    logger.debug("Sleep for %s sec."%sleepLength)
    time.sleep(sleepLength)
    logger.debug('Slept for %s seconds.  It is now: %s'%(sleepLength, datetime.datetime.now().isoformat()))

    dayNumber = int(secSinceEpoch / 86400) - 1      #  number of days since epoch till yesterday

    with DBConn.cursor() as cursor, SerialPort(args.serialPort) as sp, V4Meter(myMeterId, sp) as myMeter:
        try:
####    10      Loop the number of times specified
            loopCount = int(args.repeatCount)
            if loopCount == 0: loopCount = 1000000000   #  Essentially keep going forever
            while loopCount > 0:
                logger.debug('Entering read/store loop with loop count = %s'%loopCount)
####    11          set state of water valve based on magic water valve file
####                    (as a by-product, A data is read)
                itsWet = os.path.exists(os.path.expandvars('${HOME}/.WeatherWet'))
                waterOff = None
                if itsWet:
                    logger.debug('It is wet out there; turn OFF main water valve.')
                    myMeter.setRelay(RelayInterval.Hold, Relay.Relay2, RelayState.RelayOpen)
                    waterOff = 1
                else:
                    logger.debug('It is dry out there; turn ON main water valve.')
                    myMeter.setRelay(RelayInterval.Hold, Relay.Relay2, RelayState.RelayClose)
                    waterOff = 0

####    12          log raw A data to database
####    13          update database to reflect new valve state
                logger.debug('Length of response A is: %s'%len(myMeter.m_raw_read_a))
                queryValueDict = {}
                queryValueDict['MeterTime'] = getDatetimeFromEKM(myMeter.getFieldA(Field.Meter_Time))
                queryValueDict['MeterId'] = myMeter.getFieldA(Field.Meter_Address)
                queryValueDict['DataType'] = 'V4A'
                queryValueDict['MeterType'] = myMeter.getFieldA(Field.Model)
                queryValueDict['MeterData'] = myMeter.m_raw_read_a.encode('ascii')
                queryValueDict['WaterOff'] = waterOff

                query = """INSERT INTO `{schema}`.`{table}` 
                (MeterTime, MeterId, DataType, MeterType, WaterOff, MeterData) 
                VALUES (%(MeterTime)s, %(MeterId)s, %(DataType)s, %(MeterType)s, %(WaterOff)s, %(MeterData)s)""".format(schema = schema,
                    table = meterAtable)
                logger.debug('Response A insertion query is: %s'%query)
                if dontWriteDb:
                    logger.debug('NOT inserting into A table with query: "%s"'%cursor.mogrify(query, queryValueDict))
                else:
                    logger.debug('Inserting into A table with query: "%s"'%cursor.mogrify(query, queryValueDict))
                    cursor.execute(query, queryValueDict)
                    DBConn.commit()

####    14          publish selected/computed A data to MQTT
                publish.single(mqttTopic, payload = makeMeterDataMsg(myMeter), hostname = mqttHost, port = mqttPort)


####    15          if "time to read B"
                if time.time() > nextBTime:
                    logger.debug('It is %s, time to read "B" data.'%datetime.datetime.now().isoformat())
####    16              update "time to read B"
                    nextBTime += bIntervalSec
####    17              read B data
                    myMeter.request()           # gets A and B
####    18              log raw B data to database
                    queryValueDict = {}
                    queryValueDict['MeterTime'] = getDatetimeFromEKM(myMeter.getFieldB(Field.Meter_Time))
                    queryValueDict['MeterId'] = myMeter.getFieldB(Field.Meter_Address)
                    queryValueDict['DataType'] = 'V4B'
                    queryValueDict['MeterType'] = myMeter.getFieldB(Field.Model)
                    queryValueDict['MeterData'] = myMeter.m_raw_read_b.encode('ascii')
                    queryValueDict['WaterOff'] = 0
                    query = """INSERT INTO `{schema}`.`{table}` 
                    (MeterTime, MeterId, DataType, MeterType, WaterOff, MeterData) 
                    VALUES (%(MeterTime)s, %(MeterId)s, %(DataType)s, %(MeterType)s, %(WaterOff)s, %(MeterData)s)""".format(schema = schema,
                        table = meterBtable)
                    logger.debug('Response B insertion query is: %s'%query)
                    if dontWriteDb:
                        logger.debug('NOT inserting into B table with query: "%s"'%cursor.mogrify(query, queryValueDict))
                    else:
                        logger.debug('Inserting into B table with query: "%s"'%cursor.mogrify(query, queryValueDict))
                        cursor.execute(query, queryValueDict)
                        DBConn.commit()

####    19          if it is a new day
                today = int(secSinceEpoch / 86400)
                if today != dayNumber:
                    logger.debug("It's a new day; set the time in the meter.")
                    dayNumber = today
####    20              set local standard time to meter
                    myMeter.setTimeFromDateTime(datetime.datetime.now(localStandardTimeZone))

####    21          if magic shutdown file exists, exit loop, cleanup and exit
                magicQuitPath = os.path.expandvars('${HOME}/.CloseReadEKM')
                if os.path.exists(magicQuitPath):
                    logger.debug('Quitting because magic file exists.')
                    logger.debug('Delete magic file.')
                    os.remove(magicQuitPath)
                    break

                loopCount = loopCount - 1
                if loopCount == 0:
                    logger.debug('Loop counter exhausted.')
                    break        #  No point in waiting if just going to quit
                else:
                    logger.debug('Keep going %s more times.'%loopCount)

####    22          wait till next time to read A
                sleepLength = intervalSec - time.time() % intervalSec
                logger.debug("Sleep for %s sec."%sleepLength)
                time.sleep(sleepLength)
                logger.debug('Slept for %s seconds.  It is now: %s'%(sleepLength, datetime.datetime.now().isoformat()))

        finally:
            pass

    DBConn.close()
    # if sp.m_ser.is_open:
    #     logger.info('At program end, serial port is open, close it.')
    #     sp.closePort()
    # logger.debug('At end, serial port is open? %s'%sp.m_ser.is_open)

    logger.info('             ##############   ReadEKM All Done   #################')

if __name__ == "__main__":
    main()
    pass
