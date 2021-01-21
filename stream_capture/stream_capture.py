import sys
# sys.path.append('/hyperpeer')
from hyperpeer import Peer, PeerState
import asyncio
import subprocess
import pathlib
import ssl
import logging
import os
import time
import urllib.request
from pathlib import Path

ROOT = os.path.dirname(__file__)
logging.basicConfig(level=logging.INFO)

logging.info('*** STREAM CAPTURE v0.7 ***')
#ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
#ssl_context.load_verify_locations('cert.pem')

ssl_context = ssl.create_default_context()
ssl_context.options |= ssl.OP_ALL
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE



class StreamCapture:
    def __init__(self, source, peer_id, peer_type, format=None, metadata=None, remotePeerId=None, remotePeerType=None):
        self.id = peer_id
        self.metadata = metadata
        self.remotePeerId = remotePeerId
        self.remotePeerType = remotePeerType
        if format:
            self.peer = Peer('wss://' + os.environ['HP_SERVER']+':'+ os.environ['SERVER_PORT'], id=peer_id,
                             peer_type=peer_type, media_source=source, ssl_context=ssl_context, media_source_format=format)
        else:
            self.peer = Peer('wss://' + os.environ['HP_SERVER']+':'+ os.environ['SERVER_PORT'], id=peer_id,
                             peer_type=peer_type, media_source=source, ssl_context=ssl_context)
        self.running = False

    async def on_data(self, data):
        # logging.info(f'[{self.id}]: Remote message: {str(data)}')
        if data['type'] == 'data':
            acknowledge = {
                'type': 'acknowledge',
                'rec_time': data['rec_time']
            }
            await self.peer.send(acknowledge)
    
    def add_data_handler(self, handler):
        self.peer.add_data_handler(handler)

    async def start(self):
        await self.peer.open()
        self.peer.add_data_handler(self.on_data)
        try:
            while True:
                if self.remotePeerId:
                    await self.peer.connect_to(self.remotePeerId)
                    logging.info(f'connected to %s', self.remotePeerId)
                elif self.remotePeerType:
                    # List connected peers
                    peers = await self.peer.get_peers()
                    for peer in peers:
                        if peer['type'] == self.remotePeerType and not peer['busy']:
                            await self.peer.connect_to(peer['id'])
                            logging.info(f'connected to {self.remotePeerType} with id: {self.remotePeerId}')
                            await self.peer.send({'type': 'source', 'peerId': self.id})
                            break
                else:
                    logging.info(f'[{self.id}]: Waiting peer connections...')
                    self.remotePeerId = await self.peer.listen_connections()
                    logging.info(f'[{self.id}]: Connection request from peer: {self.remotePeerId}')
                    await self.peer.accept_connection()
                await self.peer.send({'type': 'metadata', 'metadata': self.metadata})
                while self.peer.readyState != PeerState.ONLINE:
                    await asyncio.sleep(1)
                await asyncio.sleep(1)
                self.remotePeerId = None
        except Exception as err:
            logging.error(f'[{self.id}]: Execution error: {err}')
            #raise err
        finally:
            await self.peer.close()
    
    async def stop(self):
        await self.peer.close()

    def run(self):
        if self.running:
            return
        self.running = True
        # run event loop
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.start())
            #asyncio.run(asyncio.gather(demo1.start(), demo2.start()))
        except KeyboardInterrupt:
            logging.info(' -> End signal')
        finally:
            # cleanup
            logging.info(' -> Cleaning...')
            loop.run_until_complete(self.stop())

if __name__ == '__main__':
    source_id = os.environ["STREAM_CAPTURE_ID"].rstrip()
    logging.info('STREAM_CAPTURE_ID: ' + source_id)
    source_url = os.environ[f'SOURCE_{source_id}'].rstrip()
    logging.info('Source URL: ' + source_url)
    #source_format = os.environ.get("SOURCE_FORMAT", 'mpjpeg')
    source_metadata = os.environ.get("STREAM_METADATA", {'url': source_url})
    remote_peer_type = os.environ.get("REMOTE_PEER_TYPE", None)

    try:
        req = urllib.request.Request(source_url)
        urllib.request.urlopen(req)
    except (ValueError, urllib.error.URLError) as e:
        logging.info(f'source is not a standard url...')
        if not source_url.startswith('rtsp:'):
            logging.info(f'source is neither a rtsp url ...')
            if not Path(source_url).is_file():
                logging.error(f'source is neither a file ...')
                # raise Exception(f'Invalid source ({source_url}): {str(e)}')
        
        #sys.exit()

    if source_url.endswith('mjpg'):
        source_format = 'mpjpeg'
    elif source_url.startswith('/dev'):
        source_format = 'v4l2'
    else:
        source_format = None
    
    import json
    output_file_path = os.environ.get('OUTPUT_FILE', "messages.txt")

    with  open(output_file_path, 'w') as output_file:
        def print_to_file(data):
            if data['type'] == 'data':
                data_to_save = {
                    'vc_time': data['vc_time'],
                    'last_frame_shape': data['last_frame_shape'],
                    'data': data['data']
                }
                output_json = json.dumps(data_to_save)
                output_file.write(output_json + '\n')
        stream_capture = StreamCapture(source=source_url, peer_id=source_id, peer_type='stream_capture', format=source_format, metadata=source_metadata, remotePeerType=remote_peer_type)
        # stream_capture.add_data_handler(lambda data: logging.info(f'*** Remote message: {str(data)}'))
        stream_capture.add_data_handler(print_to_file)
        stream_capture.run()

