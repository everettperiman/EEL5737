import pickle, logging
import argparse

from memoryfs import *
import os.path

## This class implements an interactive shell to navigate the file system

class FSShell():
  def __init__(self, file):
    # cwd stored the inode of the current working directory
    # we start in the root directory
    self.FileObject = file
    self.rootdir = self.FileObject.rootdir
    self.cwd = self.rootdir

#########################
### Start of new code ###

  def mkdir(self, dirname):
    # create a new dir in cwd
    response = self.FileObject.Create(self.cwd, dirname, INODE_TYPE_DIR)
    if(response == -1):
      print("mkdir: Cannot create directory")
    return response
     

  def create(self, filename):
    # create a new file in the cwd
    # filename is a name in the cwd
    response = self.FileObject.Create(self.cwd, filename, INODE_TYPE_FILE)
    if(response == -1):
      print("create: Cannot create file")
    return response

  def append(self, filepath, string):
    # filepath is a general path
    # appends a string to a file
    # Step 1 resolve general file path
    # Step 2 check and write the new file
    # Check if the inode exists
    file_inode = self.FileObject.GeneralPathToInodeNumber(filepath, self.cwd)

    if file_inode == -1:
      print("Error: not found" )
      return -1

    file_inode_obj = InodeNumber(self.FileObject.RawBlocks, file_inode)
    file_inode_obj.InodeNumberToInode()

    # Check if the inode is a file
    if file_inode_obj.inode.type != INODE_TYPE_FILE:
      print("Error: not a file")
      return -1

    # Read the file contents and print them to the term
    file_contents_block = self.FileObject.Read(file_inode,0,MAX_FILE_SIZE)

    file_contents = file_contents_block.decode(encoding='UTF-8').replace("\x00","")
    file_contents = file_contents + string
    write_file_contents = bytearray(file_contents.encode(encoding='UTF-8'))    
    write_code = self.FileObject.Write(file_inode_number = file_inode, 
                                      offset = 0, 
                                      data = write_file_contents)
    

  def ln(self, targetpath, linkname):
    # create a link to target path with name linkname in the cwd
    # linkname is a name in the cwd
    # targetpath is a general path
    response = self.FileObject.Link(targetpath,linkname,self.cwd)
    if(response == -1):
      print("create: Cannot link file")
    return response
    

  def chroot(self, chrootpath):
    response = self.FileObject.Chroot(chrootpath, self.cwd)
    
    if(response == -1):
      print("chroot: Cannot change root")
      return response

    self.rootdir = self.FileObject.rootdir
    return 0

### End of new code ###
#########################

  # implements cd (change directory)
  def cd(self, dir):
    i = self.FileObject.GeneralPathToInodeNumber(dir, self.cwd) # Added GeneralPathToInodeNumber
    if i == -1:
      print ("Error: not found\n")
      return -1
    inobj = InodeNumber(self.FileObject.RawBlocks,i)
    inobj.InodeNumberToInode()
    if inobj.inode.type != INODE_TYPE_DIR:
      print ("Error: not a directory\n")
      return -1
    self.cwd = i

  # implements ls (lists files in directory)
  def ls(self):
    inobj = InodeNumber(self.FileObject.RawBlocks, self.cwd)
    inobj.InodeNumberToInode()
    block_index = 0
    while block_index <= (inobj.inode.size // BLOCK_SIZE):
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
          print("[" + str(inobj2.inode.refcnt) + "]:" + entryname.decode() + "/")
        else:
          print("[" + str(inobj2.inode.refcnt) + "]:" + entryname.decode())
        current_position += FILE_NAME_DIRENTRY_SIZE
      block_index += 1
    return 0

  # implements cat (print file contents)
  def cat(self, filename):
    i = self.FileObject.GeneralPathToInodeNumber(filename, self.cwd) # Added GeneralPathToInodeNumber
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

  # implements showblock (log block n contents)
  def showblock(self, n):

    try:
      n = int(n)
    except ValueError:
      print('Error: ' + n + ' not a valid Integer')
      return -1

    if n < 0 or n >= TOTAL_NUM_BLOCKS:
      print('Error: block number ' + str(n) + ' not in valid range [0, ' + str(TOTAL_NUM_BLOCKS - 1) + ']')
      return -1
    logging.info('Block (string) [' + str(n) + '] : ' + str((self.FileObject.RawBlocks.Get(n).decode(encoding='UTF-8',errors='ignore'))))
    logging.info('Block (hex) [' + str(n) + '] : ' + str((self.FileObject.RawBlocks.Get(n).hex())))
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
      elif splitcmd[0] == "cd":
        if len(splitcmd) != 2:
          print ("Error: cd requires one argument")
        else:
          self.cd(splitcmd[1])
      elif splitcmd[0] == "cat":
        if len(splitcmd) != 2:
          print ("Error: cat requires one argument")
        else:
          self.cat(splitcmd[1])
      elif splitcmd[0] == "ls":
        self.ls()
      elif splitcmd[0] == "showblock":
        if len(splitcmd) != 2:
          print ("Error: showblock requires one argument")
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

      #Assignment 2 Callouts
      elif splitcmd[0] == "mkdir":
        if len(splitcmd) != 2:
          print ("Error: mkdir requires 1 argument")
        else:
          self.mkdir(splitcmd[1])
      elif splitcmd[0] == "create":
        if len(splitcmd) != 2:
          print ("Error: create requires 1 argument")
        else:
          self.create(splitcmd[1])
      elif splitcmd[0] == "chroot":
        if len(splitcmd) != 2:
          print ("Error: chroot requires 1 argument")
        else:
          self.chroot(splitcmd[1])
      elif splitcmd[0] == "append":
        if len(splitcmd) != 3:
          print ("Error: append requires 2 arguments")
        else:
          self.append(splitcmd[1],splitcmd[2])
      elif splitcmd[0] == "ln":
        if len(splitcmd) != 3:
          print ("Error: ln requires 2 arguments")
        else:
          self.ln(splitcmd[1],splitcmd[2])



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

  ap.add_argument('-nb', '--total_num_blocks', type=int, help='an integer value')
  ap.add_argument('-bs', '--block_size', type=int, help='an integer value')
  ap.add_argument('-ni', '--max_num_inodes', type=int, help='an integer value')
  ap.add_argument('-is', '--inode_size', type=int, help='an integer value')

  # Other than FS args, consecutive args will be captured in by 'arg' as list
  ap.add_argument('arg', nargs='*')

  args = ap.parse_args()

  # Initialize empty file system data
  logging.info('Initializing data structures...')
  RawBlocks = DiskBlocks(args)
  boot_block = b'\x12\x34\x56\x78' # constant 12345678 stored as beginning of boot block; no need to change this
  RawBlocks.InitializeBlocks(boot_block)


  # Print file system information and contents of first few blocks to memoryfs.log
  RawBlocks.PrintFSInfo()
  RawBlocks.PrintBlocks("Initialized",0,16)

  # Initialize FileObject inode
  FileObject = FileName(RawBlocks)

  # reload the global variables (in case they changed due to command line inputs)
  from memoryfs import *

  # Initalize root inode
  FileObject.InitRootInode()

  # Redirect INFO logs to console as well
  console_handler = logging.StreamHandler()
  console_handler.setLevel(logging.INFO)
  logging.getLogger().addHandler(console_handler)

  # Run the interactive shell interpreter
  myshell = FSShell(FileObject)
  myshell.Interpreter()

