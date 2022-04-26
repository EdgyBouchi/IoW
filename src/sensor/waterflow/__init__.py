import json
from multiprocessing import Process, Event, Queue, Lock

from src.base import EdgiseBase

import RPi.GPIO as GPIO
import time

#
# def count_sensor_pulse(counter_tuple):
#     if counter_tuple[0]:
#         counter_tuple[1] += 1

global pulse_count
pulse_count = 0

class WaterflowSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, washcycle_q: Queue, output_q: Queue,
                 config_dict, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._washcycle_q: Queue = washcycle_q
        self._output_q: Queue = output_q
        self._config_dict = config_dict
        self._name = self._config_dict['name']
        # self.pulse_count = 0
        # self.start_counter = 0
        self.pulses = {}
        self.limit_dict = 60
        self.time_tracker = 0.0

        self.pulse_count_q = Queue()

        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(self._config_dict['Pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # GPIO.add_event_detect(self._config_dict['Pin'], GPIO.FALLING,
        #                       callback=lambda x: count_sensor_pulse((self.start_counter, self.pulse_count)))

        Process.__init__(self)
        EdgiseBase.__init__(self, name=self._name, logging_q=logging_q)

        # config = {
        #           "PINNR":int,
        #           "SensorI    bD":int,
        #           "Unit":"cm"
        #           "SensorType":""
        #           }

    def run(self) -> None:
        self.info("Starting Waterflow sensor")
        global pulse_count
        pulse_count = 0

        def count(count_q):
            # if GPIO.input(13):
            global pulse_count
            pulse_count += 1
            count_q.put_nowait(pulse_count)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._config_dict['Pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self._config_dict['Pin'], GPIO.RISING, callback=lambda x: count(self.pulse_count_q))

        while not self._stop_event.is_set():

            while not self.pulse_count_q.empty():
                pulse_count = self.pulse_count_q.get_nowait()

                # self.pulse_count_q.put_nowait(0)

            # Keeping values together with timestamp in
            current_time = time.time()
            self.pulses[str(current_time)] = pulse_count

            pulses = [float(i) for i in self.pulses.values()]
            timestamps = [float(i) for i in self.pulses.keys()]
            timestamps.sort()

            if len(timestamps) > self.limit_dict:
                self.pulses.pop(str(timestamps[0]))

            # pulses over a minute
            pulses_min = 0.0
            for i in pulses:
                pulses_min += i

            # unused
            start_min_time = timestamps[0]

            # push values every 10 seconds
            if pulse_count > 0 and self.time_tracker + float(10) <= time.time():
                self.time_tracker = time.time()

                # https://abra-electronics.com/sensors/sensors-liquid-flow/flow-sensor-yf-b6.html
                # Frequency(Pulse / second): F = 6.6 * Q (Liter / second)
                # => Q(L/s) = F / 6.6

                raw_val = pulse_count
                flow_s = raw_val / 6.6
                flow_min = pulses_min / 6.6
                flow_h = (pulses_min * 60) / 6.6

                self.info("rawVal: {}".format(raw_val))
                self.info("currentTime: {}".format(current_time))
                self.info("flowSec: {} L/s".format(flow_s))
                self.info("flowMin: {} L/min".format(flow_min))
                self.info("flowHour: {}".format(flow_h))

            # self.start_counter = 1
            # time.sleep(1)
            # self.start_counter = 0
            # raw_val = self.pulse_count
            # flow_s = (raw_val / 396)
            # flow_min = (raw_val / 6.6)
            # flow_h = (raw_val * 60) / 6.6
            # self.pulse_count = 0
            # self.info("rawVal: {}".format(raw_val))
            # self.info("flowSec: {}".format(flow_s))
            # self.info("flowMin: {}".format(flow_min))
            # self.info("flowHour: {}".format(flow_h))

            data = {'waterflowSensorData': {
                'rawVal': raw_val,
                'flowSec': flow_s,
                'flowMin': flow_min,
                'flowHour': flow_h
            }}
            measurement = {'data': data}
            if not self._washcycle_q.empty():
                self._output_q.put_nowait({'event': json.dumps(measurement)})
            pulse_count = 0

        time.sleep(1)
