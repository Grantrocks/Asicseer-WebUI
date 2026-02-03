import json
import datetime
from flask import Flask,render_template
import os
import requests

coindeskAPIKEY="COINDESK API KEY"
apiProvider="https://data-api.coindesk.com/index/cc/v1/latest/tick?market=cadli&instruments=BCH-USD&apply_mapping=true&api_key="+coindeskAPIKEY
bitaxeAPI="http://192.168.86.28//api/system/info" #PLEASE CHANGE THE IP ADDRESS TO YOUR BITAXE IP
app = Flask(__name__)
logPath="/home/USER/asicseer/logs/" #PLEASE CHANGE THIS DIRECTORY PATH TO YOUR ASICSEER LOGS PATH

lastApiCheck=0
bchValue=0.0
def format_difficulty(difficulty: float) -> str:
    """
    Convert a difficulty float into a human-readable string
    with SI units (M, G, T, P, E, Z).
    """
    units = ["", "K", "M", "G", "T", "P", "E", "Z"]
    # Start at base unit
    idx = 0
    value = difficulty

    # Scale down until value < 1000 or we run out of units
    while value >= 1000 and idx < len(units) - 1:
        value /= 1000.0
        idx += 1

    # Format with 2 decimal places
    return f"{value:.2f} {units[idx]}"

def seconds_to_days_arithmetic(seconds):
    """Converts a given number of seconds to days using basic arithmetic."""
    seconds_in_a_day = 24 * 60 * 60  # 1440 minutes in a day
    days = seconds / seconds_in_a_day
    return round(days,2)
def getNetworkStats():
    res=requests.get(bitaxeAPI)
    data=res.json()
    return data
def getApiValue(blockReward):
    spacing=3600
    global lastApiCheck
    global bchValue
    print(datetime.datetime.now().timestamp()-lastApiCheck)
    print(datetime.datetime.now().timestamp()-lastApiCheck>spacing)
    if datetime.datetime.now().timestamp()-lastApiCheck>spacing:
        response = requests.get(apiProvider)
        data = response.json()
        bchValue = data["Data"]["BCH-USD"]["VALUE"]
        lastApiCheck=datetime.datetime.now().timestamp()
        print("API Updated")
    return round(blockReward*bchValue,2)


@app.route('/')
def home():
    poolStatus=open(f'{logPath}pool/pool.status', 'r').readlines()
    poolStatusJSON=[]

    for line in poolStatus:
        poolStatusJSON.append(json.loads(line))

    for jsonObj in poolStatusJSON:
        keys=jsonObj.keys()
        for key in keys:
            if key=='runtime':
                uptime=seconds_to_days_arithmetic(jsonObj[key])
            if key=='lastupdate':
                lastUpdate=datetime.datetime.fromtimestamp(jsonObj[key]).strftime('%Y-%m-%d %H:%M:%S')
            if key=='Users':
                users=jsonObj[key]
            if key=='Workers':
                workers=jsonObj[key]
            if key=='Idle':
                idleWorkers=jsonObj[key]
            if key=='Disconnected':
                disconnectedWorkers=jsonObj[key]
            if key=='hashrate1m':
                hashrate1M=jsonObj[key]
            if key=='hashrate5m':
                hashrate5M=jsonObj[key]
            if key=='hashrate15m':
                hashrate15M=jsonObj[key]
            if key=='hashrate1hr':
                hashrate1Hr=jsonObj[key]
            if key=='hashrate6hr':
                hashrate6Hr=jsonObj[key]
            if key=='hashrate1d':
                hashrate24Hr=jsonObj[key]
            if key=='hashrate7d':
                hashrate7Day=jsonObj[key]
            if key=='SPS1h':
                sharespersecond=jsonObj[key]
            if key=='reward':
                blockReward=jsonObj[key]
    activeWorkers=open(f'{logPath}pool/pool.miners', 'r').readlines()
    activeWorkersJSON=[]

    for line in activeWorkers:
        line=line.strip("bitcoincash:")
        address=""
        for c in line:
            if c==":":
                break
            address+=c
        line=line.strip(address+":")
        activeWorkersJSON.append(json.loads('{"'+address+'": '+line+"}"))
    formattedWorkerJson=[]
    for worker in activeWorkersJSON:
        for address in worker.keys():
            worker[address]['lastshare']=datetime.datetime.fromtimestamp(worker[address]['lastshare']).strftime('%Y-%m-%d %H:%M:%S')
            worker[address]['bestshare']=format_difficulty(worker[address]['bestshare'])
            worker[address]['bestshare_alltime']=format_difficulty(worker[address]['bestshare_alltime'])            
        formattedWorkerJson.append(worker)
    workerDevices=[]
    fileList=[f for f in os.listdir(f'{logPath}users') if os.path.isfile(os.path.join(f'{logPath}users', f))]
    for user in fileList:
        f=open(f'{logPath}users/{user}',"r")
        data=json.load(f)
        for slaveWorker in data['worker']:
                name=slaveWorker['workername'].split(".")
                if len(name)==2:
                    slaveWorker['workername']=name[1]
                else:
                    name=slaveWorker['workername'].strip("bitcoincash:")
                slaveWorker['bestshare']=format_difficulty(slaveWorker['bestshare'])
                slaveWorker['lastshare']=datetime.datetime.fromtimestamp(slaveWorker['lastshare']).strftime('%Y-%m-%d %H:%M:%S')
                workerDevices.append(slaveWorker)
    print(workerDevices)
    bitaxeData=getNetworkStats()
    
    return render_template('index.html', users=users, lastUpdate=lastUpdate, uptime=uptime, workers=workers, idleWorkers=idleWorkers, disconnectedWorkers=disconnectedWorkers,
    hashrate7d=hashrate7Day,workerDevices=workerDevices, hashrate1hr=hashrate1Hr, sharespersecond=sharespersecond, blockReward=blockReward,workerJson=formattedWorkerJson,blocksFound=len(os.listdir(f'{logPath}pool/blocks/')),bchRewardValue=getApiValue(blockReward),blockHeight=bitaxeData['blockHeight'],scriptSig=bitaxeData['scriptsig'],networkDiff=format_difficulty(float(bitaxeData['networkDifficulty'])))


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080)
