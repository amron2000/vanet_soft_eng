import sched
import time
from typing import Callable

from node import Node

scheduler = sched.scheduler(time.time, time.sleep)


class MessageScheduler:
    @staticmethod
    def setup_periodic_messaging(node: Node, task: Callable):
        while True:
            scheduler.enterabs(node.next_message_timestamp, 1, task)
            scheduler.run()
