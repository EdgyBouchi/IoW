from multiprocessing import Process, Event, Queue, Lock

from src.base import EdgiseBase
from grove.modules.bme280 import bme280

import time
from config import cfg
import json


import smbus
import time
from ctypes import c_short
from ctypes import c_byte
from ctypes import c_ubyte


class EnvironmentSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, washcycle_q: Queue, output_q: Queue, config_dict,
                 resource_lock: Lock, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._washcycle_q: Queue = washcycle_q
        self._output_q: Queue = output_q
        self._config_dict = config_dict
        self.bme_sensor = bme280()
        self.i2c_lock = resource_lock

        # Set oversampling
        # bme280 class defines OVRS_x0, .._x1, .._x2, .._x4, .._x8, .._x16
        # set_oversampling(osrs_h(humidity), osrs_t(temperature), osrs_p(pressure))
        # Set_oversampling > OVRS_x0 to enable the measurement, OVRS_x0 disables the measurement
        self.bme_sensor.set_oversampling(bme280.OVRS_x16, bme280.OVRS_x16, bme280.OVRS_x16)

        # Set internal IIR filter coefficient. 0 = no filter
        self.iir_filter = bme280.filter_16
        self.bme_sensor.set_filter(self.iir_filter)

        # Know values for pressure correction
        self.current_level_from_sea = 103  # Know height from sealevel m
        self.current_sea_level_pressure = 1027.5  # Forecast data: current pressure at sealevel
        self.count = 0  # Just for counting delays
        self.calibration_set = 0  # Help bit

        self.bme_sensor_reader = Bme_Reader()
        Process.__init__(self)
        EdgiseBase.__init__(self, name=self._config_dict['name'], logging_q=logging_q)

    def calibration_sequence(self):
        response_time = (2 ** self.iir_filter) * 2
        while self.count < response_time:
            self.info("Wait for sensor to settle before setting compensation! {} s".format(response_time - self.count))
            self.count += 1
            # set mode to FORCE that is one time measurement
            # bme280.MODE_SLEEP, ...FORCE, ...NORMAL
            # If normal mode also set t_sb that is standby time between measurements
            # if not specified is set to 1000ms bme280.t_sb_1000
            # Returns 1 on success 0 otherwise
            if not self.bme_sensor.set_mode(bme280.MODE_FORCE):
                self.info("\nMode change failed!")

            # Measure raw signals measurements are put in bme280.raw_* variables
            # Returns 1 on success otherwise 0
            if not self.bme_sensor.read_raw_signals():
                self.info("\nError in measurement!")

            # Compensate the raw signals
            if not self.bme_sensor.read_compensated_signals():
                self.info("\nError compensating values")

            time.sleep(1)

        # count == response time
        self.bme_sensor.set_pressure_calibration(level=self.current_level_from_sea,
                                                 pressure=self.current_sea_level_pressure)
        self.count = response_time + 1
        self.calibration_set = 1
        # Update the compensated values because new calibration value is given
        if not self.bme_sensor.read_compensated_signals():
            self.info("\nError compensating values")
        self.info("Sensor compensation is set")
        self.info("response time reached, finished calibration sequence!")
        # self.bme_sensor.write_reset()
        return

    def run(self) -> None:
        self.info("Starting Environment sensor")

        self.calibration_sequence()
        while not self._stop_event.is_set():
            if self.calibration_set:
                # measurement = {'deviceId': cfg.deviceId,
                #                'projectId': cfg.projectId,
                #                'timeStamp': time.time()
                #                }

                with self.i2c_lock:
                    self.bme_sensor.read_raw_signals()
                    # time.sleep(1)
                    self.bme_sensor.read_compensated_signals()
                    #   Only works if pressure calibration is done with set_pressure_calibration()
                    altitude = self.bme_sensor.get_altitude(self.current_sea_level_pressure)
                    # self.bme_sensor.write_reset()
                    helper_temperature, helper_pressure , helper_humidity = self.bme_sensor_reader.get_sensor_values()

                # self.info out the data
                self.info("Temperature: {} deg".format(self.bme_sensor.temperature))
                self.info("Pressure: {} hPa, where correction is {} hPa, sensor reading is {} hPa".format(
                    self.bme_sensor.calibrated_pressure, self.bme_sensor.calibration_pressure,
                    self.bme_sensor.pressure))
                self.info(" values of the helper class:    temperature ; {}   pressure {} ,   humidity  {}%RH  ".format(helper_temperature,helper_pressure,helper_humidity))
                self.info("Humidity: {} %RH".format(self.bme_sensor.humidity))
                self.info(
                    "altitude from sea level: {}m, {}".format(
                        altitude, self.bme_sensor.calibrated_pressure + altitude / 8))

                data = {"environmentSensorData": {
                    #"temperature": self.bme_sensor.temperature,
                    "temperature": helper_temperature,
                    "pressureSensorReading": self.bme_sensor.pressure,
                    "pressureCorrrection": self.bme_sensor.calibration_pressure,
                    "pressure": self.bme_sensor.calibrated_pressure,
                    #"humidity": self.bme_sensor.humidity,
                    "humidity": helper_humidity,
                    "altitude": altitude
                    }
                }
                measurement = {'data': data}
                if not self._washcycle_q.empty():
                    self._output_q.put_nowait({'event': json.dumps(measurement)})
                time.sleep(10)

class Bme_Reader():

    DEVICE = 0x76


    def __init__(self):
        # Default device I2C address

        # Rev 2 Pi, Pi 2 & Pi 3 uses bus 1
                        # Rev 1 Pi uses bus 0
        self.bus = smbus.SMBus(1)
        time.sleep(1)
        print('init')

    def getShort(self,data,index):
        # return two bytes from data as a signed 16-bit value
        return c_short((data[index+1] << 8) + data[index]).value

    def getUShort(self,data,index):
        # return two bytes from data as an unsigned 16-bit value
        return (data[index+1] << 8) + data[index]

    def getChar(self,data,index):
        # return one byte from data as a signed char
        result = data[index]
        if result > 127:
            result -= 256
        return result

    def getUChar(self,data,index):
        # return one byte from data as an unsigned char
        result =  data[index] & 0xFF
        return result

    def readBME280ID(self,addr=DEVICE):
        # Chip ID Register Address
        REG_ID     = 0xD0
        (chip_id, chip_version) = self.bus.read_i2c_block_data(addr, REG_ID, 2)
        return (chip_id, chip_version)

    def readBME280All(self,addr=DEVICE):
        time.sleep(1)
        # Register Addresses
        REG_DATA = 0xF7
        REG_CONTROL = 0xF4
        REG_CONFIG  = 0xF5

        REG_CONTROL_HUM = 0xF2
        REG_HUM_MSB = 0xFD
        REG_HUM_LSB = 0xFE

        # Oversample setting - page 27
        OVERSAMPLE_TEMP = 2
        OVERSAMPLE_PRES = 2
        MODE = 1

        # Oversample setting for humidity register - page 26
        OVERSAMPLE_HUM = 2
        self.bus.write_byte_data(addr, REG_CONTROL_HUM, OVERSAMPLE_HUM)

        control = OVERSAMPLE_TEMP<<5 | OVERSAMPLE_PRES<<2 | MODE
        self.bus.write_byte_data(addr, REG_CONTROL, control)

        # Read blocks of calibration data from EEPROM
        # See Page 22 data sheet
        cal1 = self.bus.read_i2c_block_data(addr, 0x88, 24)
        cal2 = self.bus.read_i2c_block_data(addr, 0xA1, 1)
        cal3 = self.bus.read_i2c_block_data(addr, 0xE1, 7)

        # Convert byte data to word values
        dig_T1 = self.getUShort(cal1, 0)
        dig_T2 = self.getShort(cal1, 2)
        dig_T3 = self.getShort(cal1, 4)

        dig_P1 = self.getUShort(cal1, 6)
        dig_P2 = self.getShort(cal1, 8)
        dig_P3 = self.getShort(cal1, 10)
        dig_P4 = self.getShort(cal1, 12)
        dig_P5 = self.getShort(cal1, 14)
        dig_P6 = self.getShort(cal1, 16)
        dig_P7 = self.getShort(cal1, 18)
        dig_P8 = self.getShort(cal1, 20)
        dig_P9 = self.getShort(cal1, 22)

        dig_H1 = self.getUChar(cal2, 0)
        dig_H2 = self.getShort(cal3, 0)
        dig_H3 = self.getUChar(cal3, 2)

        dig_H4 = self.getChar(cal3, 3)
        dig_H4 = (dig_H4 << 24) >> 20
        dig_H4 = dig_H4 | (self.getChar(cal3, 4) & 0x0F)

        dig_H5 = self.getChar(cal3, 5)
        dig_H5 = (dig_H5 << 24) >> 20
        dig_H5 = dig_H5 | (self.getUChar(cal3, 4) >> 4 & 0x0F)

        dig_H6 = self.getChar(cal3, 6)

        # Wait in ms (Datasheet Appendix B: Measurement time and current calculation)
        wait_time = 1.25 + (2.3 * OVERSAMPLE_TEMP) + ((2.3 * OVERSAMPLE_PRES) + 0.575) + ((2.3 * OVERSAMPLE_HUM)+0.575)
        time.sleep(wait_time/1000)  # Wait the required time  

        # Read temperature/pressure/humidity
        data = self.bus.read_i2c_block_data(addr, REG_DATA, 8)
        pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        hum_raw = (data[6] << 8) | data[7]

        #Refine temperature
        var1 = ((((temp_raw>>3)-(dig_T1<<1)))*(dig_T2)) >> 11
        var2 = (((((temp_raw>>4) - (dig_T1)) * ((temp_raw>>4) - (dig_T1))) >> 12) * (dig_T3)) >> 14
        t_fine = var1+var2
        temperature = float(((t_fine * 5) + 128) >> 8);

        # Refine pressure and adjust for temperature
        var1 = t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * dig_P6 / 32768.0
        var2 = var2 + var1 * dig_P5 * 2.0
        var2 = var2 / 4.0 + dig_P4 * 65536.0
        var1 = (dig_P3 * var1 * var1 / 524288.0 + dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * dig_P1
        if var1 == 0:
            pressure=0
        else:
            pressure = 1048576.0 - pres_raw
            pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
            var1 = dig_P9 * pressure * pressure / 2147483648.0
            var2 = pressure * dig_P8 / 32768.0
            pressure = pressure + (var1 + var2 + dig_P7) / 16.0

        # Refine humidity
        humidity = t_fine - 76800.0
        humidity = (hum_raw - (dig_H4 * 64.0 + dig_H5 / 16384.0 * humidity)) * (dig_H2 / 65536.0 * (1.0 + dig_H6 / 67108864.0 * humidity * (1.0 + dig_H3 / 67108864.0 * humidity)))
        humidity = humidity * (1.0 - dig_H1 * humidity / 524288.0)
        if humidity > 100:
            humidity = 100
        elif humidity < 0:
            humidity = 0

        return temperature/100.0,pressure/100.0,humidity

    def get_sensor_values(self):

        #(chip_id, chip_version) = self.readBME280ID()
        #print "Chip ID     :", chip_id
        #print "Version     :", chip_version
        
        temperature,pressure,humidity = self.readBME280All()
        return temperature,pressure,humidity
        #print "Temperature : ", temperature, "C"
        #print "Pressure : ", pressure, "hPa"
        #print "Humidity : ", humidity, "%"


