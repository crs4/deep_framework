import zmq
import numpy,json
#from cereal import log
#from common import realtime

def new_message():
  dat = log.Event.new_message()
  dat.logMonoTime = int(realtime.sec_since_boot() * 1e9)
  return dat

def pub_sock(context, port, addr="*"):
  sock = context.socket(zmq.PUB)
  sock.bind("tcp://%s:%d" % (addr, port))
  return sock

def sub_sock(context, port, poller=None, addr="127.0.0.1", conflate=False):
  sock = context.socket(zmq.SUB)
  if conflate:
    sock.setsockopt(zmq.CONFLATE, 1)
  sock.connect("tcp://%s:%d" % (addr, port))
  sock.setsockopt(zmq.SUBSCRIBE, "")
  if poller is not None:
    poller.register(sock, zmq.POLLIN)
  return sock

def drain_sock(sock, wait_for_one=False):
  ret = []
  while 1:
    try:
      if wait_for_one and len(ret) == 0:
        dat = sock.recv()
      else:
        dat = sock.recv(zmq.NOBLOCK)
      dat = log.Event.from_bytes(dat)
      ret.append(dat)
    except zmq.error.Again:
      break
  return ret


# TODO: print when we drop packets?
def recv_sock(sock, wait=False):
  dat = None
  while 1:
    try:
      if wait and dat is None:
        dat = sock.recv()
      else:
        dat = sock.recv(zmq.NOBLOCK)
    except zmq.error.Again:
      break
  if dat is not None:
    dat = log.Event.from_bytes(dat)
  return dat

def recv_one(sock):
  return log.Event.from_bytes(sock.recv())

def recv_one_or_none(sock):
  try:
    return log.Event.from_bytes(sock.recv(zmq.NOBLOCK))
  except zmq.error.Again:
    return None




def send_data(socket,imgs=None, flags=0, copy=False, track=False,  **kwargs):

    
    """send a numpy array with metadata"""
    md = dict()    
    

    for key, value in kwargs.items():
        md[key] = value


    
    

    if not imgs:
        return socket.send_json(md)
        


    payloads = []
    for im in imgs:
        payloads.append(dict( dtype = str(im.dtype),shape=im.shape))

    md['payloads'] = payloads
    #socket.send_json(json.dumps(md))
    socket.send_json(md, flags|zmq.SNDMORE)
    return socket.send_multipart(imgs, flags, copy=copy, track=track)








def recv_data(socket,flags=0, copy=True, track=False):

  

  """recv a numpy array"""
  imgs = []
  #topic = socket.recv_string()


  md = socket.recv_json(flags=flags)

  #md = json.loads(md_temp)

  if not 'payloads' in md.keys():
    return md,imgs

  msgs = socket.recv_multipart(flags=flags)
  #md = json.loads(temp)

  payloads = md['payloads']
  for i in range(len(payloads)):

    #msg = socket.recv(flags=flags, copy=copy, track=track)
    msg = msgs[i]
    try:
      buf = memoryview(msg)
    except:
      buf = buffer(msg)

    shape = list(payloads[i]['shape'])
    dtype = payloads[i]['dtype']
    img = numpy.frombuffer(buf, dtype=dtype)
    img = img.reshape(shape)
    imgs.append(img)
  
  return md,imgs
  








