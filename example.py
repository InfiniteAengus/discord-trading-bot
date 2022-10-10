from websocket import create_connection
import json
import time
import threading

ACCESS_TOKEN = 'WSWZmsVc3U0pszShO9L2wfj79mcL7'
REFRESH_TOKEN = 'gPYpUHmRdzeW0eVm1V6d1RTHTVoY42'
GATEWAY = 'wss://gateway.discord.gg'

lock = threading.Lock()
last_sequence_number = None

SUBSCRIBED_CHANNELS = ['test-general']
ws = None


def open_websocket():
    global ws
    ws = create_connection(GATEWAY)
    event = receive_json_response(ws)
    if event['op'] != 10:
        raise Exception("Wrong op code for hello.")
    print(event)
    heartbeat_interval = event['d']['heartbeat_interval'] / 1000
    heartbeat(ws)
    threading.Thread(target=heartbeat, args=(ws, heartbeat_interval), daemon=True)


# intents calculator - https://ziad87.net/intents
def send_identify():
    global ws
    payload = {
        "op": 2,
        "d": {
            "token": ACCESS_TOKEN,
            "properties": {
                "os": "linux",
                "browser": "mercenary",
                "device": "mercenary"
            },
            "intents": 33280
        }
    }
    send_json_request(ws, payload)


def send_json_request(ws, request):
    ws.send(json.dumps(request))


def receive_json_response(ws):
    response = ws.recv()
    if response:
        response_obj = json.loads(response)
        if response_obj['op'] == 0:
            set_last_seq(int(response_obj['s']))
        return response_obj


def heartbeatLoop(ws, interval):
    while True:
        time.sleep(interval)
        heartbeat(ws)


def heartbeat(ws):
    heartbeatJSON = {
        "op": 1,
        "d": get_last_seq()
    }
    send_json_request(ws, heartbeatJSON)
    ack = receive_json_response(ws)
    print(ack)
    if ack['op'] != 11:
        raise Exception("Wrong opcode for heartbeat ack " + str(ack['op']))


def get_last_seq():
    with lock:
        return last_sequence_number


def set_last_seq(seqNum):
    global last_sequence_number
    with lock:
        last_sequence_number = seqNum


def parse_trade(content):
    return "TRADE"


def event_loop():
    while True:
        event = receive_json_response(ws)
        try:
            # if activity type at discord is message_create only then execute the program
            if event["t"] == 'MESSAGE_CREATE':
                print("Got message", event['d'])

                channel_id = event['d']['channel_id']
                msg_content = event['d']["content"]
                if channel_id in SUBSCRIBED_CHANNELS:
                    try:
                        trade = parse_trade(msg_content)
                        if trade:
                            print("New Order detected --> ", trade)
                    except Exception as e:
                        print(e)
                else:
                    pass
            else:
                pass
        except Exception as e:
            print(e)


if __name__ == '__main__':
    open_websocket()
    send_identify()
    event_loop()
