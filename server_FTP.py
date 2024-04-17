import os
import struct
import sys
import signal

from socket import *
from subprocess import check_output

## Socket Setup

TCP_PORT = 6969 #why not

BUFFER_SIZE = 1024 # I guess this is pretty standard
serverSocket = socket(AF_INET, SOCK_STREAM)

serverSocket.bind(('', TCP_PORT)) #I think we'll want this to listen for other devices so I'm borrowing this from PA2
#serverSocket.settimeout(10)

def signalHandler(sig, fram):
    print("SigInt Pressed. Exiting Now")
    serverSocket.close()

signal.signal(signal.SIGINT, signalHandler)

#Also going to borrow the bit that will give us the machine's IP rather than loopback
ips = check_output(['hostname', '--all-ip-addresses']).decode().split()
print(f"FTP server running at address {ips[0]}") #Works

#Now we need to listen for incoming connections
serverSocket.listen(5) #I don't think we should ever need this many connections, but just in case

## So passing client connection as a parameter, we can still have our functions up here
'''
Alright, so we'll need functions for:
CONNECT (possibly) - which will connect a client to a server at a given port number
LIST - showing the files of the current directory of the server
RETRIEVE - which will send back a file
STORE - which will let the client send up a file
QUIT - which closes the connection
'''

#Not sure if we're going to have one for connection on this side just yet


#LIST seems like an easy one to start with though
def ls(clientSocket):
    try:
        # Get list of files in the current directory
        files = os.listdir(os.getcwd())
        num_files = len(files)
        totalSize = 0

        # Send the number of files to the client
        clientSocket.send(struct.pack('i', num_files))

        # Iterate over each file and send file details to the client
        for filename in files:
            # Send the length of the filename
            filename_length = len(filename)
            clientSocket.send(struct.pack('i', filename_length))

            # Send the filename
            clientSocket.send(filename.encode())

            # Get file size
            file_size = os.path.getsize(filename)
            totalSize += file_size
            clientSocket.send(struct.pack('i', file_size))
            clientSocket.recv(BUFFER_SIZE)

        clientSocket.send(struct.pack('i', totalSize))
        print(f"Sent {num_files} file(s) to the client.")
        clientSocket.recv(BUFFER_SIZE)

    except Exception as e:
        print(f"Error in ls function: {e}")
        clientSocket.close()

def quit(clientConnection):
    print(f"Initiating quit from {clientConnection}")
    #send quit confirmation
    clientConnection.send("1".encode())
    #close and restart server
    #clientConnection.close()
    #serverSocket.close()


# I'm realizing it would probably make more sense to just stop an invalid message
# from even going out on the client side... but I think Ima still leave this in here
def invalidCommand(clientConnection, message):

    messageBytes = message.encode()
    messageLength = len(messageBytes)

    try:
        clientConnection.send("i", messageLength)

        clientConnection.sendall(messageBytes)
    except:
        print("Invalid server command detected")
        #should we close the server here?

#handle incoming connections and handle requests from the client-side

def store(clientConnection):
    print("Store Pressed")

    try:
        clientConnection.send(b"1")

        #Now we need to receive and deal with file details
        fileNameSize = struct.unpack("i", clientConnection.recv(4))[0]
        fileName = clientConnection.recv(fileNameSize)
        print(f"Client requesting upload of file: {fileName}")

        #Send message to let client know the server is ready to receive
        clientConnection.send(b"1")

        #Now for the file size
        fileSize = struct.unpack("i", clientConnection.recv(4))[0]

        outputFile = open(fileName, "wb")

        bytesReceived = 0 #This will keep track of the number of bytes we've sent over (kind of like we did in the other one)

        print("Receiving upload from client")
        while bytesReceived < fileSize:
            chunk = clientConnection.recv(BUFFER_SIZE)
            print(chunk)
            outputFile.write(chunk)
            bytesReceived += BUFFER_SIZE
        outputFile.close()

        print("File upload complete")
        clientConnection.send(b"1")
    except Exception as e:
        print(f"Error uploading file: {e}")

def retrieve(clientConnection):
    print("Retrive Pressed")

    clientConnection.send(b"1")
    filename_length = struct.unpack("i", clientConnection.recv(4))[0]

    filename = clientConnection.recv(filename_length)
    print(f"Client requested file: {filename}\nChecking if that exists...")

    #does the requested file exist?
    if os.path.isfile(filename):
        clientConnection.send(struct.pack("i", len(filename)))
    else:
        print("File does not exist at this FTP server")
        clientConnection.send(struct.pack("i", -1))
        return
    #Now we need to wait for the okay to sesnd the file
    clientConnection.recv(BUFFER_SIZE)

    print("Sending file to client...")
    content = open(filename, "rb")

    #Gotta break it into chunks defined by the buffer size
    chunk = content.read(BUFFER_SIZE)
    while chunk:
        clientConnection.send(chunk)
        chunk = content.read(BUFFER_SIZE)
    content.close()

    print("Download complete")
    #Final check
    clientConnection.recv(BUFFER_SIZE)


def handleClient(clientSocket):
    try:
        while True:

            data = clientSocket.recv(BUFFER_SIZE)

            if not data:
                print(f"{clientAddress} has disconnected from the server")
                break

            command = data.decode().strip()
            print(command)

            match command.upper():
                case "LIST":
                    ls(clientConn)
                # some other stuff will go here in a minute
                case "QUIT":
                    quit(clientConn)
                case "RETRIEVE":
                    retrieve(clientConn)
                case "STORE":
                    store(clientConn)
                case _:
                    #invalidCommand(clientConn, "Error! Invalid command detected")
                    print(f"Extraneous/invalide command: {command}")
    except Exception as e:
        print(f"Error handling client: {e}")
while True:

    clientConn, clientAddress = serverSocket.accept()
    print(f"Connection established with {clientConn}")


    handleClient(clientConn)

    # This is where the acutal stuff will happen

    clientConn.close()

# And then this is where the server socket will close
serverSocket.close()
