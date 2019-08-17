#!/usr/bin/env python3
import http.client
import websocket
import json
import hashlib
import _thread
import sys

h=http.client.HTTPConnection("smilebasicsource.com")

username=0
passwordhash=0
session=0
auth=0
uid=0

def getlogin(force=False):
    global username,passwordhash
    if not force:
        try:
            with open("login.txt") as loginfile:
                username=loginfile.readline()[:-1]
                passwordhash=loginfile.readline()
            return
        except IOError:
            pass
    username=input("username")
    passwordhash=hashlib.md5(bytes(input("password"),"ascii")).hexdigest()
    with open("login.txt","w") as loginfile:
        loginfile.write(username+"\n")
        loginfile.write(passwordhash)

def getsession(force=False):
    global session,username,passwordhash
    if not force:
        try:
            with open("session.txt") as sessionfile:
                session=sessionfile.readline()
                return
        except IOError:
            pass
    print("logging in...")
    h.request("POST",url="/query/submit/login?session=x&small=1",headers={"Content-Type":"application/x-www-form-urlencoded"},body="username="+username+"&password="+passwordhash)
    resp=h.getresponse()
    if resp.status!=200:
        return
    data=resp.read()
    data=json.loads(str(data,"ascii"))
    session=data["result"]
    if not session:
        return
    with open("session.txt","w") as sessionfile:
        sessionfile.write(session)
        
def getauth():
    global auth,session,uid
    print("requesting auth...")
    h.request("GET",url="/query/request/chatauth?session="+session)
    resp=h.getresponse()
    if resp.status!=200:
        return
    data=resp.read()
    data=json.loads(str(data,"ascii"))
    auth=data["result"]
    uid=data["requester"]["uid"]

getlogin()
getsession()
if not session:
    print("couldnt get session")
    exit()
getauth()
if not auth:
    print("couldn't get auth, maybe session expired?")
    getsession(True)
    getauth()
    if not auth:
        print("auth failed")
        exit()

messageids=[]

def converthtml(text):
    return text.replace("&apos;","'").replace("&quot;","\"").replace("&gt;",">").replace("&lt;","<")

def roomname(tag):
    if tag[0:4]=="room":
        tag=tag[5:]
    else:
        tag=tag[0]
    return tag

def displaymessage(message):
    #print(message)
    if message["id"] in messageids:
        return
    messageids.append(message["id"])

    type=message["type"]
    encoding=message["encoding"]
    if encoding=="raw" or encoding=="text":
        text=converthtml(message["message"])
        if type=="system":
            text="        "+text
        elif type=="warning":
            text="!       "+text
        elif type=="module":
            text=roomname(message["tag"])+"; "+text
        elif type=="message" or type=="image":
            text=roomname(message["tag"])+": "+message["sender"]["username"]+": "+text
    elif encoding=="draw":
        text="[drawing]"
    else:
        text="UNKNOWN ENCODING: "+encoding
    print(text)

user_list = []
room_list = []
cur_room = "offtopic"

def handle_userlist(users):
    global user_list
    user_list = users

def handle_rooms(rooms):
    global room_list
    room_list = rooms

def print_roomlist():
    global room_list
    for room in room_list:
        text = room["name"]+": "
        for user in room["users"]:
            text += user["username"]+" "
        print(text)

def print_userlist():
    global user_list
    for user in user_list:
        print(user["username"])
    
def on_message(ws, message):
    message=json.loads(message)
    type=message["type"]
    if type=="response":
        from_pythonsucks=message["from"]
        if from_pythonsucks=="bind":
            ws.send(json.dumps({
                "type":"request",
                "request":"messageList"
            }))
        elif message["result"]!=True:
            print("unknown response:", message);
    elif type=="messageList":
        for msg in message["messages"]:
            displaymessage(msg)
    elif type=="userList":
        handle_userlist(message["users"]);
        handle_rooms(message["rooms"]);
    else:
        print("unknown websocket message type: "+type)
        #displayuserlist(message["users"])
        #displayrooms(message["rooms"])
    #print(message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("CLOSED")

def sendmessage(text,room):
    ws.send(json.dumps({
        "type":"message",
        "text":text,
        "key":auth,
        "tag":room
    }))
    
def run():
    global cur_room
    while 1:
        message=input()#sys.stdin.readline()
        if message=="/ul":
            print_userlist()
        elif message=="/rl":
            print_roomlist()
        elif message[0:2]=="/r":
            cur_room = message[3:]
        elif message=="/reconnect":
            websocket.close()
        else:
            sendmessage(message,cur_room)

def on_open(ws):
    websocket.setdefaulttimeout(9999999)
    print("Websocket connected")
    print("sending bind...")
    ws.send(json.dumps({
        "type":"bind",
        "uid":uid,
        "lessData":True,
        "key":auth
    }))
    _thread.start_new_thread(run,())

print("starting websocket")
#websocket.enableTrace(True)
websocket.setdefaulttimeout(9999999)

ws=websocket.WebSocketApp(
    "ws://chat.smilebasicsource.com:45695/chatserver",
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
)
ws.on_open=on_open
print(".")
ws.run_forever()
