import os.path
import subprocess
import json
import time


def ping_platform(host):
    command = ['ping', '-c', '1', host]
    return subprocess.call(command) == 0

def check_wifi_connectivity(retry_amount):
    for i in range(retry_amount):
        print("Connection attempt {}".format(i+1))
        if not ping_platform("https://platform-test.edgise.com/api/"):
            print("no connection to platform.\n")
            print("retrying in 2 seconds.\n")
            continue
        print("Platform is reachable.\n")
        return True
    return False



if __name__ == "__main__":
    print(os.getcwd())
    os.chdir("/home/pi/Documents/IoW")
    json_path = '/home/pi/Documents/IoW/utils/captive_portal/user_register.json'
    captive_portal_script_path = '/home/pi/Documents/IoW/utils/captive_portal.py'
    main_script_path = '/home/pi/Documents/IoW/main.py'


    while not os.path.exists(json_path):
        captive_portal_script = subprocess.Popen("sudo python3 {}".format(captive_portal_script_path), shell=True)
        if captive_portal_script.wait() != 0:
            print("captive portal failed.\n")
            output, error = captive_portal_script.communicate()
            print(output)
            print(error)
            continue

    # json with wifi data already exists
    print("wifi config json found")
    with open(json_path,'r') as user_register_file:
        json_dict = json.load(user_register_file)

    # use user_registration.json to connect to network ?
    ssid = json_dict["ssid"]
    password = json_dict["password"]

    res = subprocess.Popen('sudo nmcli dev wifi connect {ssid} password {password}', stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, shell=True)

    if res.wait() != 0:
        output, error = res.communicate()
        print(error)
        print("NMCLI Con not successfully activated.\n")
    else:
        # check if the wifi connection is up and the platform reachable
        print("NMCLI Con successfully actived.\n")
        if check_wifi_connectivity(5):
            print("starting main script")
            main_script = subprocess.Popen("sudo python3 {}".format(main_script_path), shell=True)


