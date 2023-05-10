from multiprocessing import Process, Event, Queue, Lock
from src.base import EdgiseBase
import time




class WashingCycle(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, washcycle_q: Queue, output_q: Queue,
                 wf_sensor_q: Queue, ac_sensor_q: Queue, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._washcycle_q: Queue = washcycle_q
        self._wf_sensor_q: Queue = wf_sensor_q
        self._ac_sensor_q: Queue = ac_sensor_q
        self._output_q: Queue = output_q

        Process.__init__(self)
        EdgiseBase.__init__(self, name=self._name, logging_q=logging_q)

    def run(self) -> None:
        self.info("Starting Washing Cycle monitor")

        while not self._stop_event.is_set():
            # poll waterflow sensor and wait for first measurment
            water_trigger = self._wf_sensor_q.get()
            if water_trigger > 0:
                # wait for ac measurement
                start_power = self._ac_sensor_q.get()
                start_time = time.time()
                # washing cycle should take 1 hour?
                while time.time() - start_time < 3600:
                    measured_power = self._ac_sensor_q.get_nowait()
                    measured_water = self._wf_sensor_q.get_nowait()



            else:
                time.sleep(5)



        time.sleep(3)
