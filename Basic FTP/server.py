from socket import *
from struct import pack, unpack
import hashlib

BUFFER_SIZE = 1024


class FileTransferServer():
    """ 
    Initialize your server's listening socket and store it in self here. You'll need to reference in 
    the start() function later.
    """
    def __init__(self, serverport=3601):
        self.serverport = serverport
        self.listen_sock = socket(AF_INET, SOCK_STREAM)
        self.listen_sock.bind(('',self.serverport))
        self.listen_sock.listen(1)
        print('The server is listening...')
        


    """ start function

    This function should loop forever. Each iteration of the loop should
    1) accept a new connection request
    2) attempt to receive a file from the newly connected client
    3) check to make sure a file was received
        3a) if received successfully, save the file to the transfered folder as a binary file (code provided),
            compute the MD5 hash of the file (code provided), and then send this back to the client. Do not 
            include the metadata in the MD5 computation, just the contents of the received binary file. You 
            should then close the client connection.
        3b) if not recieved successfully, print an error to the console and exit the loop
        
    The client will send messages using the following protocol:
    1) filename_length (unsigned byte)
    2) filename (variable-length string, max length is 255)
    3) created (unsigned int, UNIX time)
    4) modified (unsigned int, UNIX time)
    5) read_only (bool)
    6) owner_length (unsigned byte)
    7) owner (variable-length string, max length is 255)
    8) file_size (int)
    9) file (variable length byte array)

    You should unpack the contents of this message and decode the contents of string variables. Store the 
    following variables in a dictionary named 'metadata'. Use the protocol field name as the associated key in 
    the dictionary: filename, created, modified, read_only, owner

    Return: nothing
    """
    
    def start(self):
        while True:
            # Accept a new connection request
            client_socket, address = self.listen_sock.accept()
            print(f"Connection established with {address}")

            try:
                # Attempt to receive a file from the newly connected client
                data = client_socket.recv(BUFFER_SIZE)
                if data:
                    filename_length = unpack('B', data[:1])[0]
                    end_index = 1 + filename_length
                    filename = data[1:end_index].decode()

                    created, = unpack('!I', data[end_index:end_index + 4])
                    end_index += 4

                    modified, = unpack('!I', data[end_index:end_index + 4])
                    end_index += 4

                    read_only = unpack('!?', data[end_index:end_index + 1])[0]
                    end_index += 1

                    owner_length = unpack('!B', data[end_index:end_index + 1])[0]
                    end_index += 1

                    owner = data[end_index:end_index + owner_length].decode()
                    end_index += owner_length

                    file_size, = unpack('!i', data[end_index:end_index + 4])
                    end_index += 4

                    file = data[end_index:]

                    
                    while len(file) < file_size:
                        data = client_socket.recv(BUFFER_SIZE)
                        if data:
                            file += data
                        else:
                            break

                    # Store the metadata in a dictionary
                    metadata = {
                        'filename': filename,
                        'created': created,
                        'modified': modified,
                        'read_only': read_only,
                        'owner': owner
                    }

                    # Save the file as a binary file and compute its MD5 hash
                    with open(f"transfered/{metadata['filename']}", "wb") as f:
                        f.write(file)
                    md5_hash = hashlib.md5(file).hexdigest().encode()

                    # Send the MD5 hash back to the client
                    client_socket.send(md5_hash)

                else:
                    print('No file received')

            except Exception as e:
                print(f"An error occurred: {e}")

            finally:
                # Close the client connection
                client_socket.close()


if __name__ == "__main__":
    server = FileTransferServer()
    server.start()