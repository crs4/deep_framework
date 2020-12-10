import sys
from hyperpeer import Peer, PeerState
import asyncio
import subprocess
import pathlib
import ssl
import logging
import numpy
import os
import zmq
import time
from stream_manager_constants import *
from video_sources import VideoCapture, StreamCapture

from utils.socket_commons import send_data, recv_data

ROOT = os.path.dirname(__file__)
logging.basicConfig(level=logging.INFO)

logging.info('*** DEEP STREAM MANAGER v1.0.6 ***')

#ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
#ssl_context.load_verify_locations('cert.pem')

ssl_context = ssl.create_default_context()
ssl_context.options |= ssl.OP_ALL
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


class StreamManager:

    def __init__(self):        
        self.id = SOURCE_ID
        frame_consumer_to_client = None
        if SOURCE_TYPE == 'remote_client':
            frame_consumer_to_client = lambda f: self.create_deep_message(f)
        
        self.stream_capture = None
        self.source_ready = asyncio.Event()
        self.core_watchdog = asyncio.Event()
        self.stream_enable = asyncio.Event()
        self.__connection_reset()
        self.__socket_setup()

        datachannel_options = {
            'label': 'data_channel',
            'maxPacketLifeTime': None,
            'maxRetransmits': 0,
            'ordered': False,
            'protocol': ''
        }

        def frame_generator_to_client():
            logging.info(f'[{self.id}]: Generator started')
            self.generated_frames = 0

            while True:
                self.generated_frames+=1
                yield self.received_frame

        self.hp_server_address = HP_SERVER +':'+ SERVER_PORT
        self.peer = Peer('wss://' + self.hp_server_address, peer_type='deep_output', id=self.id,
                        frame_generator=frame_generator_to_client, frame_consumer=frame_consumer_to_client, ssl_context=ssl_context,
                        datachannel_options=datachannel_options, frame_rate=FRAME_RATE)
        self.capture_peer = None
    
    def __connection_reset(self):
        logging.info(f'[{self.id}]: Initializing connection variables')
        self.deafult_frame = numpy.random.rand(720, 1280, 3)
        self.deafult_frame = numpy.uint8(self.deafult_frame * 100)
        self.received_frame = self.deafult_frame
        self.processed_frame = self.received_frame
        self.received_frames = 0
        self.processed_frames = 0
        self.last_processed_frame = 0
        self.generated_frames = 0
        self.messages_sent = 0
        self.received_frames = 0
        self.remotePeerId = None
        self.source_peer_id = None
        self.source_metadata = None
        self.deep_delay = 0
        self.round_trip = 0
        self.processing_period = 0
        

    def __socket_setup(self):
        
        collector_list = COLLECTOR_PORTS.split(',')
        self.context = zmq.Context()
        self.sender_socket = self.context.socket(zmq.PUB)
        self.sender_socket.bind(PROT + '*:' + STREAM_OUT)

        self.collectors = []
        for coll_port in collector_list:

            receiver_socket = self.context.socket(zmq.PAIR)
            receiver_socket.bind(PROT +'*:'+ coll_port)
            self.collectors.append({'socket':receiver_socket})

        self.server_pair_socket = self.context.socket(zmq.PAIR)
        self.server_pair_socket.connect(PROT + HP_SERVER + ':' +SERVER_PAIR_PORT)


    def create_deep_message(self, frame):
        if not self.stream_enable.is_set():
            return
        self.received_frame = frame
        self.received_frames += 1
        capture_time = time.time()

        res = {'frame_idx': self.received_frames , 'vc_time': capture_time, 'frame_shape': frame.shape}
        if self.deep_delay < float(MAX_ALLOWED_DELAY) and self.processing_period < float(MAX_ALLOWED_DELAY):  
            send_data(self.sender_socket,[frame],0,False,**res)
        else:
            logging.info(f'[{self.id}]: Skipping frame: {str(self.received_frames)}, deep delay: {str(self.deep_delay)}, processing period: {str(self.processing_period)}')
        
        self.core_watchdog.set()


    async def receiver(self, socket):
        logging.info(f'[{self.id}]: Receiver started')
        self.processed_frames = 0
        last_receive_time = time.time()
        no_data_time = 0
        try:
            while True:
                await self.source_ready.wait()
                await self.stream_enable.wait()
                try:
                    received_data, __ = recv_data(socket,1,False)
                    # logging.info(f'[{self.id}]: received_data: {str(received_data)}')
                    received_data["rec_time"] = time.time()
                    self.deep_delay = received_data["rec_time"] - received_data["vc_time"]
                    self.processing_period = received_data["rec_time"] - last_receive_time
                    no_data_time = 0
                    self.processed_frames += 1
                    last_receive_time = received_data["rec_time"]
                    if self.peer.readyState == PeerState.CONNECTED:
                        self.messages_sent += 1
                        data_to_send = {
                            'type': 'data',
                            'received_frames': self.received_frames,
                            'processed_frames': self.processed_frames,
                            'generated_frames': self.generated_frames,
                            'messages_sent': self.messages_sent,
                            'last_frame_shape': self.received_frame.shape,
                            'round_trip': self.round_trip,
                            'deep_delay': self.deep_delay,
                            'processing_period': self.processing_period
                        }
                        data_merged = {**data_to_send,**received_data}
                        # logging.info(f'[{self.id}]: Sending data: {str(data_merged)}')
                        await self.peer.send(data_merged)
                except Exception as e:
                    self.processing_period = time.time() - last_receive_time
                    no_data_time += self.processing_period
                    if no_data_time > float(MAX_ALLOWED_DELAY) * 1.2:
                        # if no_data_time > 10 * float(MAX_ALLOWED_DELAY):
                        #     msg = f'No data from DEEP since  {str(no_data_time)} seconds. Reason: {str(e)}'
                        #     if self.peer.readyState == PeerState.CONNECTED:
                        #         await self.peer.send({'type': 'warning', 'messagge': msg })
                        #     logging.error(msg)
                        #     await asyncio.sleep(float(MAX_ALLOWED_DELAY) * 2)
                        #     # break
                        # else:

                        #     msg = f'High processing period: {str(no_data_time)}. Reason: {str(e)}' 
                        #     if self.peer.readyState == PeerState.CONNECTED:
                        #         await self.peer.send({'type': 'warning', 'messagge': msg})
                        #     logging.warning(msg)
                        #     await asyncio.sleep(float(MAX_ALLOWED_DELAY) * 0.5)

                        self.deep_delay = -1
                        self.processing_period = -1
                        last_receive_time = time.time()

                await asyncio.sleep(0.05)

        except asyncio.CancelledError as c:
            await asyncio.sleep(float(MAX_ALLOWED_DELAY))
            try:
                while True:
                    received_data, __ = recv_data(socket,1,False)
            except:
                logging.info(f'[{self.id}]: collector socket empty')
            raise c


    def on_remote_data(self, data):
        # logging.info(f'[{self.id}]: Remote message: {str(data)}')
        data_type = data['type']
        if data_type == 'acknowledge':
            try:
                self.round_trip = time.time() - data["rec_time"]
            except Exception as e:
                logging.error('error on data' + str(e))

        elif data_type == 'metadata':
            self.source_metadata = data['metadata']
            logging.info('Source metadata: ' + str(self.source_metadata))
    
    async def on_capture_data(self, data):
        self.source_metadata = data['metadata']
        logging.info('Source metadata: ' + str(self.source_metadata))
        if self.peer.readyState == PeerState.CONNECTED:
            await self.peer.send(data)

    async def task_monitor(self, tasks):
        while True:
            for task in tasks:
                if task.done():
                    try:
                        res = task.result()
                        logging.info(f'[{self.id}]: Task result: {res}')
                    except Exception as e:
                        logging.error(f'[{self.id}]: Task error: {str(e)}')
                        raise e
            await asyncio.sleep(1)

    async def core_watchdog_timer(self):
        while True:
            try:
                await asyncio.wait_for(self.core_watchdog.wait(), timeout=30)
            except asyncio.TimeoutError:
                logging.warning(f'[{self.id}]: Watchdog: timer set!')
                logging.info(f'[{self.id}]: Watchdog: sending default frame to core components...')
                res = {'frame_idx': 0, 'vc_time': time.time(), 'frame_shape': self.deafult_frame.shape}
                send_data(self.sender_socket,[self.deafult_frame],0,False,**res)
                await asyncio.sleep(2)
                # Empty collector socket
                for coll in self.collectors:
                    try:
                        while True:
                            __, __ = recv_data(coll['socket'],1,False)
                            logging.info(f'[{self.id}]: Watchdog: received collector data')  
                    except:
                        logging.info(f'[{self.id}]: Watchdog: collector socket empty')  
            self.core_watchdog.clear()

    async def receive_server_signaling(self,server_socket):
        logging.info('server_signaling started')
        while True:
            try:
                message = str(server_socket.recv(flags=zmq.NOBLOCK), encoding='utf-8')
                logging.info(f'Server message: {message}')
                if message == 'START':
                    self.stream_enable.set()
                    self.start_stream_capture()
                else:
                    self.stream_enable.clear()
                    if self.peer.readyState == PeerState.CONNECTED:
                        await self.peer.send({'type': 'warning', 'messagge': 'Stream manager deactivated'})
                        await self.peer.disconnect()
                    await self.stop_stream_capture()
            except Exception as e:
                await asyncio.sleep(0.5)
    
    def start_stream_capture(self):
        if SOURCE_TYPE == 'remote_client':
            self.stream_capture = None
            return
        if SOURCE_TYPE == 'local_file':
            stream_capture = VideoCapture(SOURCE_PATH, frame_consumer=self.create_deep_message, is_file=True)
        elif SOURCE_TYPE == 'ip_stream':
            stream_capture = VideoCapture(SOURCE_URL, frame_consumer=self.create_deep_message, is_file=False)
        elif SOURCE_TYPE == 'stream_capture':
            stream_capture = StreamCapture(peer_id=self.id, frame_consumer=self.create_deep_message, data_handler=self.on_capture_data)
        
        self.stream_capture = asyncio.create_task(stream_capture.start(self.source_ready))

    async def stop_stream_capture(self):
        self.stream_capture.cancel()
        try:
            await self.stream_capture
        except asyncio.CancelledError:
            pass

    async def stop(self):
        self.sender_socket.close()
        for collector in self.collectors:
            collector['socket'].close()
        if self.capture_peer:
            await self.capture_peer.close()
        await self.peer.close()

    async def start(self):
        logging.info(f'[{self.id}]: Open connection with peer server...')
        await self.peer.open()
        logging.info(f'[{self.id}]: Open video source...')
        tasks = []     
        tasks.append(asyncio.create_task(self.core_watchdog_timer()))

        for coll in self.collectors:
            logging.info(f'[{self.id}]: creating receiver for collector: {str(coll)}')
            receiver_task = asyncio.create_task(self.receiver(coll['socket']))
            tasks.append(receiver_task)


        tasks.append(asyncio.create_task(self.receive_server_signaling(self.server_pair_socket)))

        tasks.append(asyncio.create_task(self.task_monitor(tasks)))

        self.peer.add_data_handler(self.on_remote_data)
        try:
            while True:
                await self.stream_enable.wait()
                
                
                logging.info(f'[{self.id}]: Waiting peer connections...')
                self.remotePeerId = await self.peer.listen_connections()

                logging.info(f'[{self.id}]: Connection request from peer: {self.remotePeerId}')
                await self.peer.accept_connection()
                if SOURCE_TYPE == 'remote_client':
                    self.source_ready.set()

                await self.peer.disconnection_event.wait()
                if SOURCE_TYPE == 'remote_client':
                    self.source_ready.clear()

                while self.peer.readyState != PeerState.ONLINE:
                    await asyncio.sleep(1)
                
                self.__connection_reset()


                
        except Exception as err:
            logging.info(f'[{self.id}]: Execution error: {err}')
            #raise err
        finally:
            for task in tasks:
                task.cancel()
            await self.peer.close()


stream_manager = StreamManager()

# run event loop
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(stream_manager.start())
    #asyncio.run(asyncio.gather(demo1.start(), demo2.start()))
except KeyboardInterrupt:
    logging.info(' -> End signal')
finally:
    # cleanup
    logging.info(' -> Cleaning...')
    tasks = asyncio.all_tasks()
    for t in [t for t in tasks if not (t.done() or t.cancelled())]:
        # give canceled tasks the last chance to run
        loop.run_until_complete(t)
    loop.run_until_complete(stream_manager.stop())
