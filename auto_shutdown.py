import subprocess
from time import localtime, strftime, sleep,time,strptime,mktime
import googleapiclient.discovery
from google.oauth2 import service_account
import sys


def check_connection():
    current_timestamp = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())
    print(current_timestamp)
    cmd = 'netstat -a'
    ns_output = subprocess.run(cmd,shell=True,capture_output=True,text=True)
    result = ns_output.stdout
    result_lines = result.split('\n')
    for line in result_lines:
        if '3389' in line and 'ESTABLISHED' in line:
            connected = True
            print('%s'%(line))
            break
    else:
        connected = False
    return connected

def perform_hibernate():
    cmd = 'shutdown /h'
    result = subprocess.run(cmd,shell=True)

def perform_shutdown(creds):
    project='winvms'
    zone='us-central1-a'
    credentials = service_account.Credentials.from_service_account_file(creds)
    instance='instance-1'
    compute = googleapiclient.discovery.build('compute', 'v1',credentials=credentials)

    # get info about nodes in project, as a way to test that credentials are working
    result = compute.instances().list(project=project, zone=zone).execute()
    print(result)

    # send shutdown command to gce
    result = compute.instances().stop(project=project,zone=zone,instance=instance).execute()
    sleep(120)

creds = sys.argv[1]
connected = True
threshold = 5*60 # num seconds the RDP session can be gone before we take action
shutdown_fallback_time = 5*60 # num seconds to wait for hibernate to work
current_time = time()
while True:
    last_connected = connected
    connected = check_connection()
    last_time = current_time
    current_time = time()
    if current_time > last_time + 60:
        # system likely suspended/hibernated; reset any disconnect time
        disconnect_time = max(disconnect_time, current_time)
    if last_connected == True and connected == False:
        # detect transition
        disconnect_time = current_time
    elif connected == True:
        disconnect_time = mktime(strptime('2030','%Y')) #set disconnect time way into the future
    elif connected == False:
        current_time = time()
        if current_time - disconnect_time > threshold + shutdown_fallback_time:
            perform_shutdown(creds)
        elif current_time - disconnect_time > threshold:
            perform_hibernate()
        else:
            print('shutting down in %d seconds'%(threshold-(current_time- disconnect_time)))

    sleep(10)
