import cv2
import acapture
import time
import numpy as np
import asyncio
import logging

from hyperpeer import Peer, PeerState
import ssl
from stream_manager_constants import HP_SERVER, SERVER_PORT


class VideoCapture:
    def __init__(self, video_path, frame_consumer, is_file=False):
        self.frame_consumer = frame_consumer
        # if is_file: 
        #     self.video = acapture.open(video_path, loop=True)
        # else:
        #     self.video = acapture.open(video_path)
        self.video = cv2.VideoCapture(video_path)
        self.width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))  # uses given video width and height
        self.height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.num_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.video.get(5)
        self.is_file = is_file
        print('Reading video ', video_path)
        print(self.width, self.height, self.num_frames, self.fps)
        # self.frame_index = 0
        # self.timestamp = self.frame_index / self.fps
        # self.current_frame = np.random.rand(int(self.width * 9 / 16), self.width, 3)
        # self.current_frame = np.uint8(self.current_frame * 100)
        self.last_frame_time = time.time()
        # self.frame_period = 1 / self.fps
         
    async def start(self, ready_event):
        ready_event.set()
        try:
            while True:
                if self.is_file:
                    elapsed_frame_time = time.time() - self.last_frame_time
                    if elapsed_frame_time < 1 / self.fps:
                        await asyncio.sleep(1 / self.fps - elapsed_frame_time)

                # if self.frame_index == self.num_frames:
                #     self.frame_index = 1 #Or whatever as long as it is the same as next line
                #     self.video.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)

                # for frame_index in range(1, num_frames + 1):
                # Read a new frame
                frame_ok, self.current_frame = self.video.read()
                if not frame_ok:
                    await asyncio.sleep(0.01)
                else:
                    # self.frame_index += 1
                    # self.timestamp = self.frame_index / self.fps
                    self.last_frame_time = time.time()
                    self.frame_consumer(self.current_frame)
        except:
            ready_event.clear()
            raise

class StreamCapture:
    def __init__(self, peer_id, frame_consumer, data_handler=None):
        ssl_context = ssl.create_default_context()
        ssl_context.options |= ssl.OP_ALL
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        hp_server_address = HP_SERVER +':'+ SERVER_PORT
        self.peer = Peer('wss://' + hp_server_address, peer_type='deep_input', id=peer_id, frame_consumer=frame_consumer, ssl_context=ssl_context)
        self.peer.add_data_handler(data_handler)
        self.remotePeerId = None

    async def start(self, ready_event):
        await self.peer.open()
        while True:
            self.remotePeerId = await self.peer.listen_connections()
            logging.info(f'[Stream_capture]: Connection request from peer: {self.remotePeerId}')
            await self.peer.accept_connection()
            ready_event.set()
            await self.peer.disconnection_event.wait()
            ready_event.clear()
            while self.peer.readyState != PeerState.ONLINE:
                await asyncio.sleep(0.2)

    

