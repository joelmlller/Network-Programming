from socket import *
from struct import pack, unpack
import hashlib

class FileTransferClient():
    """
    Create your socket and store it in self here
    """    
    def __init__(self, servername="localhost", serverport=3601):
        self.servername = servername
        self.serverport = serverport
        self.server_sock = socket(AF_INET, SOCK_STREAM)

    """
    This function should connect to the server using the information passed into on init. It should then send 
    the provided file and associated metadata using the protocol shown below. Upon sending the message, 
    attempt to receive a reponse from the server containing the md5 hash of the file the server received. 
    Return the hash you receive at the end of this function.

    The client should send messages using the following protocol:
    1) filename_length (unsigned byte)
    2) filename (variable-length string, max length is 255)
    3) created (unsigned int, UNIX time)
    4) modified (unsigned int, UNIX time)
    5) read_only (bool)
    6) owner_length (unsigned byte)
    7) owner (variable-length string, max length is 255)
    8) file_size (int)
    9) file (variable length byte array)
    """
    def transfer_file(self, file, metadata):
        self.server_sock.connect((self.servername,self.serverport))

    

        fileLength = len(metadata["filename"])
        ownerLength = len(metadata["owner_name"])
        fileSize = len(file)

        packedMsg = pack(f'!B{fileLength}s', fileLength, metadata["filename"].encode())
        packedMsg += pack(f'!2I?B', metadata["created"], metadata["modified"], metadata["read_only"], ownerLength)
        packedMsg += pack(f'!{ownerLength}si', metadata["owner_name"].encode(), fileSize)
        packedMsg += pack(f'!{fileSize}s', file)

        self.server_sock.send(packedMsg)
        print("Data sent!")

        hash = self.server_sock.recv(32).decode()
        print("Hash received!")

        self.server_sock.close()
        print("Connection killed!")

        return hash





if __name__ == "__main__":
    client = FileTransferClient()
    metadata = {
        "filename": "testFile3.jpg",
        "created": 1684772033,
        "modified": 1684772053,
        "read_only": True,
        "owner_name": "ssssss"
    }
    file = open(metadata['filename'], 'rb').read()
    result = client.transfer_file(file, metadata)
    print(result)