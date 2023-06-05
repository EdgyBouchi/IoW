import os.path
import subprocess
import json
import sys
import time

def ping_platform(host):
    command = ['ping', '-c', '1', host]
    return subprocess.call(command) == 0

def check_wifi_connectivity(retry_amount):
    for i in range(retry_amount):
        print("Connection attempt {}".format(i+1))
        #if not ping_platform("https://platform-test.edgise.com"):
        if not ping_platform("www.google.be"):
            print("no connection to internet.\n")
            print("retrying in 2 seconds.\n")
            time.sleep(2)
            continue
        print("internet is reachable.\n")
        return True
    return False

def connect_to_network(ssid,password):
    res = subprocess.Popen(['sudo', 'nmcli', 'dev', 'wifi', 'connect', ssid , 'password', password], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.wait() != 0:
        output, error = res.communicate()
        print(error)
        print("NMCLI Con not successfully activated.")
        return False
    else:
        # check if the wifi connection is up and the platform reachable
        print("NMCLI Con successfully actived.\n")
        return True

def start_main_script(main_script_path):
    print("starting main script")
    main_script = subprocess.Popen("sudo python3 {}".format(main_script_path), shell=True)
    if main_script.wait() != 0:
        print("main script failed.\n")
        output, error = main_script.communicate()
        print(output)
        print(error)
        return False
    return main_script

def start_captive_port_script(captive_portal_script_path):
    print("starting captive portal script")
    captive_portal_script = subprocess.Popen("sudo python3 {}".format(captive_portal_script_path), shell=True)
    if captive_portal_script.wait() != 0:
        print("captive portal failed.\n")
        output, error = captive_portal_script.communicate()
        print(output)
        print(error)
        return False

if __name__ == "__main__":
    print(os.getcwd())
    os.chdir("/home/pi/Documents/IoW")
    json_path = '/home/pi/Documents/IoW/utils/captive_portal/user_register.json'
    captive_portal_script_path = '/home/pi/Documents/IoW/utils/captive_portal.py'
    main_script_path = '/home/pi/Documents/IoW/main.py'

    while not os.path.exists(json_path):
        # debug this
        if not start_captive_port_script(captive_portal_script_path):
            continue

    # json with wifi data already exists
    print("wifi config json found")
    with open(json_path, 'r') as user_register_file:
        json_dict = json.load(user_register_file)
    ssid = json_dict["ssid"]
    password = json_dict["password"]
    if not connect_to_network(ssid, password) and not check_wifi_connectivity(5):
        print("No connecting to network or internet.\n")
        print("Retried 5 times\n")
        print("Not starting main script.\n")
        print("Deleting User config and restarting launcher script.\n")
        os.remove(json_path)
        os.execv(__file__, sys.argv)
    else:
        print("Starting Main script.\n")
        #Check if this will keep running when launcher script ends.
        start_main_script(main_script_path)







