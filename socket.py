from __future__ import annotations
from dataclasses import dataclass, field
import socket
from threading import Thread
from node import Node
from settings import (
    BROADCAST_HOST,
    BROADCAST_PORT,
    COLLECT_PK_LIST_PREFIX,
    PUBLIC_KEY_BROADCAST_PREFIX,
)
from rich import print


class BroadcastSocket(socket.socket):
    node: Node
    listen_thread: Thread

    def __init__(
        self, node: Node, host: str = BROADCAST_HOST, port: int = BROADCAST_PORT
    ):
        super().__init__(socket.AF_INET, socket.SOCK_DGRAM)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.bind((host, port))
        self.node = node

    def _listen_to_broadcast(self):
        while True:
            data, addr = self.recvfrom(1024)
            message = data.decode("utf-8")
            print(f"message: {message} from {addr}")
            self.parse_message(message=message)

    def parse_message(self, message: str):
        parser = Parser(message=message)
        if parser.is_pk_broadcast_message:
            # someone broadcasted their pk, so add it to your list
            self.node.add_public_key(message=message)
        elif parser.is_pk_collection_message:
            # someone wants to collect all the pks, so broadcast yours
            Broadcaster.broadcast_public_key(node=self.node, socket=self)

    def start_listen(self):
        print("Listening...")
        self.listen_thread = Thread(target=self._listen_to_broadcast)
        self.listen_thread.start()

    def broadcast(self, message: str):
        Broadcaster.broadcast(message_prefix="", message=message, socket=self)


class Broadcaster:
    @staticmethod
    def broadcast(message_prefix: str, message: str, socket: BroadcastSocket):
        message = bytes(f"{message_prefix}{message}", "utf-8")
        socket.sendto(message, ("<broadcast>", BROADCAST_PORT))

    @staticmethod
    def broadcast_public_key(node: Node, socket: BroadcastSocket):
        Broadcaster.broadcast(
            message_prefix=PUBLIC_KEY_BROADCAST_PREFIX,
            message=node.pk,
            socket=socket,
        )

    @staticmethod
    def collect_public_keys(socket: BroadcastSocket):
        Broadcaster.broadcast(
            message_prefix=COLLECT_PK_LIST_PREFIX,
            message="",
            socket=socket,
        )


@dataclass
class Parser:
    message: str
    is_pk_broadcast_message: bool = field(init=False, default=False)
    is_pk_collection_message: bool = field(init=False, default=False)

    def __post_init__(self):
        if self.message.startswith(PUBLIC_KEY_BROADCAST_PREFIX):
            self.is_pk_broadcast_message = True
        elif self.message.startswith(COLLECT_PK_LIST_PREFIX):
            self.is_pk_collection_message = True
