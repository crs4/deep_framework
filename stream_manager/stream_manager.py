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

from utils.socket_commons import send_data, recv_data

ROOT = os.path.dirname(__file__)
logging.basicConfig(level=logging.INFO)

logging.info('*** DEEP STREAM MANAGER v0.5 ***')
#ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
#ssl_context.load_verify_locations('cert.pem')

ssl_context = ssl.create_default_context()
ssl_context.options |= ssl.OP_ALL
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


class StreamServer():

    def __init__(self, peer_type):        
        self.id = 'temp_id'
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
                if self.stream_ready:
                    yield self.received_frame
                else:
                    yield self.deafult_frame

        def frame_consumer_to_client(frame):
            if self.stream_ready and not self.capture_peer:
                self.create_deep_message(frame)

        self.hp_server_address = HP_SERVER +':'+ SERVER_PORT
        print(self.hp_server_address)
        self.peer = Peer('wss://' + self.hp_server_address, peer_type=peer_type,
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
        self.source_changed = False
        self.stream_ready = False
        self.deep_delay = 0
        self.round_trip = 0
        self.processing_period = 0
        

    def __socket_setup(self):
        
        collector_list = SERVER_IN_PORTS.split(',')
        self.context = zmq.Context()
        self.sender_socket = self.context.socket(zmq.PUB)
        self.sender_socket.bind(PROT + '*:' + VC_OUT)

        self.collectors = []
        for coll in collector_list:

            name, coll_port = coll.split(':')
            receiver_socket = self.context.socket(zmq.PAIR)
            receiver_socket.bind(PROT +'*:'+ coll_port)
            self.collectors.append({'name':name,'socket':receiver_socket})

    def create_deep_message(self,frame):

        self.received_frame = frame
        self.received_frames += 1
        capture_time = time.time()

        res = {'frame_idx': self.received_frames , 'vc_time': capture_time, 'frame_shape': frame.shape}
        if self.deep_delay < float(MAX_ALLOWED_DELAY) and self.processing_period < float(MAX_ALLOWED_DELAY):  
            send_data(self.sender_socket,[frame],0,False,**res)
        else:
            logging.info(f'[{self.id}]: Skipping frame: {str(self.received_frames)}, deep delay: {str(self.deep_delay)}, processing period: {str(self.processing_period)}')




    async def receiver(self,socket):
        logging.info(f'[{self.id}]: Receiver started')
        self.processed_frames = 0
        last_receive_time = time.time()
        no_data_time = 0
        try:
            while True:

                if not self.stream_ready:
                    await asyncio.sleep(0.5)
                    self.processed_frames = 0
                    last_receive_time = time.time()
                    no_data_time = 0
                    continue

                try:
                    received_data, __ = recv_data(socket,1,False)
                    received_data["rec_time"] = time.time()
                    self.deep_delay = received_data["rec_time"] - received_data["vc_time"]
                    self.processing_period = received_data["rec_time"] - last_receive_time
                    no_data_time = 0
                    self.processed_frames += 1
                    last_receive_time = received_data["rec_time"]
                    asyncio.create_task(self.send(received_data))
                except Exception as e:
                    self.processing_period = time.time() - last_receive_time
                    no_data_time += self.processing_period
                    if no_data_time > float(MAX_ALLOWED_DELAY) * 1.2:
                        if no_data_time > 5 * float(MAX_ALLOWED_DELAY):
                            await self.peer.send({'type': 'error', 'messagge':  f'No data from DEEP since  {str(no_data_time)} seconds. Reason: {str(e)}' })
                            raise Exception(msg)

                        msg = f'High processing period: {str(no_data_time)}. Reason: {str(e)}' 
                        await self.peer.send({'type': 'warning', 'messagge': msg})
                        logging.warning(msg)

                        self.deep_delay = -1
                        self.processing_period = -1
                        last_receive_time = time.time()
                        await asyncio.sleep(float(MAX_ALLOWED_DELAY) * 0.5)

                await asyncio.sleep(0.05)

        except asyncio.CancelledError as c:
            await asyncio.sleep(float(MAX_ALLOWED_DELAY))
            try:
                while True:
                    received_data, __ = recv_data(socket,1,False)
            except:
                logging.info(f'[{self.id}]: collector socket empty')
            raise c

    async def send(self,data):
        if self.peer.readyState != PeerState.CONNECTED:
            return
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
        data_merged = {**data_to_send,**data}
        # logging.info(f'[{self.id}]: Sending data: {str(data_merged)}')
        await self.peer.send(data_merged)

    def on_remote_data(self, data):
        # logging.info(f'[{self.id}]: Remote message: {str(data)}')
        data_type = data['type']
        if data_type == 'acknowledge':
            try:
                self.round_trip = time.time() - data["rec_time"]
            except Exception as e:
                logging.error('error on data' + str(e))
        
        elif data_type == 'source':
            logging.info('Source info: ' + str(data))
            
            if self.source_peer_id == data['peerId']:
                return
                
            self.source_peer_id = data['peerId']
            self.source_changed = True

            if self.source_peer_id == 'none':
                self.source_peer_id = None

        elif data_type == 'metadata' and self.remotePeerId == self.source_peer_id:
            self.source_metadata = data['metadata']
            logging.info('Source metadata: ' + str(self.source_metadata))
    
    async def on_capture_data(self, data):
        if data['type'] == 'metadata' and self.remotePeerId != self.source_peer_id:
            self.source_metadata = data['metadata']
            logging.info('Source metadata: ' + str(self.source_metadata))
            await self.peer.send(data)

    
    async def stop(self):
        self.sender_socket.close()
        for collector in self.collectors:
            collector['socket'].close()
        if self.capture_peer:
            await self.capture_peer.close()
        await self.peer.close()

    async def start(self, remotePeerId=None):
        await self.peer.open()
        self.peer.add_data_handler(self.on_remote_data)
        try:
            while True:
                tasks = []               
                logging.info(f'[{self.id}]: Waiting peer connections...')
                self.remotePeerId = await self.peer.listen_connections()
                logging.info(f'[{self.id}]: Connection request from peer: {remotePeerId}')
                await self.peer.accept_connection()

                for coll in self.collectors:
                    receiver_task = asyncio.create_task(self.receiver(coll['socket']))
                    tasks.append(receiver_task)

                while self.peer.readyState == PeerState.CONNECTED:
                    if self.capture_peer:
                        if self.capture_peer.readyState == PeerState.DISCONNECTING:
                            self.stream_ready = False
                            await self.peer.send({'type':'source-disconnecting'})

                    if self.source_changed:
                        self.source_changed = False
                        self.stream_ready = False
                        if self.capture_peer:
                            await self.capture_peer.close()
                            self.capture_peer = None

                        if self.source_peer_id != self.remotePeerId and self.source_peer_id is not None: #check
                            try:
                                def consumer(frame):
                                    self.create_deep_message(frame)

                                self.capture_peer = Peer('wss://' + self.hp_server_address, peer_type='video_capture',
                                        frame_generator=None, frame_consumer=consumer, ssl_context=ssl_context)
                                
                                await self.capture_peer.open()
                                logging.info(f'[{self.id}]: capture peer instance created')
                                self.capture_peer.add_data_handler(self.on_capture_data)

                                await self.capture_peer.connect_to(self.source_peer_id)
                                logging.info(f'[{self.id}]: connected to {self.source_peer_id}')
                                self.stream_ready = True
                            except Exception as err:
                                await self.peer.send({'type':'source-error','error':str(err)})
                        elif self.source_peer_id == self.remotePeerId:
                            self.stream_ready = True
                    
                    await asyncio.sleep(0.1)

                self.stream_ready = False
                for task in tasks:
                    task.cancel()
                try:
                    for task in tasks:
                        await task
                except asyncio.CancelledError:
                    print(f'[{self.id}]: tasks are cancelled now')
                while self.peer.readyState != PeerState.ONLINE:
                    await asyncio.sleep(1)
                
                self.__connection_reset()
                if self.capture_peer:
                    await self.capture_peer.close()
                
        except Exception as err:
            logging.info(f'[{self.id}]: Execution error: {err}')
            #raise err
        finally:
            await self.peer.close()





stream_manager = StreamServer(peer_type='stream_manager')

#demo2 = Player(source='video_test.mov', peer_type='video-server',
#               id='server1', format='mp4')


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
    loop.run_until_complete(stream_manager.stop())
