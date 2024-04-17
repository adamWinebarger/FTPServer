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
def ls(clientConnection): #of course we're going to call it ls
    print("Listing files")

    #getting files from current working directory
    lst = os.listdir(os.getcwd())

    #first let's send the number of files that the client should expect. helps with overhead and error detection
    clientConnection.send(struct.pack("i", len(lst)))

    totalSize = 0
    try:
        for i in lst:
            #file name size
            print(i)
            clientConnection.send(struct.pack("i", sys.getsizeof(i)))

            #file name
            clientConnection.send(i.encode())

            #File content size
            clientConnection.send(struct.pack("i", os.path.getsize(i)))

            totalSize += os.path.getsize(i) #adding the size of file i to our totalSize

            #make sure client and server are synced
            clientConnection.recv(BUFFER_SIZE)

        #total size of all files in the directory
        clientConnection.send(struct.pack("i", totalSize))

        #one last check
        serverSocket.recv(BUFFER_SIZE)
        print("File List Sent Successfully")

    except Exception as e:
        print(f"Error occurred in file listing {e}")
        #if e.args[0] == 107 or e.args[0] == 32 or e.args[0] == 104:
        clientConnection.close()
        return

def quit(clientConnection):
    print(f"Initiating quit from {clientConnection}")
    #send quit confirmation
    clientConnection.send("1".encode())
    #close and restart server
    clientConnection.close()
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
serverSocket.close()
