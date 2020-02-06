import sys
sys.path.append('/hyperpeer')
from hyperpeer import Peer, PeerState
import asyncio
import subprocess
import pathlib
import ssl
import logging
import os
import time
import urllib.request


ROOT = os.path.dirname(__file__)
logging.basicConfig(level=logging.INFO)

logging.info('*** STREAM CAPTURE v0.1 ***')
#ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
#ssl_context.load_verify_locations('cert.pem')

ssl_context = ssl.create_default_context()
ssl_context.options |= ssl.OP_ALL
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE



class Player:
    def __init__(self, source, peer_type, format=None):
        self.id = 'temp_id'
        if format:
            self.peer = Peer('wss://' + os.environ['HP_SERVER']+':'+ os.environ['SERVER_PORT'],
                             peer_type=peer_type, media_source=source, ssl_context=ssl_context, media_source_format=format)
        else:
            self.peer = Peer('wss://' + os.environ['HP_SERVER']+':'+ os.environ['SERVER_PORT'],
                             peer_type=peer_type, media_source=source, ssl_context=ssl_context)

    async def start(self, remotePeerId=None):
        await self.peer.open()
        try:
            while True:
                if remotePeerId:
                    await self.peer.connect_to(remotePeerId)
                    #logging.info(f'connected to %s', remotePeerId)
                else:
                    logging.info(f'[{self.id}]: Waiting peer connections...')
                    remotePeerId = await self.peer.listen_connections()
                    logging.info(f'[{self.id}]: Connection request from peer: {remotePeerId}')
                    await self.peer.accept_connection()
                while self.peer.readyState != PeerState.ONLINE:
                    await asyncio.sleep(1)
                await asyncio.sleep(1)
                remotePeerId = None
        except Exception as err:
            logging.info(f'[{self.id}]: Execution error: {err}')
            #raise err
        finally:
            await self.peer.close()
    
    async def stop(self):
        await self.peer.close()


source_url = os.environ["SOURCE"]
source_format = os.environ.get("SOURCE_FORMAT", 'mpjpeg')


try:
    req = urllib.request.Request(source_url)
    urllib.request.urlopen(req)
except (ValueError, urllib.error.URLError) as e:
    print(f'Invalid source url ({source_url}, format: {source_format}): {str(e)}')
    sys.exit()


stream_capture = Player(source=source_url, peer_type='stream_capture', format=source_format)


# run event loop
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(stream_capture.start())
    #asyncio.run(asyncio.gather(demo1.start(), demo2.start()))
except KeyboardInterrupt:
    logging.info(' -> End signal')
finally:
    # cleanup
    logging.info(' -> Cleaning...')
    loop.run_until_complete(stream_capture.stop())
