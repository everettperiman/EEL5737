import pickle, logging
import argparse
import hashlib

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

def checksum_check(block_number, data):
  if block_number == CBLCK:
    print("Bad block")
    return 0
  else:
    if hashlib.md5(bytearray(data.data)).hexdigest() == server.checksums[block_number]:
      print("It matches!")


if __name__ == "__main__":

  # Construct the argument parser
  ap = argparse.ArgumentParser()

  ap.add_argument('-nb', '--total_num_blocks', type=int, help='an integer value')
  ap.add_argument('-bs', '--block_size', type=int, help='an integer value')
  ap.add_argument('-port', '--port', type=int, help='an integer value')
  ap.add_argument('-sid', '--sid', type=int, help='an integer value') # Added to support adding server ID value
  ap.add_argument('-cblck', '--cblck', type=int, help='an integer value', required=False) # Added to support adding a bad block


  args = ap.parse_args()
  print(args)

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

  if args.sid is not None:
    SID = args.sid
  else:
    print('Must specify server id number')
    quit()

  if args.cblck:
    CBLCK = args.cblck
  else:
    CBLCK = -1


  # initialize blocks
  RawBlocks = DiskBlocks(TOTAL_NUM_BLOCKS, BLOCK_SIZE)

  # Create server
  server = SimpleXMLRPCServer(("127.0.0.1", PORT), requestHandler=RequestHandler) 

  server.checksums = [0 for i in range(TOTAL_NUM_BLOCKS+1)]

  def Get(block_number):
    result = RawBlocks.block[block_number]
    checksum_check(block_number, result)
    return result

  server.register_function(Get)

  def Put(block_number, data):
    RawBlocks.block[block_number] = data
    server.checksums[block_number] = hashlib.md5(data.data).hexdigest()
    return 0

  server.register_function(Put)

  def RSM(block_number):
    result = RawBlocks.block[block_number]
    # RawBlocks.block[block_number] = RSM_LOCKED
    RawBlocks.block[block_number] = bytearray(RSM_LOCKED.ljust(BLOCK_SIZE,b'\x01'))
    return result

  server.register_function(RSM)

  def ServerID():
    result = args.sid
    return result

  server.register_function(ServerID)

  # Run the server's main loop
  print ("Running block server with nb=" + str(TOTAL_NUM_BLOCKS) + ", bs=" + str(BLOCK_SIZE) + " on port " + str(PORT))
  server.serve_forever()

