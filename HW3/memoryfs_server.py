import pickle, logging
import argparse
import time # Added to support cacheinvalidation

# For locks: RSM_UNLOCKED=0 , RSM_LOCKED=1 
RSM_UNLOCKED = bytearray(b'\x00') * 1
RSM_LOCKED = bytearray(b'\x01') * 1

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
  rpc_paths = ('/RPC2',)

class DiskBlocks():
  def __init__(self, total_num_blocks, block_size):
    # This class stores the raw block array
    self.block = []                                            
    # Initialize raw blocks 
    for i in range (0, total_num_blocks):
      putdata = bytearray(block_size)
      self.block.insert(i,putdata)



if __name__ == "__main__":
  
  CacheInvalidationTime = time.time() # Added to support cache invalidation

  # Construct the argument parser
  ap = argparse.ArgumentParser()

  ap.add_argument('-nb', '--total_num_blocks', type=int, help='an integer value')
  ap.add_argument('-bs', '--block_size', type=int, help='an integer value')
  ap.add_argument('-port', '--port', type=int, help='an integer value')

  args = ap.parse_args()

  if args.total_num_blocks:
    TOTAL_NUM_BLOCKS = args.total_num_blocks
  else:
    print('Must specify total number of blocks') 
    quit()

  if args.block_size:
    BLOCK_SIZE = args.block_size
  else:
    print('Must specify block size')
    quit()

  if args.port:
    PORT = args.port
  else:
    print('Must specify port number')
    quit()

  # initialize blocks
  RawBlocks = DiskBlocks(TOTAL_NUM_BLOCKS, BLOCK_SIZE)

  # Create server
  server = SimpleXMLRPCServer(("127.0.0.1", PORT), requestHandler=RequestHandler) 

  def Get(block_number):
    result = RawBlocks.block[block_number]
    return result

  server.register_function(Get)

  def Put(block_number, data):
    RawBlocks.block[block_number] = data
    return 0

  server.register_function(Put)

  def RSM(block_number):
    result = RawBlocks.block[block_number]
    # RawBlocks.block[block_number] = RSM_LOCKED
    RawBlocks.block[block_number] = bytearray(RSM_UNLOCKED.ljust(BLOCK_SIZE,b'\x00'))
    return result

  server.register_function(RSM)

  def Release(self):
    logging.debug ('Release')
    # Put()s a zero-filled block to release lock
    time.sleep(10)
    print("Release")
    self.Put(RSM_BLOCK,bytearray(RSM_UNLOCKED.ljust(BLOCK_SIZE,b'\x00')),False)
    return 0

  def InvalidateClientCaches():
    server.invalidatetime = time.time()
    return server.invalidatetime

  server.register_function(InvalidateClientCaches)

  def GetInvalidateTime():
    return server.invalidatetime

  server.register_function(GetInvalidateTime)

  # Run the server's main loop
  print("Running block server with nb=" + str(TOTAL_NUM_BLOCKS) + ", bs=" + str(BLOCK_SIZE) + " on port " + str(PORT))
  server.invalidatetime = time.time()
  server.serve_forever()

