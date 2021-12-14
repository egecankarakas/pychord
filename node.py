import os
import asyncio
import settings
import logging
import socket
import time

from base_node import BaseNode


class HostnameFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = HostnameFilter.hostname
        return True

handler = logging.StreamHandler()
handler.addFilter(HostnameFilter())
handler.setFormatter(logging.Formatter('%(asctime)s %(hostname)s: %(message)s', datefmt='%b %d %H:%M:%S'))
log=logging.getLogger('Chord')
log.addHandler(handler)

class Node(BaseNode):
    def __init__(self, ip, bootstrap_server=None) -> None:
        super().__init__()
        self.ip=ip
        self.task_update_periodically=None
        self.bootstrap_server=bootstrap_server
        self.joined=False
    
    async def run(self,loop):
        self._server = await asyncio.start_server(self.handle, self.ip, settings.CHORD_PORT)
        self.task_update_periodically = loop.create_task(self.update_periodically())
        await self.task_update_periodically

    async def update_periodically(self):
        log.info('Started Updating Periodically!')
        while True:
            if not self.joined:
                if self.bootstrap_server:
                    log.info('Joining Chord Ring!')
                    self.join()
                else:
                    log.info('Waiting for others to join the ring!')
                    time.sleep(1)
            log.debug('Stabilizing')
        # pass

    async def stop(self):
        if self.task_update_periodically:
            self.task_update_periodically.close()

    async def handle(self, stream_reader, stream_writer):
        log.debug(f'Reader:{stream_reader} \n Writer:{stream_writer}')
        pass

    async def join(self):
        pass

    