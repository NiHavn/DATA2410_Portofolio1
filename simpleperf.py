import sys
import socket
import time
import argparse

def print_table(results):                                                                   #Helps print the results to the server and client and makes it into a table format
    print("{:<20} {:<20} {:<20} {:<20}".format("ID", "Interval", "Transfer", "Bandwidth"))  #Line 7 and 9 is formating the rows and columns in the table

    for row in results:
        print("{:<20} {:<20} {:<20} {:<20}".format(row["Client Address"], row["Interval"], row["Transfer"], row["Bandwidth"]))

    print()  #Prints the results

def print_final_result(results):
    print("--------------------------------------------------")
    print_table(results)

def server_mode(ip, port):                                              #Function to establish server parameters
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #Establishes a server socket for the client to connect
    server_socket.bind((ip, port))                                      #And binds the server to an ip
    server_socket.listen(10)                                            #The server listens for up to 10 clients
    print("-----------------------------------------------")
    print("A simpleperf server is listening on port", port)             #Communicates that the server is ready to recieve transmition
    print("-----------------------------------------------")

    while True:
        connection, client_address = server_socket.accept()                 #Accepts the connection                                            #Starts a timer for later calculations
        start_time = time.time()
        total_data_received = 0                                             #Initiates a variable for the amount of data revieved throuout the transmition
        
        results = []                                                        #Makes an array variable for the result to be printed later
        
        while True:                                                         #Loops the server to continously recieve data
            data = connection.recv(1000)                                    #Amount of bits recieved for each loop
            total_data_received += len(data)                                #Adds the amount of bits recieved to the total_data varialbe 
            
            if not data or b"BYE" in data:                                  #This if test tests for either no data or if the data i containing BYE
                connection.send('ACK BYE'.encode())                         #If it is empty or contains BYE it will send an ACK BYE to client
                break                                                       #breaks the while loop                                                #Prints the table from the print_table def
        bandwidth = ((total_data_received / 1000000) / (time.time() - start_time)) * 8
        results.append({
            "Client Address": f"{client_address[0]}:{client_address[1]}",
            "Interval": f"0.0 - {time.time() - start_time:.1f}",
            "Transfer": f"{total_data_received / 1000000:.2f} MB",
            "Bandwidth": f"{bandwidth:.2f} Mbps"     
        })
        connection.close()                                                  #Closes the connection
        print_final_result(results)

def client_mode(server_ip, port, data_to_send_in_MB, duration, interval):         #def to create client parameters
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #Creates a client socket
    client_socket.connect((server_ip, port))                            #And connects to the server

    total_data_to_send = 0                                              #Initiates a variable for data to send
    if data_to_send_in_MB is not None:                                  #If the amount of data to sent is not given, total data to send will be 
        total_data_to_send = data_to_send_in_MB                         #set to infinity
    else:
        total_data_to_send = float('inf')                               

    data_sent = 0                                                       #Initiates a variable for the data sent
    start_time = time.time()                                            #Start time for the connection to server for later calcutations
    interval_start_time = time.time()
    interval_data_sent = 0
    results = []
    new_interval = False

    while data_sent < total_data_to_send and time.time() - start_time <= duration:      #Makes sure the client keeps sending data either until time limit is reached, or the total data to send is less than data sent
        data = b'0' * 1000                                                              #Makes 1000 bytes to send
        client_socket.send(data)                                                        #sends the data created
        data_sent += len(data)                                                          #adds the amount sent to the data_sent variable
        interval_data_sent += len(data)

        current_time = time.time()
        elapsed_interval_time = current_time - interval_start_time
        if interval is not None and elapsed_interval_time >= interval:
            new_interval = True
            elapsed_time = time.time() - interval_start_time
            bandwidth = ((interval_data_sent / 1000000) / elapsed_time) * 8
            results.append({
                "Client Address": f"{server_ip}:{port}",
                "Interval": f"{interval_start_time - start_time:.1f} - {current_time - start_time:.1f}",
                "Transfer": f"{interval_data_sent / 1000000:.2f} MB",
                "Bandwidth": f"{bandwidth:.2f} Mbps"
            })
            interval_start_time = current_time
            interval_data_sent = 0

        if new_interval:
            print_table(results)
            results = []
            new_interval = False

    client_socket.send(b"BYE")                                          #When the client is done sending it sends a BYE message
    client_socket.recv(1000)                                            
        
    elapsed_time = time.time() - start_time                             #Time variable used for calculations
    bandwidth = (data_sent / 1000000) / elapsed_time                    #Calculates the bandwith
    result = {                                                          #Result variable used to create a table for print
        "Client Address": f"{server_ip}:{port}",
        "Interval": "0.0 - " + f"{elapsed_time:.1f}",
        "Transfer": f"{round(data_sent / 1000000, 2)} MB",
        "Bandwidth": f"{round(bandwidth * 8, 2)} Mbps"
    }
    print_final_result([result])                                               #Prints the results in a table
    client_socket.close()                                               #Closes connection

def main():
    parser = argparse.ArgumentParser(description="A simple network throughput measurement tool.")   #Used to 
    parser.add_argument("-s", "--server", action="store_true", help="Run simpleperf in server mode.")
    parser.add_argument("-c", "--client", action="store_true", help="Run simpleperf in client mode, connecting to specified server IP.")
    parser.add_argument("-n", "--num", default=None, type=int, help="Amount of data to send in client mode (in MB).")
    parser.add_argument("-p", "--port", type=int, default=5001, help="Port to use (default: 5001).")
    parser.add_argument("-I", "--serverip", type=str, default="127.0.0.1")
    parser.add_argument("-b", "--bind", type=str, default="127.0.0.1")
    parser.add_argument("-t", "--time", type=int, default=25)
    parser.add_argument("-i", "--interval", type=int, default=None)
    parser.add_argument("-P", "--parallel", type=int, default=1)

    args = parser.parse_args()

    if args.server:
        server_mode(args.bind, args.port)
    elif args.client:
        client_mode(args.serverip, args.port, args.num, args.time, args.interval)
    else:
        print("--error--, must be in server or client mode")
        parser.print_help()

if __name__ == "__main__":
    main()
