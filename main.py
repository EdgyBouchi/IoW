#!/usr/bin/python3

import os
from src.update import UpdateWatcher
from src.registration import RegisterProcess
from src.uploader import UploaderProcess
from src.edgise_mqtt import EdgiseMQTT
from src.device_state import DeviceState
from src.edgise_logger import EdgiseLogger
from src.sensor.electricty import ACSensor
from src.sensor.environment import EnvironmentSensor
from src.sensor.vibration import VibrationSensor
from src.sensor.waterflow import WaterflowSensor

from config import cfg
import queue
import time
import sys
from multiprocessing import Queue, Process
from multiprocessing import Event as mpEvent
from src.base import EdgiseBase
from typing import List


class Handler(EdgiseBase):
    def __init__(self, stop_event: mpEvent, logging_q: Queue, mqtt_send_q):
        self._logging_q = logging_q
        self._stop_event = stop_event
        EdgiseBase.__init__(self, name="MAIN", logging_q=logging_q)
        self.info('Initializing IoW application')

        # queues to sync data between threads
        self._data_q = Queue()
        self._cmd_q_update_watcher = Queue()
        self._cmd_q_main_process = Queue()
        self._mqtt_send_q = mqtt_send_q

        self._services: List = []

        # Initialize registration process
        self.registration_process = RegisterProcess(stop_event=self._stop_event,
                                                    logging_q=self._logging_q)

        self._services.append(self.registration_process)

        # Initialize update watcher
        self.update_watcher = UpdateWatcher(stop_event=self._stop_event,
                                            cmd_q=self._cmd_q_update_watcher,
                                            logging_q=self._logging_q)

        self._services.append(self.update_watcher)

        # Measurement dictionary
        measurement_dict = {}

        # Queues for AC sensor
        self._input_ac_q = Queue()
        self._output_ac_q = Queue()

        # connect AC sensor to analog port A0
        AC_sensor_config = {
            'name': "Electricity sensor",
            'pin': 0,
            'type': "INPUT",
            'unit': "mA",
        }
        test = 1
        print(type(test))
        config_list =[]
        config_list.append(test)
        print(type(config_list))

        self._ac_sensor = ACSensor(stop_event=self._stop_event,
                                   logging_q=self._logging_q,
                                   input_q=self._input_ac_q,
                                   output_q=self._output_ac_q,
                                   config_list=config_list
                                   )
        self._services.append(self._ac_sensor)

        # Queues for env sensor
        self._input_env_q = Queue()
        self._output_env_q = Queue()

        # connect env sensor to I2c
        self.env_sensor_config = {
            'name': "Environment Sensor",
            'Port': 1,
            'Address': 0x76,
            'Type': "INPUT",
            'Unit': ("°C", "hPa", " % rH"),
        }

        self._environment_sensor = EnvironmentSensor(stop_event=self._stop_event,
                                                     logging_q=self._logging_q,
                                                     input_q=self._input_env_q,
                                                     output_q=self._output_env_q,
                                                     kwargs=self.env_sensor_config
                                                     )
        self._services.append(self._environment_sensor)

        # Queues for vibration sensor
        self._input_vibration_q = Queue()
        self._output_vibration_q = Queue()

        # connect vibration sensor to analog port A2
        self._vibration_sensor_config = {
            'name': 'Vibration sensor',
            'Pin': 2,
            'Type': 'INPUT',
            'Unit': 'MHz',
        }

        self._vibration_sensor = VibrationSensor(stop_event=self._stop_event,
                                                 logging_q=self._logging_q,
                                                 input_q=self._input_vibration_q,
                                                 output_q=self._output_vibration_q,
                                                 kwargs=self._vibration_sensor_config
                                                 )
        self._services.append(self._vibration_sensor)

        # # Queues for  sensor
        # self._input_wf_q = Queue()
        # self._output_wf_q = Queue()
        #
        # # connect waterflow sensor to analog port
        # wf_sensor_config = {
        #     "name": "Waterflow sensor",
        #     "Pin": "0",
        #     "Type": "INPUT",
        #     "Unit": "MHz",
        # }
        #
        # self._wf_sensor = WaterflowSensor(stop_event=self._stop_event,
        #                                   logging_q=self._logging_q,
        #                                   input_q=self._input_wf_q,
        #                                   output_q=self._output_wf_q,
        #                                   config=wf_sensor_config
        #                                   )
        # self._services.append(self._wf_sensor)

        # Initialze MQTT process
        self.edgise_mqtt = EdgiseMQTT(stop_event=self._stop_event,
                                      data_q=self._data_q,
                                      cmd_qs=[self._cmd_q_update_watcher,
                                              self._cmd_q_main_process],
                                      send_q=self._mqtt_send_q,
                                      logging_q=self._logging_q)

        self._services.append(self.edgise_mqtt)

        # Initialize state process
        self.state_process = DeviceState(stop_event=self._stop_event,
                                         send_q=self._mqtt_send_q,
                                         logging_q=self._logging_q)

        self._services.append(self.state_process)

        # Initialize uploader process
        self.uploader_process = UploaderProcess(stop_event=self._stop_event,
                                                logging_q=self._logging_q)

        self._services.append(self.uploader_process)

        self.info('--------------------------- App initialization complete ---------------------------')

    def stop(self):
        self.info('Stopping services')
        self._stop_event.set()

        for service in self._services:
            service.join()

        self.info("Quitting.")

    def main(self):

        # platform = os.uname()
        # try:
        #     assert platform[1] == "raspberrypi"
        #     assert platform[4].startswith("arm")
        # except AssertionError:
        #     self.error("Not running on a Raspberry Pi. Quitting")
        #     exit()

        for service in self._services:
            service.start()

        # restart command handler
        while True:
            cmd = ""
            try:
                cmd = self._cmd_q_main_process.get_nowait()
            except queue.Empty:
                pass
            except Exception as e:
                try:
                    self._logging_q.put_nowait(self.error(f"Unknown exception : {e}"))
                except Exception as e:
                    print(f"SHITTY ERROR! {e}")

            if cmd == "RESTART":
                self.stop()
                break

            time.sleep(0.1)


if __name__ == '__main__':
    with open(
            f"{cfg.root_dir}/asciiart.telly") as f:  # The with keyword automatically closes the file when you are done
        print(f.read())

    logging_q = Queue()
    stop_event = mpEvent()
    mqtt_send_q = Queue()
    fake_stop = mpEvent()

    # Initialize a logging process that takes an incoming queue
    logging_process = EdgiseLogger(stop_event=fake_stop,  # Just for now
                                   incoming_q=logging_q,
                                   outgoing_q=mqtt_send_q)

    # Directly start logging process
    logging_process.start()

    handler = Handler(stop_event=stop_event,
                      logging_q=logging_q,
                      mqtt_send_q=mqtt_send_q)

    handler.main()

    # fake_stop.set()
    # logging_process.join()

    os.execv(sys.executable, ['python3'] + sys.argv)
