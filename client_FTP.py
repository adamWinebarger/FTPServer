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
        serverName = ip
        clientSocket.connect((ip, serverPort))
        #clientSocket.recv(BUFFER_SIZE) # remember we're setting the buffer here in connect
        print("Connection Successful")
        return True
    except Exception as e:
        print(f"Unable to connect to {ip}. Please double-check your settings or try again later\nError: {e}")
        return False

def quit(qCode = '0'):
    if isConnected:
        #ip, port = clientSocket.getpeername()
        clientSocket.send("QUIT".encode())
        #wait for server go-ahed
        clientSocket.recv(BUFFER_SIZE)
        clientSocket.close()
        print(f"Disconnected from server {serverName}.")
        #serverName = ''
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
        - HELP: Show this menu again
        '''
    )

def ls(clientSocket):
    try:
        # Send the 'LIST' command to the server
        clientSocket.send(b'LIST')

        # Receive the number of files
        num_files_data = clientSocket.recv(4)
        num_files = struct.unpack('i', num_files_data)[0]
        print(num_files)

        # Receive and print details of each file
        for _ in range(num_files):
            # Receive filename length
            filename_length_data = clientSocket.recv(4)
            filename_length = struct.unpack('i', filename_length_data)[0]

            # Receive filename
            filename = clientSocket.recv(filename_length).decode()

            # Receive file size
            file_size_data = clientSocket.recv(4)
            file_size = struct.unpack('i', file_size_data)[0]

            # Print file details
            print(f"File: {filename} - Size: {file_size} bytes")

            # Send acknowledgment to the server
            clientSocket.send(b'1')

        # Receive the total directory size
        total_directory_size_data = clientSocket.recv(4)
        total_directory_size = struct.unpack('i', total_directory_size_data)[0]
        print(f"Total directory size: {total_directory_size} bytes")
        clientSocket.send(b'1')
        return

    except Exception as e:
        print(f"Error in ls function: {e}")

    finally:
        # Send final acknowledgment to the server
        clientSocket.send(b'1')

def retrieve(clientSocket, filePath):
    #print("Client pressed store")
    if filePath is None:
        print("Error. Must provide argument in the form of a filepath")
        return

    try:
        clientSocket.send(b"RETRIEVE")
    except Exception as e:
        print(f"Error with making server request: {e}")
    try:
        #first wait for okay from the server
        clientSocket.recv(BUFFER_SIZE)
        #Now we'll send the file name along
        clientSocket.send(struct.pack("i", len(filePath)))
        clientSocket.send(filePath)

        #get file size if it exists
        print("retrieving file from server")

        fileSize = struct.unpack("i", clientSocket.recv(4))[0]

        if fileSize <= 0:
            print("File does not exist. Please recheck your naming and try again")
            return

    except:
        print("Error checking files")
    try:
        #So now we'll send the okay to send the file along
        clientSocket.send("1")
        outputFile = open(fileName, "wb")

        bytesReceived = 0

        print("Transferring file from server")
        while bytesReceived < fileSize:

            #Basically, we have to send it over in chunks defined by our buffer
            chunk = clientSocket.recv(BUFFER_SIZE)
            outputFile.write(chunk)
            bytesReceived += BUFFER_SIZE
        outputFile.close()
        print("Download complete")

        #message letting the server know we're disconnected
        clientSocket.send(b"1")
    except Exception as e:
        print(f"Error downloading file: {e}")



def store(clientSocket, filePath):
    #print("Client pressed retrieve")
    if filePath is None:
        print("Error. Must provide argument in the form of a filepath")
        return

    try:
        clientSocket.send(b"STORE")
    except Exception as e:
        print(f"Error with storing: {e}")


### Driver code ###

# Our little catchment so that we can pass a server IP in through argv if we want to
if len(sys.argv) >= 2:
    if (isIP(sys.argv[1])):
        serverName = sys.argv[1]
        isConnected = connect(serverName)

print("Welcome to the FTP client-side... thing")
printMenu()


while True:

    command = input(f"Input your command: ")
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
                ls(clientSocket)
                #isConnected = False
            case "HELP":
                show_menu()
            case "STORE":
                store(clientSocket, tokens[1] if len(tokens) > 1 else None)
            case "RETRIEVE":
                retrieve(clientSocket, tokens[1] if len(tokens) > 1 else None)


            case _ :
                print("Error! Invalid command detected")

    command = None
    tokens = None
    action = None
