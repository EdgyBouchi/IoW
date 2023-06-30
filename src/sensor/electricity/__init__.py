import time

from math import sqrt
from multiprocessing import Process, Event, Queue, Lock
from src.base import EdgiseBase
from grove.adc import ADC
from config import cfg
import json

import queue


class ACSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, washcycle_q: Queue, output_q: Queue,
                 config_dict, resource_lock: Lock, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._washcycle_q: Queue = washcycle_q
        self._output_q: Queue = output_q
        self.RMS_voltage = 230
        self.VCC = 3.3
        self._config_dict = config_dict
        self._name = self._config_dict['name']
        self._threshold = self._config_dict['threshold']
        self.adc = ADC(address=self._config_dict['i2cAddress'])
        self.i2c_lock = resource_lock

        # hyteresis
        # these will be consecutive measurements above the threshold
        # needs to be configurable
        self._max_hysteresis_value = 4
        # temporar
        self._washcycle_threshold = 100
        self._washcycle_start_time = None
        # time in seconds in which start of a washcycle cannot be interrupted
        self._washcycle_max_elapsed_time = 600

        self._washcycle_counter = 0

        Process.__init__(self)
        EdgiseBase.__init__(self, name=self._name, logging_q=logging_q)

        # config = {
        #           "name":str
        #           "PINNR":int,
        #           "SensorI    bD":int,
        #           "Unit":"cm"
        #           "SensorType":""
        #           }

    def read_sensor(self):
        sample_time = 2
        start_time = time.time()
        sensor_max = 0
        self.info("start sampling")
        while (time.time() - start_time < sample_time):
            sensor_value = self.adc.read_raw(self._config_dict['pin'])
            if (sensor_value > sensor_max):
                sensor_max = sensor_value
        print("------------------------------------------------------------sensor value {}".format(sensor_max))
        return sensor_max

    def amplitude_current(self, sensor_value):
        return 2 * (float(sensor_value) / 4096 * self.VCC / 800 * 2000)  # 1:2000 coils -> A => 2000000 mA

    def RMS_current(self, amplitude_current):
        return amplitude_current / sqrt(2)

    def avg_power_consumption(self, RMS_current):
        return self.RMS_voltage * RMS_current

    def detect_washcycle(self):
        if self._washcycle_counter == self._max_hysteresis_value:
            #self._washcycle_counter = self._max_hysteresis_value
            if self._washcycle_q.empty():
                # there are enough consective measurements larger than the threshold, this indicated the start of a washcycle
                self._washcycle_q.put_nowait(True)
                self._washcycle_start_time = time.time()
                return
            self.info("there is still a washcycle running.")

        if self._washcycle_counter == 0:
           # self._washcycle_counter = 0
            if not self._washcycle_q.empty():
                elapsed_time = self._washcycle_start_time - time.time()
                if elapsed_time > self._washcycle_max_elapsed_time:
                    self.info("Condition to stop washcycle is met.")
                    self.info("Washcycle counter is: {}".format(self._washcycle_counter))
                    self.info("Elapsed time is: {}".format(elapsed_time))
                    try:
                        # stop washcycle
                        self._washcycle_q.get_nowait()
                        self._washcycle_start_time = None
                    except queue.Empty:
                        self.info("Could not consume washcycle queue.")
                        pass
                self.info("washcycle timer has not been exceeded yet.")
                self.info("Washcycle counter is: {}".format(self._washcycle_counter))
            self.info("No washcycle has been detected.")

    def run(self) -> None:
        self.info("Starting AC sensor")
        print(self._config_dict['name'])
        while not self._stop_event.is_set():
            raw_val = self.read_sensor()
            self.info("measured raw value: {}".format(raw_val))
            # increment threshold counter
            if raw_val >= self._washcycle_threshold:
                self._washcycle_counter += 1
            if raw_val < self._washcycle_threshold:
                self._washcycle_counter -= 1
            self.info("washcycle counter is: {}".format(self._washcycle_counter))
            self.detect_washcycle()

            if not self._washcycle_q.empty():
                self.info("a washcycle is running")
                # here we are in a washcycle
                self.info("Raw Value: {}".format(raw_val))
                amplitude_current = self.amplitude_current(raw_val)
                self.info("A I Value: {}".format(amplitude_current))
                rms_current = self.RMS_current(amplitude_current)
                self.info("RMS I Value: {}".format(rms_current))
                avg_power = self.avg_power_consumption(rms_current)
                self.info("AVG W Value: {}".format(avg_power))

                data = {'electricitySensorData': {
                    'rawVal': raw_val,
                    'currentAmp': amplitude_current,
                    'rmsCurrent': rms_current,
                    'avgPower': avg_power
                }}
                measurement = {'data': data}
                self._output_q.put_nowait({'event': json.dumps(measurement)})

            time.sleep(1)
