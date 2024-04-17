import ipaddress #might just need the one function
import sys
import os
import struct

from socket import *

#Looking at PA2, I don't remember why I incorporated this function. But it seems
# Like it might be useful later.

#Oh, I did it so I could pass IP addresses in argv. Yeah I'm leaving this in here
def isIP(inputSTR):
    try:
        ipObject = ipaddress.ip_address(inputSTR)
        return True
    except ValueError:
        return False

#So now we need to set up our socket

serverName = '' #left blank for the time being
serverPort = 6969

isConnected = False #Going to have connection tracking as well
BUFFER_SIZE = 1024

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.settimeout(5)
'''
Alright, so we'll need functions for:
CONNECT (possibly) - which will connect a client to a server at a given port number
LIST - showing the files of the current directory of the server
RETRIEVE - which will send back a file
STORE - which will let the client send up a file
QUIT - which closes the connection
'''

def connect(ip):
    #try connecting to the server

    #Gotta have a catchment if we're going to let people pass in their own IPs
    if not isIP(ip):
        print(f"{ip} not a valid IP address. Please try something else")
        return

    print(f"Attempting to connect to {ip}...")

    try:
        clientSocket.connect((ip, serverPort))
        #clientSocket.recv(BUFFER_SIZE) # remember we're setting the buffer here in connect
        print("Connection Successful")
        return True
    except Exception as e:
        print(f"Unable to connect to {ip}. Please double-check your settings or try again later\nError: {e}")
        return False

def quit(qCode = '0'):
    if isConnected:
        ip, port = clientSocket.getpeername()
        clientSocket.send("QUIT".encode())
        #wait for server go-ahed
        clientSocket.recv(BUFFER_SIZE)
        clientSocket.close()
        print(f"Disconnected from server {ip}.")
        #clientSocket = socket(AF_INET, SOCK_STREAM) # So putting this here should theoretically give us a new socket after closing. IT's a bit wasteful, but...
        #isConnected = False
        os._exit(os.EX_OK) #we'll come back to this in a minute
    if not isConnected:
        os._exit(os.EX_OK) #there's probably a better way to do all of this
    if qCode == '1':
        if isConnected:
            clientSocket.close()
        print("Exiting now...")
        os._exit(os.EX_OK)
    if qCode != '1' and qCode != '0':
        print("Error: I am not sure what the quit code you're trying to send is. But please stop it.")

def printMenu():
    print(
        '''Menu options:
        - CONNECT or CONN : Connects to server. Will require IP address. Can also specify port number (default is 6969)
        - LIST or LS : shows files in current working directory
        - RETRIEVE : allows client to get specified filename from server. Requires filename as argument
        - STORE : Allows client to send specified file to server. Requires filename as argument
        - QUIT : Terminates connection to server. Takes additional argument that allows user to also exit the clientside program (0 to stay open, 1 to close; default is 0)
        '''
    )

def ls():

    if not isConnected:
        print("Error! You need to connect to a server first!")
        return

    try:
        clientSocket.send("LIST".encode())
    except:
        ("Unable to make request to server at this time")
        return

    try:
        clientSocket.settimeout(60)
        #clientSocket.recv(BUFFER_SIZE)
        #first we will need the number of files
        #print("Got to here")
        numFiles = struct.unpack("i", clientSocket.recv(4))[0] #should give us a value that we can convert into an int
        print(numFiles)

        #now we need a loop to receive each individual file
        for i in range(int(numFiles)):
            #print("Got to here")
            fileNameSize = struct.unpack("i", clientSocket.recv(4))[0]
            fileName = clientSocket.recv(fileNameSize) #Setting the buffer to be the file size

            fileSize = struct.unpack("i", clientSocket.recv(4))[0]

            print(f"{fileName} - {fileSize}")

            clientSocket.send(b"1") #ensures client/server synchronization

        totalDirectorySize = struct.unpack("i", clientSocket.recv(4))[0]
        print(f"Total Size: {totalDirectorySize}")
        clientSocket.settimeout(5)
    except Exception as e:
        print(f"Could not retrieve listing from server. Please try again later (Error: {e})")
        clientSocket.settimeout(5)
        return
    try:
        clientSocket.send("1".encode())
    except:
        print("Unable to receive final confirmation from server")


### Driver code ###

# Our little catchment so that we can pass a server IP in through argv if we want to
if len(sys.argv) >= 2:
    if (isIP(sys.argv[1])):
        serverName = sys.argv[1]
        isConnected = connect(serverName)

print("Welcome to the FTP client-side... thing")
printMenu()


while True:

    command = input("Input your command: ")
    tokens = command.split()

    if not tokens:
        print("Error! You must enter something in the thing")
    else:

        action = tokens[0].upper()

        match action:

            case "CONN" | "CONNECT":
                if (len(tokens) < 2):
                    print("Error! You must provide an IP address to connect to")
                elif not isConnected:
                    isConnected = connect(tokens[1])
                else:
                    quit()
                    #clientSocket = socket(AF_INET, SOCK_STREAM)
                    isConnected = connect(tokens[1])
            case "QUIT" | "EXIT":
                quit(tokens[1] if len(tokens) > 1 else '0')
                #clientSocket = socket(AF_INET, SOCK_STREAM)
                isConnected = False

            case "LS" | "LIST":
                ls()

            case _ :
                print("Error! Invalid command detected")

    command = None
    tokens = None
    action = None
