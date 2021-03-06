# -*- coding: utf-8 -*-
"""rdt_udp_client_final.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1TE-bL_7Wta0TNCfc6U84-X9VQbeb2V_i
"""

import socket
from socket import timeout
import time
import sys
import os
import struct

BUFFER_SIZE = 1000

serverName = 'localhost'

PortRecv = 15001
PortSend = 15000

recv = (serverName, PortRecv)
send = (serverName, PortSend)

recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

recv_sock.bind(recv)

recv_sock.settimeout(5)

def process_ACK(message):
    if message == "":
        return  []
    acks = ([int(x) for x in message.split(",")])
    acks.sort()
    return acks

# 2 modes, create and update
# In update, first extra argument would be the ACK array from the server
#            second extra argument would be the last positive ack
def update_queue(arr=[], mode="create", N=100, neg_acks = [], last_ack=-1):
    global seq
    global content
    if mode=="create":
        seq = 0
        data = content.read(BUFFER_SIZE)
        while N>0 and data != b'':
            arr += [(seq, data)]
            seq += 1
            N -= 1
            # Prevent reading extra bits
            if N>0:
                data = content.read(BUFFER_SIZE)
    elif mode=="update":
        seq = arr[-1][0] + 1
        index = 0
        ack_index = 0
        
        # Removing successfully transmitted packets
        while index<len(arr) and arr[index][0]<=last_ack:
            if ack_index==len(neg_acks):
                #print("Element:{} popped".format(arr[index][0]))
                arr.pop(index)
            elif neg_acks[ack_index] > arr[index][0]:
                #print("element:{} popped".format(arr[index][0]))
                arr.pop(index)
            elif neg_acks[ack_index] == arr[index][0]:
                #print("Element:{} skipped".format(arr[index][0]))
                index += 1
                ack_index += 1
        
        # Adding new packets in new empty spaces
        extra_space = N-len(arr)
        if extra_space>0:
            data = content.read(BUFFER_SIZE)
            while extra_space>0 and len(data) >0:
                arr += [(seq, data)]
                seq += 1
                extra_space -= 1
                if extra_space>0:
                    data = content.read(BUFFER_SIZE)
    return arr

def make_packet(seq,ack,data):
    seq_field = (seq).to_bytes(4,byteorder='big')
    ack_field = (ack).to_bytes(4,byteorder='big')
    packet =  seq_field + ack_field + data
    return packet


def upld(file_name):
    global seq
    global content
    seq = 0
    content = open(file_name, "rb")
    finished = os.path.getsize(file_name)//BUFFER_SIZE
    N = 10000
    last_ack = -1
    start_time = time.time()
    current_queue = update_queue(N=N)
    print(len(current_queue))
    while current_queue:
        for part in current_queue:
            packet = make_packet(part[0], finished, part[1])
            send_sock.sendto(packet,send)
            # This is important because otherwise the socket buffer drops packets otherwise
            time.sleep(0.001)
        print("Sent next Queue")
        while True:
            try:
                response ,address = recv_sock.recvfrom(4096)
                if last_ack < int.from_bytes(response[4:8],byteorder='big'):
                    break
            except timeout:
                break
        recv_sock.settimeout(3)
        negative_acks = process_ACK(response[8:].decode())
        last_ack = int.from_bytes(response[4:8],byteorder='big')  # Last positive ack is stored here
        print("Negative ACKs Length:{}".format(len(negative_acks)))
        current_queue = update_queue(current_queue, mode="update", N=N, neg_acks = negative_acks, last_ack=last_ack)
        print("Length of current_queue:{}".format(current_queue))
        print("Progress:{}".format(100*seq/finished))
    # record throughput and time etc
    content.close()
    print("Total tim taken:{} secs\nOverall Throughput:{} bps".format(time.time()-start_time, 104.8*1024*1024*8/(time.time()-start_time)))
    return

def upld_p(file_name): 
    # Upload a file
    print ("\nUploading file: {}...".format(file_name))
    try:
        # Check the file exists
        content = open(file_name, "rb")
    except:
        print ("Couldn't open file. Make sure the file name was entered correctly.")
        return
    try:
        # Make upload request
        cp.sendall(b'UPLD')
    except:
        print ("Couldn't make server request. Make sure a connection has bene established.")
        return
    try:
        # Wait for server acknowledgement then send file details
        # Wait for server ok
        cp.recv(BUFFER_SIZE)
        # Send file name size and file name
        cp.send(struct.pack("h", sys.getsizeof(file_name)))
        cp.send(file_name.encode())
        # Wait for server ok then send file size
        cp.recv(BUFFER_SIZE)
        cp.send(struct.pack("i", os.path.getsize(file_name)))
    except:
        print ("Error sending file details")
    return



# Initialise socket stuff
TCP_IP = "127.0.0.1" # Only a local server

CP_PORT_SERV = 9029 # CONTROL PROCESS PORT


BUFFER_SIZE = 1024 # Standard chioce

cp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def link():
    # Connect to the server
    print( "Sending server request...")
    try:
        cp.connect((TCP_IP, CP_PORT_SERV))
        print( "Connection unsucessful")
        #cp.sendall((str(DTP_PORT_CLT).encode('UTF-8')))
    except:
        print( "Connection unsucessful. Make sure the server is online.")
        
    

def quit():
    cp.send(b"QUIT")
    # Wait for server go-ahead
    cp.recv(BUFFER_SIZE)
    cp.close()
    recv_sock.close()
    send_sock.close()
    print ("Server connection ended")
    return

print ("\n\nWelcome to the FTP client.\n\nCall one of the following functions:\nCONN           : Connect to server\nUPLD file_path : Upload file\nLIST           : List files\nDWLD file_path : Download file\nDELF file_path : Delete file\nQUIT           : Exit")

while True:
    # Listen for a command
    prompt = input("\nEnter a command: ")
    if prompt[:4].upper() == "CONN":
        conn = link()
    elif prompt[:4].upper() == "UPLD":
        #print("first upload")
        file_name=prompt[5:]
        upld_p(file_name)
        upld(file_name)
    elif prompt[:4].upper() == "QUIT":
        quit()
        break
    else:
        print ("Command not recognised; please try again")

