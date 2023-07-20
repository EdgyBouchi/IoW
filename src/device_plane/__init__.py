import subprocess
import time
from config import cfg
from threading import Thread, Event
import os
import queue
from multiprocessing import Queue
from src.base import EdgiseBase


class DevicePlanceOnboarder(Thread, EdgiseBase):
    def __init__(self, stop_event: Event,cmd_q: Queue, logging_q: Queue, **kwargs):
        self._stop_event = stop_event
        Thread.__init__(self)
        EdgiseBase.__init__(self, name="DEVICEPLANE", logging_q=logging_q)
        self._cmd_q = cmd_q

    def run(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(0.1)
            cmd = ""
            try:
                cmd = self._cmd_q.get_nowait()
            except queue.Empty:
                pass

            if cmd == "DEVICEPLANE":
                self.info("Registering device on device plane.\n")
                self.info("Executing the following command: ")
                self.info("curl https://downloads.deviceplane.com/install.sh | VERSION=1.16.0 PROJECT=prj_1tLwDHWhgf8GmpA5TDoCrKMVSyg REGISTRATION_TOKEN=drt_1tLwDFq4ri9JC3AUGdXSHtaVR8I bash\n")
                retcode = subprocess.call([
                    'curl',
                    'https://downloads.deviceplane.com/install.sh',
                    '|',
                    'VERSION=1.16.0',
                    'PROJECT=prj_1tLwDHWhgf8GmpA5TDoCrKMVSyg',
                    'REGISTRATION_TOKEN=drt_1tLwDFq4ri9JC3AUGdXSHtaVR8I',
                    'bash'],shell=False)

                if not retcode:
                    self.info("could not onboard device on device plane\n")
                else:
                    self.info("device onboarded successfully\n")



        self.info(f"Quitting.")
