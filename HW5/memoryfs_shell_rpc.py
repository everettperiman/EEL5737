import pickle, logging
import argparse

from memoryfs_client import *
import os.path

## This class implements an interactive shell to navigate the file system

class FSShell():
  def __init__(self, file):
    # cwd stored the inode of the current working directory
    # we start in the root directory
    self.cwd = 0
    self.FileObject = file

  # implements repair
  def repair(self, server_ID):
    try:
      server_ID = int(server_ID)
    except ValueError:
      print('Error: ' + server_ID + ' not a valid Integer')
      return -1
    logging.info('Initiating repair on server ' + str(server_ID) + '...')
    self.FileObject.RawBlocks.Repair(int(server_ID))
    logging.info('Repair complete!')

  # implements cd (change directory)
  def cd(self, dir):
    # i = self.FileObject.Lookup(dir,self.cwd)
    i = self.FileObject.GeneralPathToInodeNumber(dir,self.cwd)
    if i == -1:
      print ("Error: not found\n")
      return -1
    inobj = InodeNumber(self.FileObject.RawBlocks,i)
    inobj.InodeNumberToInode()
    if inobj.inode.type != INODE_TYPE_DIR:
      print ("Error: not a directory\n")
      return -1
    self.cwd = i

  # implements mkdir
  def mkdir(self, dir):
    i = self.FileObject.Create(self.cwd, dir, INODE_TYPE_DIR)
    if i == -1:
      print ("Error: cannot create directory\n")
      return -1
    return 0

  # implements create
  def create(self, file):
    i = self.FileObject.Create(self.cwd, file, INODE_TYPE_FILE)
    if i == -1:
      print ("Error: cannot create file\n")
      return -1
    return 0

  # implements append
  def append(self, filename, string):
    logging.info("APPEND")
    i = self.FileObject.Lookup(filename, self.cwd)
    if i == -1:
      print ("Error: not found\n")
      return -1
    inobj = InodeNumber(self.FileObject.RawBlocks,i)
    inobj.InodeNumberToInode()
    if inobj.inode.type != INODE_TYPE_FILE:
      print ("Error: not a file\n")
      return -1
    written = self.FileObject.Write(i, inobj.inode.size, bytearray(string,"utf-8"))
    print ("Successfully appended " + str(written) + " bytes.")
    logging.debug("APPEND")
    return 0
    
  # implements link
  def link(self, target, name):
    i = self.FileObject.Link(target, name, self.cwd)
    if i == -1:
      print ("Error: cannot create link\n")
      return -1
    return 0

  # implements chroot
  def chroot(self, target):
    i = self.FileObject.Chroot(target, self.cwd)
    if i == -1:
      print ("Error: cannot chroot\n")
      return -1
    return 0


  # implements ls (lists files in directory)
  def ls(self):
    inobj = InodeNumber(self.FileObject.RawBlocks, self.cwd)
    inobj.InodeNumberToInode()
    block_index = 0
    while block_index <= (inobj.inode.size // BLOCK_SIZE):
      if block_index < len(inobj.inode.block_numbers):
        block = self.FileObject.RawBlocks.Get(inobj.inode.block_numbers[block_index])
      if block_index == (inobj.inode.size // BLOCK_SIZE):
        end_position = inobj.inode.size % BLOCK_SIZE
      else:
        end_position = BLOCK_SIZE
      current_position = 0
      while current_position < end_position:
        entryname = block[current_position:current_position+MAX_FILENAME]
        entryinode = block[current_position+MAX_FILENAME:current_position+FILE_NAME_DIRENTRY_SIZE]
        entryinodenumber = int.from_bytes(entryinode, byteorder='big')
        inobj2 = InodeNumber(self.FileObject.RawBlocks, entryinodenumber)
        inobj2.InodeNumberToInode()
        if inobj2.inode.type == INODE_TYPE_DIR:
          print (entryname.decode() + "/")
        else:
          print (entryname.decode())
        current_position += FILE_NAME_DIRENTRY_SIZE
      block_index += 1
    return 0

  # implements cat (print file contents)
  def cat(self, filename):
    i = self.FileObject.Lookup(filename, self.cwd)
    if i == -1:
      print ("Error: not found\n")
      return -1
    inobj = InodeNumber(self.FileObject.RawBlocks,i)
    inobj.InodeNumberToInode()
    if inobj.inode.type != INODE_TYPE_FILE:
      print ("Error: not a file\n")
      return -1
    data = self.FileObject.Read(i, 0, MAX_FILE_SIZE)
    print (data.decode())
    return 0

  # implements showblock (log block n contents) -> extended to show block for specific server
  def showblock(self, n, parity=False):
    
    # try:
    #   s = int(s)
    # except ValueError:
    #   print('Error: ' + s + ' not a valid Integer')
    #   return -1
    try:
      n = int(n)
    except ValueError:
      print('Error: ' + n + ' not a valid Integer')
      return -1
    
    # if s < 0 or s >= self.FileObject.RawBlocks.numServers:
    #   print('Error: server number ' + str(s) + ' not in valid range [0, ' + str(self.FileObject.RawBlocks.numServers) + ']')
    #   return -1

    if n < 0 or n >= TOTAL_NUM_BLOCKS:
      print('Error: block number ' + str(n) + ' not in valid range [0, ' + str(TOTAL_NUM_BLOCKS - 1) + ']')
      return -1

    dataServer, dataBlock = self.FileObject.RawBlocks.VirtualToPhysicalData(n)
    parityServer, parityBlock = self.FileObject.RawBlocks.VirtualToPhysicalParity(n)
    
    # output parity block for speicified block number (n) if parity = True
    logging.info('Block Parity [' + str(n) + '] : ' + str((self.FileObject.RawBlocks.ServerGet(parityServer, parityBlock).hex())))
    #logging.info('Block (string) [' + str(n) + '] : ' + str((self.FileObject.RawBlocks.Get(n).decode(encoding='UTF-8',errors='ignore'))))
    logging.info('Block (hex) [' + str(n) + ']  : ' + str((self.FileObject.RawBlocks.ServerGet(dataServer, dataBlock).hex())))
  
    return 0

  # implements showinode (log inode i contents)
  def showinode(self, i):

    try:
      i = int(i)
    except ValueError:
      print('Error: ' + i + ' not a valid Integer')
      return -1

    if i < 0 or i >= MAX_NUM_INODES:
      print('Error: inode number ' + str(i) + ' not in valid range [0, ' + str(MAX_NUM_INODES - 1) + ']')
      return -1

    inobj = InodeNumber(self.FileObject.RawBlocks, i)
    inobj.InodeNumberToInode()
    inode = inobj.inode
    inode.Print()
    return 0

  # implements showfsconfig (log fs config contents)
  def showfsconfig(self):
    self.FileObject.RawBlocks.PrintFSInfo()
    return 0

  # implements load (load the specified dump file)
  def load(self, dumpfilename):
    if not os.path.isfile(dumpfilename):
      print("Error: Please provide valid file")
      return -1
    self.FileObject.RawBlocks.LoadFromDisk(dumpfilename)
    self.cwd = 0
    return 0

  # implements save (save the file system contents to specified dump file)
  def save(self, dumpfilename):
    self.FileObject.RawBlocks.DumpToDisk(dumpfilename)
    return 0

  def Interpreter(self):
    while (True):
      command = input("[cwd=" + str(self.cwd) + "]:")
      splitcmd = command.split()
      if len(splitcmd) == 0:
        continue
      elif splitcmd[0] == "repair":
        if len(splitcmd) != 2:
          print("Error: repair requires one argument")
        else:
          self.repair(splitcmd[1]) 
      elif splitcmd[0] == "cd":
        if len(splitcmd) != 2:
          print ("Error: cd requires one argument")
        else:
          #self.FileObject.RawBlocks.Acquire()
          self.cd(splitcmd[1])
          #self.FileObject.RawBlocks.Release()
      elif splitcmd[0] == "cat":
        if len(splitcmd) != 2:
          print ("Error: cat requires one argument")
        else:
          #self.FileObject.RawBlocks.Acquire()         
          self.cat(splitcmd[1])
          #self.FileObject.RawBlocks.Release()
      elif splitcmd[0] == "mkdir":
        if len(splitcmd) != 2:
          print ("Error: mkdir requires one argument")
        else:
          #self.FileObject.RawBlocks.Acquire()
          self.mkdir(splitcmd[1])
          #self.FileObject.RawBlocks.Release()
      elif splitcmd[0] == "create":
        if len(splitcmd) != 2:
          print ("Error: create requires one argument")
        else:
          #self.FileObject.RawBlocks.Acquire()
          self.create(splitcmd[1])
          #self.FileObject.RawBlocks.Release()
      elif splitcmd[0] == "ln":
        if len(splitcmd) != 3:
          print ("Error: ln requires two arguments")
        else:
          #self.FileObject.RawBlocks.Acquire()
          self.link(splitcmd[1], splitcmd[2])
          #self.FileObject.RawBlocks.Release()
      elif splitcmd[0] == "chroot":
        if len(splitcmd) != 2:
          print ("Error: chroot requires one argument")
        else:
          #self.FileObject.RawBlocks.Acquire()
          self.chroot(splitcmd[1])
          #self.FileObject.RawBlocks.Release()
      elif splitcmd[0] == "append":
        if len(splitcmd) != 3:
          print ("Error: append requires two arguments")
        else:
          #self.FileObject.RawBlocks.Acquire()
          self.append(splitcmd[1], splitcmd[2])
          #self.FileObject.RawBlocks.Release()
      elif splitcmd[0] == "ls":
        #self.FileObject.RawBlocks.Acquire()        
        self.ls()
        #self.FileObject.RawBlocks.Release()
      elif splitcmd[0] == "showblock":
        if len(splitcmd) < 2:
          print ("Error: showblock requires at least two arguments: server#, block#")
        elif len(splitcmd) == 4:
          self.showblock(splitcmd[1], splitcmd[2], splitcmd[3])
        else:
          self.showblock(splitcmd[1])
      elif splitcmd[0] == "showinode":
        if len(splitcmd) != 2:
          print ("Error: showinode requires one argument")
        else:
          self.showinode(splitcmd[1])
      elif splitcmd[0] == "showfsconfig":
        if len(splitcmd) != 1:
          print ("Error: showfsconfig do not require argument")
        else:
          self.showfsconfig()
      elif splitcmd[0] == "load":
        if len(splitcmd) != 2:
          print ("Error: load requires 1 argument")
        else:
          self.load(splitcmd[1])
      elif splitcmd[0] == "save":
        if len(splitcmd) != 2:
          print ("Error: save requires 1 argument")
        else:
          self.save(splitcmd[1])
      elif splitcmd[0] == "exit":
        return
      else:
        print ("command " + splitcmd[0] + " not valid.\n")



if __name__ == "__main__":
    # Initialize file for logging
    # Change logging level to INFO to remove debugging messages
    logging.basicConfig(filename='memoryfs.log', filemode='w', level=logging.DEBUG)

    # Construct the argument parser
    ap = argparse.ArgumentParser()

    ap.add_argument('-ns', '-ns', type=int, help='an integer value')
    ap.add_argument('-port0', '--port0', type=int, help='an integer value')
    ap.add_argument('-port1', '--port1', type=int, help='an integer value')
    ap.add_argument('-port2', '--port2', type=int, help='an integer value')
    ap.add_argument('-port3', '--port3', type=int, help='an integer value')
    ap.add_argument('-port4', '--port4', type=int, help='an integer value')
    ap.add_argument('-port5', '--port5', type=int, help='an integer value')
    ap.add_argument('-port6', '--port6', type=int, help='an integer value')
    ap.add_argument('-port7', '--port7', type=int, help='an integer value')
    
    ap.add_argument('-nb', '--total_num_blocks', type=int, help='an integer value')
    ap.add_argument('-bs', '--block_size', type=int, help='an integer value')
    ap.add_argument('-ni', '--max_num_inodes', type=int, help='an integer value')
    ap.add_argument('-is', '--inode_size', type=int, help='an integer value')
    ap.add_argument('-cid', '--cid', type=int, help='an integer value')

    # Other than FS args, consecutive args will be captured in by 'arg' as list
    ap.add_argument('arg', nargs='*')

    args = ap.parse_args()

    # Initialize empty file system data
    logging.info('Initializing data structures...')
    RawBlocks = DiskBlocks(args)
    boot_block = b'\x00\x12\x34\x56'  # constant 00123456 stored as beginning of boot block; no need to change this
    # RawBlocks.InitializeBlocks(boot_block)

    # Print file system information and contents of first few blocks to memoryfs.log
    RawBlocks.PrintFSInfo()
    RawBlocks.PrintBlocks("Initialized", 0, 16)

    # Initialize FileObject inode
    FileObject = FileName(RawBlocks)

    # reload the global variables (in case they changed due to command line inputs)
    from memoryfs_client import *

    # Initialize root inode
    FileObject.InitRootInode()

    # Redirect INFO logs to console as well
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(console_handler)

    # Run the interactive shell interpreter
    myshell = FSShell(FileObject)
    myshell.Interpreter()
