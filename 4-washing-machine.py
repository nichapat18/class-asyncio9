import time
import random
import json
import asyncio
import aiomqtt
from enum import Enum

student_id = "6310301032"

# State 
S_OFF       = 'OFF'
S_READY     = 'READY'
S_FAULT     = 'FAULT'
S_FILLWATER = 'FILLWATER'
S_HEATWATER = 'HEATWATER'
S_WASH      = 'WASH'
S_RINSE     = 'RINSE'
S_SPIN      = 'SPIN'

# Function
S_DOORCLOSED            = 'DOORCLOSE'
S_FULLLEVELDETECTED     = 'FULLLEVELDETECTED'
S_TEMPERATUREREACHED    = 'TEMPERATUREREACHED'
S_FUNCTIONCOMPLETED     = 'FUNCTIONCOMPLETED'
S_TIMEOUT               = 'TIMEOUT'
S_MOTORFAILURE          = 'MOTORFAILURE'
S_OUTOFBALANCE          = 'OUTOFBALANCE'
S_FAULTCLEARED          = 'FAULTCLEARED'

async def publish_message(w, client, app, action, name, value):
    await asyncio.sleep(1)
    payload = {
                "action"    : "get",
                "project"   : student_id,
                "model"     : "model-01",
                "serial"    : w.SERIAL,
                "name"      : name,
                "value"     : value
            }
    print(f"{time.ctime()} - PUB topic: v1cdti/{app}/{action}/{student_id}/model-01/{w.SERIAL} payload: {name}:{value}")
    await client.publish(f"v1cdti/{app}/{action}/{student_id}/model-01/{w.SERIAL}"
                        , payload=json.dumps(payload))

async def fillwater(w, filltime=100):
    print(f"{time.ctime()} - [{w.SERIAL}] Waiting for fill water maxinum {filltime} seconds")
    await asyncio.sleep(filltime)

async def heatwater(w, filltime=100):
    print(f"{time.ctime()} - [{w.SERIAL}] Waiting for heat water maxinum {filltime} seconds")
    await asyncio.sleep(filltime)

async def wash(w, filltime=100):
    print(f"{time.ctime()} - [{w.SERIAL}] Waiting for wash maxinum {filltime} seconds")
    await asyncio.sleep(filltime)

async def rinse(w, filltime=100):
    print(f"{time.ctime()} - [{w.SERIAL}] Waiting for rinse maxinum {filltime} seconds")
    await asyncio.sleep(filltime)

async def spin(w, filltime=100):
    print(f"{time.ctime()} - [{w.SERIAL}] Waiting for spin maxinum {filltime} seconds")
    await asyncio.sleep(filltime)

class MachineStatus(Enum):
    pressure = round(random.uniform(2000,3000), 2)
    temperature = round(random.uniform(25.0,40.0), 2)

class MachineMaintStatus(Enum):
    filter = random.choice(["clear", "clogged"])
    noise = random.choice(["quiet", "noisy"])

class WashingMachine:
    def __init__(self, serial):
        self.SERIAL = serial
        self.STATE = 'OFF'
        self.Task = None
        self.event = asyncio.Event()

async def CoroWashingMachine(w, client):

    while True:
        if w.STATE == "OFF":
            print(f"{time.ctime()} - [{w.SERIAL}-{w.STATE}]")
            await w.event.wait()
            w.event.clear()
            continue

        if w.STATE == "FAULT":
            print(f"{time.ctime()} - [{w.SERIAL}-{w.STATE}]")
            await w.event.wait()
            w.event.clear()
            continue

        if w.STATE == "READY":
            print(f"{time.ctime()} - [{w.SERIAL}-{w.STATE}]")

            await publish_message(w, client, "app", "get", "STATUS", "READY")
            # door close
            
            await publish_message(w, client, "app", "get", "STATUS", "FILLWATER")
            w.STATE = "FILLWATER"

        if w.STATE == "FILLWATER":
            # fill water untill full level detected within 10 seconds if not full then timeout 
            w.Task = asyncio.create_task(fillwater(w))
            try:
                await asyncio.wait_for(w.Task, timeout=10.0)
            except asyncio.exceptions.TimeoutError:
                await publish_message(w, client, "app", "set", "STATUS", "FAULT")
                w.STATE = "FAULT"
                continue
            except asyncio.exceptions.CancelledError:
                if w.STATE == S_FULLLEVELDETECTED:
                    await publish_message(w, client, "app", "get", "STATUS", "HEATWATER")
                    w.STATE = "HEATWATER"
        if w.STATE == "HEATWATER":
            # heat water until temperature reach 30 celcius within 10 seconds if not reach 30 celcius then timeout
            w.Task = asyncio.create_task(heatwater(w))
            try:
                await asyncio.wait_for(w.Task, timeout=10.0)
            except asyncio.exceptions.TimeoutError:
                await publish_message(w, client, "app", "set", "STATUS", "FAULT")
                w.STATE = "FAULT"
                continue
            except asyncio.exceptions.CancelledError:
                if w.STATE == S_TEMPERATUREREACHED:
                    await publish_message(w, client, "app", "get", "STATUS", "WASH")
                    w.STATE = "WASH"
        if w.STATE == "WASH":
            # wash 10 seconds, if out of balance detected then fault
            w.Task = asyncio.create_task(wash(w))
            try:
                await asyncio.wait_for(w.Task, timeout=10.0)
            except asyncio.exceptions.TimeoutError:
                await publish_message(w, client, "app", "get", "STATUS", "RINSE")
                w.STATE = "RINSE"
            except asyncio.exceptions.CancelledError:
                if w.STATE == "OUTOFBALANCE":
                    await publish_message(w, client, "app", "set", "STATUS", "FAULT")
                    w.STATE = "FAULT"
                    continue
        if w.STATE == "RINSE":
            # rinse 10 seconds, if motor failure detect then fault
            w.Task = asyncio.create_task(rinse(w))
            try:
                await asyncio.wait_for(w.Task, timeout=10.0)
            except asyncio.exceptions.TimeoutError:
                await publish_message(w, client, "app", "get", "STATUS", "SPIN")
                w.STATE = "SPIN"
            except asyncio.exceptions.CancelledError:
                if w.STATE == "MOTORFAILURE":
                    await publish_message(w, client, "app", "set", "STATUS", "FAULT")
                    w.STATE = "FAULT"
                    continue
        if w.STATE == "SPIN":
            # spin 10 seconds, if motor failure detect then fault
            w.Task = asyncio.create_task(spin(w))
            try:
                await asyncio.wait_for(w.Task, timeout=10.0)
            except asyncio.exceptions.TimeoutError:
                await publish_message(w, client, "app", "get", "STATUS", "OFF")
                w.STATE = "OFF"
            except asyncio.exceptions.CancelledError:
                if w.STATE == "MOTORFAILURE":
                    await publish_message(w, client, "app", "set", "STATUS", "FAULT")
                    w.STATE = "FAULT"
                    continue

        # When washing is in FAULT state, wait until get FAULTCLEARED
            

async def listen(w, client):
    async with client.messages() as messages:
        print(f"{time.ctime()} - SUB topic: v1cdti/hw/set/{student_id}/model-01/{w.SERIAL}")
        await client.subscribe(f"v1cdti/hw/set/{student_id}/model-01/{w.SERIAL}")
        await client.subscribe(f"v1cdti/app/get/{student_id}/model-01/")
        async for message in messages:
            m_decode = json.loads(message.payload)
            if message.topic.matches(f"v1cdti/hw/set/{student_id}/model-01/{w.SERIAL}"):
                # set washing machine status
                print(f"{time.ctime()} - MQTT [{m_decode['serial']}]:{m_decode['name']} => {m_decode['value']}")
                if (m_decode['name']=="STATUS" and m_decode['value']=="FAULTCLEARED"):
                    w.STATE = "READY"
                    w.event.set()
                elif (m_decode['name']=="STATUS" and m_decode['value']=="READY" and w.STATE != "FAULT"):
                    w.STATE = "READY"
                    w.event.set()
                elif (m_decode['name']=="STATUS" and m_decode['value']=="FAULT"):
                    w.STATE = "FAULT"
                elif (m_decode['name']=="STATUS" and m_decode['value']=="OFF"):
                    w.STATE = "OFF"
                elif (w.Task is not None):
                    if (m_decode['name']=="STATUS" and m_decode['value']=="FULLLEVELDETECTED"):
                        w.STATE = "FULLLEVELDETECTED"
                        w.Task.cancel()
                    elif (m_decode['name']=="STATUS" and m_decode['value']=="TEMPERATUREREACHED"):
                        w.STATE = "TEMPERATUREREACHED"
                        w.Task.cancel()
                    elif (m_decode['name']=="STATUS" and m_decode['value']=="OUTOFBALANCE"):
                        w.STATE = "OUTOFBALANCE"
                        w.Task.cancel()
                    elif (m_decode['name']=="STATUS" and m_decode['value']=="MOTORFAILURE"):
                        w.STATE = "MOTORFAILURE"
                        w.Task.cancel()
                else:
                    print(f"{time.ctime()} - ERROR MQTT [{m_decode['serial']}]:{m_decode['name']} => {m_decode['value']}")

async def main():
    w = WashingMachine(serial='SN-001')
    async with aiomqtt.Client("broker.hivemq.com") as client:
        await asyncio.gather(listen(w, client),CoroWashingMachine(w, client))

asyncio.run(main())