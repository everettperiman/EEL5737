import pickle, logging
import argparse
import hashlib

# Corrupt block number variable
CORRUPT_BLOCK_NUMBER = -1

# Checksum error constant for handling corrupt blocks
CHECKSUM_ERROR = -1

# For locks: RSM_UNLOCKED=0 , RSM_LOCKED=1 
RSM_UNLOCKED = bytearray(b'\x00') * 1
RSM_LOCKED = bytearray(b'\x01') * 1

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

# CalcChecksum: calculates and stores a checksum for a provided block
def CalcCheckSum(data):
  return hashlib.md5(data).hexdigest()
    

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
  rpc_paths = ('/RPC2',)
  
# BLOCK LAYER
class DiskBlocks():
  def __init__(self, total_num_blocks, block_size):
    self.block = []   
    self.checksums = {} # Dict to store checksums for each block                                         
    # Initialize raw blocks 
    for i in range (0, total_num_blocks):
      putdata = bytearray(block_size)
      self.block.insert(i,putdata)
      self.checksums[i] = 0

if __name__ == "__main__": 

  # Construct the argument parser
  ap = argparse.ArgumentParser()

  ap.add_argument('-nb', '--total_num_blocks', type=int, help='an integer value')
  ap.add_argument('-bs', '--block_size', type=int, help='an integer value')
  ap.add_argument('-port', '--port', type=int, help='an integer value')
  ap.add_argument('-sid', '--sid', type=int, help='an integer value')
  ap.add_argument('-cblk', '--cblk', type=int, help='an integer value')
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
    
  if args.sid >= 0:
    SERVER_ID = args.sid
  else:
    print('Must specify valid server id')
    quit()

  # Initialize blocks
  RawBlocks = DiskBlocks(TOTAL_NUM_BLOCKS, BLOCK_SIZE)

  # Corrupt a block if input parameter exists  
  if args.cblk is not None or args.cblk == 0:
    CORRUPT_BLOCK_NUMBER = args.cblk
    print('CORRUPT BLOCK NUMBER: ' + str(CORRUPT_BLOCK_NUMBER))

  # Create server
  server = SimpleXMLRPCServer(("127.0.0.1", PORT), requestHandler=RequestHandler) 

  def Get(block_number):
    # Read block specified by block_number
    result = RawBlocks.block[block_number]
    test = RawBlocks.checksums.get(block_number)
    # Corrupt data if block_number = cblk
    if(block_number == CORRUPT_BLOCK_NUMBER):
      RawBlocks.block[block_number] = bytearray(b'\xFF') * BLOCK_SIZE
      test = CalcCheckSum(RawBlocks.block[block_number])

    # Validate checksum
    if test != RawBlocks.checksums.get(block_number):
      return CHECKSUM_ERROR

    return result

  server.register_function(Get)

  def Put(block_number, data):
    # Store data
    RawBlocks.block[block_number] = bytearray(data.data)
    # Compute and store a checksum for the data
    RawBlocks.checksums[block_number] = CalcCheckSum(RawBlocks.block[block_number])
    print('The checksum for block# ' + str(block_number) + ' is ' + str(RawBlocks.checksums[block_number]))
    return 0

  server.register_function(Put)

  # Run the server's main loop
  print ("Running block server with nb=" + str(TOTAL_NUM_BLOCKS) + ", bs=" + str(BLOCK_SIZE) + " on port " + str(PORT))
  server.serve_forever()

