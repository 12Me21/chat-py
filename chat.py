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

def displaymessage(message):
    if message["id"] in messageids:
        return
    messageids.append(message["id"])
    text=message["message"].replace("&apos;","'").replace("&quot;","\"").replace("&gt;",">").replace("&lt;","<")
    print(message["sender"]["username"]+": "+text)
    

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
    elif type=="messageList":
        for msg in message["messages"]:
            displaymessage(msg)
    elif type=="userList":
        pass
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
    while 1:
        message=sys.stdin.readline()
        sendmessage(message,"offtopic")

def on_open(ws):
    print("sending bind...");
    ws.send(json.dumps({
        "type":"bind",
        "uid":uid,
        "lessData":True,
        "key":auth
    }))
    _thread.start_new_thread(run,())

#websocket.enableTrace(True)
ws=websocket.WebSocketApp(
    "ws://chat.smilebasicsource.com:45695/chatserver",
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)
ws.on_open=on_open
ws.run_forever()
