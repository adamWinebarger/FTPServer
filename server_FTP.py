import os
import struct
import sys

from socket import *
from subprocess import check_output

## Socket Setup

TCP_PORT = 6969 #why not

BUFFER_SIZE = 1024 # I guess this is pretty standard
serverSocket = socket(AF_INET, SOCK_STREAM)

serverSocket.bind(('', TCP_PORT)) #I think we'll want this to listen for other devices so I'm borrowing this from PA2
#serverSocket.settimeout(10)

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
    clientConnection.close()
    serverSocket.close()


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
while True:

    clientConn, clientAddress = serverSocket.accept()
    print(f"Connection established with {clientConn}")

    #Now we need our data
    data = clientConn.recv(1024)
    print(data)

    if not data:
        #No data means that the client has closed the connection
        print(f"{clientAddress} has disconnected from the server")
    else:
        command = data.decode().strip()
        print(command)

        match command.upper():
            case "LIST":
                ls(clientConn)
            # some other stuff will go here in a minute
            case "QUIT":
                quit(clientConn)

            case _:
                invalidCommand(clientConn, "Error! Invalid command detected")

    # This is where the acutal stuff will happen

    #clientConn.close()

# And then this is where the server socket will close
#serverSocket.close()
