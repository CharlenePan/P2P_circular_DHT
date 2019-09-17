from socket import *
import sys
import time
import threading
import re

class Peer():
    def __init__(self,argv):
        self.peerid=int(argv[1])
        self.suc1=int(argv[2])
        self.suc2=int(argv[3])
        self.psc=[]# a set to store pscs
        self.psc1=0
        self.psc2=0
        self.is_alive=1 # 1 alive ,0 down
        self.input='input'
        self.file=0 #2012
    def get_psc(self):
        return self.psc
    def get_suc1(self):
        return self.suc1
    def get_suc2(self):
        return self.suc2
    def get_is_alive(self):
        return self.is_alive
    def get_input(self):
        return self.input

        
    def hush(self):
        return int(self.file%256) #220
        
    def get_file(self):# 1 has the file ,0 do not have the file
        n=self.hush() #220
        self.psc1=self.get_psc1()
        if (n<=self.peerid and n>self.psc1 and self.peerid>self.psc1) or (self.peerid<self.psc1 and n>self.psc1):
            return 1
        else:
            return 0
       
    def get_psc1(self):
        self.psc=self.get_psc()
        if len(self.psc)==2:
            if (self.psc[0]>self.peerid and self.psc[1]<self.peerid) or(self.psc[0]<self.peerid and self.psc[1]>self.peerid):
                if self.psc[0]<self.psc[1]:
                    self.psc1=self.psc[0]
                else:
                    self.psc1=self.psc[1]
                return self.psc1
            else:
                if self.psc[0]>self.psc[1]:
                    self.psc1=self.psc[0]
                else:
                    self.psc1=self.psc[1]
                return self.psc1
            
        
    def get_psc2(self):
         self.psc=self.get_psc()
         if len(self.psc)==2:
            if (self.psc[0]>self.peerid and self.psc[1]<self.peerid) or(self.psc[0]<self.peerid and self.psc[1]>self.peerid):
                if self.psc[0]>self.psc[1]:
                    self.psc2=self.psc[0]
                else:
                    self.psc2=self.psc[1]
                return self.psc2
            else:
                if self.psc[0]<self.psc[1]:
                    self.psc2=self.psc[0]
                else:
                    self.psc2=self.psc[1]
                return self.psc2


#-------------------------TCP Server---------------------------
def tcpserver(peer,connectionsocket,senderadd): #server
    msg=connectionsocket.recv(1024)# 1008request 2012   #1quit101010121015
    time.sleep(1)
    message=msg.decode()
    #----------------------------quit server-------------------------
    if re.match('^1quit',message) or re.match('^2quit',message):
        departure=int(message[5:9])-1000 #10
        print('Peer {0} will depart from the network.'.format(departure))
        if message[0]=='1':
            peer.suc1=int(message[9:13])-1000 #12
            peer.suc2=int(message[13:])-1000 #15
        elif message[0]=='2':
            peer.suc2=int(message[9:13])-1000 #12
        print('My first successor is now peer {0}.'.format(peer.get_suc1()))
        print('My second successor is now peer {0}.'.format(peer.get_suc2()))
        connectionsocket.close()
    #----------------------------kill server-------------------------
    elif re.match('^ask',message):# server 8 peer=8     peer=4
        response=str(peer.get_suc1()+1000) # '1012'     #1008
        connectionsocket.send(response.encode())

    #------------------server who request for the file--------------
    else:
        if re.match('^has',message):  # has10012012
            id=int(message[3:7])-1000 #1
            file=int(message[7:]) #2012
            print('Received a response message from peer {0}, which has the file {1}.'.format(id,file))
            connectionsocket.close()
        #------------------server who received the file request message--------------------------
        else:
            filename=message[12:]#2012
            peer.file=int(filename) #2012
            
            if peer.get_file(): #if has the file  #1 server
                print('File {0} is here.'.format(peer.file))
                id=int(msg[:4].decode())-1000 #8
                print('A response message,destined for peer {0} has been sent.'.format(id))
                connectionsocket.close() #close the pre connection  15---1
                #create thread for client 1
                tc=threading.Thread(target=tcpclient_has,args=(peer,msg))# peer = 1
                tc.start()
            
            else:#pass the message to peer.suc1   server 10
                print('File {0} is not stored here.'.format(peer.file))
                print('File request message for {0} has been forwarded to my successor.'.format (int(msg[12:].decode())))
                connectionsocket.close() #close the pre connection
                #create thread for client 10
                tc=threading.Thread(target=tcpclient,args=(peer,msg))# peer = 10
                tc.start()


#-------------------------TCP Client---------------------------
def tcpclient(peer,msg):# does not have the file
    newc=socket(AF_INET, SOCK_STREAM)
    newc.connect(('127.0.0.1',int(50000+peer.get_suc1()))) #peer 10 send connection request to 12
    pass_msg=msg # 1008request 2012   already encoded
    newc.send(pass_msg)# 10 pass the msg to server 12
    newc.close()

def tcpclient_has(peer,msg):# has the file  #client 1
    newc=socket(AF_INET, SOCK_STREAM)
    id=int(msg[:4].decode())-1000 #8
    newc.connect(('127.0.0.1',int(50000+id))) #client 1 send connection request to server 8
    response='has'+str(peer.peerid+1000)+msg[12:].decode() #has10012012
    newc.send(response.encode())# 1 send the response to server 8
    newc.close()

def tcp_requesting(peer):# tcp client 8
    rs=socket(AF_INET, SOCK_STREAM)
    rs.connect(('127.0.0.1',int(50000+peer.get_suc1()))) # connect to its successor
    request_msg=str(1000+peer.peerid)+peer.input # 1008request 2012
    rs.send(request_msg.encode())
    print('File request message for {0} has been sent to my successor.'.format(request_msg[12:16]))
    rs.close()

def quitclient(peer,msg):# client 10
    s1=socket(AF_INET, SOCK_STREAM)# psc1  peer 8
    s1.connect(('127.0.0.1',int(50000+peer.get_psc1())))
    s2=socket(AF_INET, SOCK_STREAM)# psc2  peer 5
    s2.connect(('127.0.0.1',int(50000+peer.get_psc2())))
    msg1=str(1)+msg #1quit101010121015
    msg2=str(2)+msg #2quit101010121015
    s1.send(msg1.encode())
    s2.send(msg2.encode())
    s1.close()
    s2.close()

def killclient(peer,msg): #client 4    3
    s=socket(AF_INET, SOCK_STREAM)
    s.connect(('127.0.0.1',int(50000+int(msg[3:])-1000))) #50008    #50004
    s.send(msg.encode())
    response=s.recv(1024) #'1012'        #1008
    res=response.decode()
    peer.suc2=int(res)-1000 #12          #8
    print('My second successor is now peer {0}.'.format(peer.get_suc2()))
    s.close()

#---------------------INPUT----------------------------
class Input_thread(threading.Thread):#tcp client
    def __init__(self,peer):
        super(Input_thread, self).__init__()
    
    def run(self):
        while peer.get_is_alive():
            inputline=sys.stdin.readline()
            #-------------------request file-------------------------
            if re.match('^request [0-9][0-9][0-9][0-9]$',inputline):
                peer.input=inputline
                t=threading.Thread(target=tcp_requesting,args=(peer,))
                t.start()
    
            #-------------------quit---------------------
            if re.match('^quit$',inputline):
                peer.input=inputline
                msg='quit'+str(peer.peerid+1000)+str(peer.suc1+1000)+str(peer.suc2+1000) #quit101010121015
                t=threading.Thread(target=quitclient,args=(peer,msg))# create thread for client 10
                t.start()
                peer.is_alive=0
                
#-----------------------------------------------------------------
class TCP_thread(threading.Thread):#tcp server
    def __init__(self,peer):
        super(TCP_thread, self).__init__()
    
    def run(self):
        if peer.get_is_alive():
            serversocket=socket(AF_INET, SOCK_STREAM)
            serversocket.bind(('127.0.0.1',int(50000+peer.peerid))) #peer 10
            serversocket.listen(10)
            while True:
                connectionsocket,senderadd= serversocket.accept()
                t=threading.Thread(target=tcpserver,args=(peer,connectionsocket,senderadd)) #file request
                t.start()
            
#---------------------------UDP---------------------------------------
class Pingclient_thread(threading.Thread):
    def __init__(self,peer):
        super(Pingclient_thread, self).__init__()
    def run(self):
        if peer.get_is_alive():
            t1=threading.Thread(target=pingc1,args=(peer,))
            t2=threading.Thread(target=pingc2,args=(peer,))
            t1.start()
            t2.start()

def pingc1(peer):
    sequence_no1=0
    time_1=0
    while peer.get_is_alive():
        cs1 = socket(AF_INET, SOCK_DGRAM)# Create a UDP socket
        cs1.settimeout(2)# Set timeout of one second for reponse from server
        data1=str(50000+peer.peerid)+'request'+str(sequence_no1)# ping message sequence number
        cs1.sendto(data1.encode(),('127.0.0.1',int(50000+peer.get_suc1())))# sent ping request to its successor
        sequence_no1+=1
        time.sleep(2)
        try:#i expected to receive from its two successors
            pingmsg1,successor1=cs1.recvfrom(1024)
            senderid01=pingmsg1.decode()
            senderid1=int(senderid01[:5])-50000
            sequence1=int(senderid01[12:])
            print('A ping response message was received from Peer{0}'.format(senderid1))
            time_1=0
        except timeout:
            #print('**********5 time out')#ping response has not been received
            time_1+=1
        if time_1==4:   #5 is no longer alive
            print('Peer {0} is no longer alive.'.format(peer.get_suc1()))
            peer.suc1=peer.get_suc2()
            print('My first succesor is now peer {0}.'.format(peer.get_suc1()))
            #create a TCP client thread for client 4
            msg='ask'+str(1000+peer.get_suc1()) #ask1008
            tc=threading.Thread(target=killclient,args=(peer,msg))# peer = 4
            tc.start()
       #cs1.close()


def pingc2(peer):
    sequence_no2=0
    time_2=0
    while peer.get_is_alive():
        cs2 = socket(AF_INET, SOCK_DGRAM)
        cs2.settimeout(2)
        data2=str(50000+peer.peerid)+'request'+str(sequence_no2)
        cs2.sendto(data2.encode(),('127.0.0.1',int(50000+peer.get_suc2())))# sent ping request to its successor
        sequence_no2+=1
        time.sleep(2)
        try:
            pingmsg2,successor2=cs2.recvfrom(1024)
            senderid02=pingmsg2.decode()
            senderid2=int(senderid02[:5])-50000
            sequence2=int(senderid02[12:])
            print('A ping response message was received from Peer {0}.'.format(senderid2))
            time_2=0
        except timeout:
            #print('**********5 time out')#ping response has not been received
            time_2+=1
        if time_2==4:   #5 is no longer alive
            print('Peer {0} is no longer alive.'.format(peer.get_suc2()))
            print('My first succesor is now peer {0}.'.format(peer.get_suc1())) #4
            #create a TCP client thread for client 3
            msg2='ask'+str(1000+peer.get_suc1()) #ask1004
            tc2=threading.Thread(target=killclient,args=(peer,msg2))# peer = 3
            tc2.start()
        #cs2.close()
        
                     

class Pingserver_thread(threading.Thread):
     def __init__(self,peer):
        super(Pingserver_thread, self).__init__()
     
     def run(self):
        ss= socket(AF_INET, SOCK_DGRAM)# Create a UDP socket
        ss.bind(('127.0.0.1',int(50000+peer.peerid))) #declare the server add
        while peer.get_is_alive(): #i expected to receive from its two predecessors
            pingmsg, pingsender = ss.recvfrom(1024)
            senderid0=pingmsg.decode()
            senderid=int(senderid0[:5])-50000
            sequence=int(senderid0[12:])
            if senderid not in peer.psc:
                peer.psc.append(senderid)
            print('A ping request message was received from Peer {0}.'.format(senderid))
            reply=str(50000+peer.peerid)+'respons'+str(sequence)# ping message type ,sequence number
            ss.sendto(reply.encode(),pingsender)
        ss.close()



peer=Peer(sys.argv)
tclient=Pingclient_thread(peer)
tserver=Pingserver_thread(peer)
tinput=Input_thread(peer)# tcp client thread
ttcp=TCP_thread(peer)# tcp server thread

tclient.start()
tserver.start()
tinput.start()
ttcp.start()

                  

