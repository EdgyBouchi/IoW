import json

from flask import Flask, request, redirect, render_template
import os
import subprocess
import time
import random
import getmac

app = Flask(__name__)

ssid_list = []


def get_ssid_list():
    ssids_list = []
    # Get the list of SSID's available
    ssids = subprocess.run(['nmcli', '-f', 'SSID', 'device', 'wifi'], stdout=subprocess.PIPE)
    ssids_str = ssids.stdout.decode('utf-8')
    list_ssids_string = ssids_str.split('\n')
    for ssid in list_ssids_string:
        ssids_list.append(ssid.strip())

    ssids_list = ssids_list[1:len(ssids_list) - 2]
    ssids_list.append("SSID not listed")

    return ssids_list


@app.route("/captive_portal_step_form", methods=['GET', 'POST'])
def index():
    print(request.method)
    if request.method == 'POST':
        # if request.form.get('btn_value') == 'Send':
        # pass
        ssid = request.form['ssid']
        if ssid == "SSID not listed":
            ssid = request.form['other_ssid']
            print(f"other SSID selected : {ssid}")
        password = request.form['password']
        os.system(f"nmcli con delete telly_con")
        os.system(f"nmcli c add type wifi con-name telly_con ifname wlan0 ssid '{ssid}'")
        os.system(f"nmcli c modify telly_con wifi-sec.key-mgmt wpa-psk wifi-sec.psk '{password}'")

        try:
            output = subprocess.check_output(["nmcli", "con", "up", "telly_con"])
            print("SUCCESS SUCCESS SUCCESS")

            with open('user_register.json', 'w') as f:
                json.dump(request.form, f)
            return render_template('user_registration_saved.html')

            func = request.environ.get('werkzeug.server.shutdown')
            if func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
            func()

            # quit_app()

        except Exception as e:
            print(f"FAILED FAILED FAILED ...  Exception : {e}")
            os.system(f"nmcli con up hotspot")

    return render_template("captive_portal_step_form.html", data=ssid_list)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return redirect("http://10.42.0.1:5000")


@app.route('/ison')
def ison():
    return "hello"


# @app.route('save_json', methods='POST')
# def save_json():
#     # if request.method == 'POST':
#     with open('user_register.json', 'w') as f:
#         json.dump(request.form, f)
#     return render_template('your_template.html')


@app.route('/retry_telly_con')
def retry_telly_con():
    try:
        os.system('nmcli con down hotspot')
        time.sleep(0.5)
        os.system('nmcli dev wifi rescan')
        time.sleep(0.5)
        #output = subprocess.check_output(["nmcli", "con", "up", "telly_con"])
        print("telly_con worked, quitting captive portal")

        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

        # quit_app()

    except Exception as e:
        print(f"telly_con failed with : {e}")
        os.system('nmcli con up hotspot')

    return "success"


# @app.route('/quit')
# def quit_app():
#     func = request.environ.get('werkzeug.server.shutdown')
#     if func is None:
#         raise RuntimeError('Not running with the Werkzeug Server')
#     func()


if __name__ == '__main__':
    selected_ssid = ""
    selected_psk = ""

    time.sleep(0.5)

    # Get the list of SSID's available
    # ssid_list = get_ssid_list()
    ssid_list = ["test"]

    c = 0
    while len(ssid_list) < 3 and c < 5:
       c += 1
       print("didn't find any SSID, trying again")
    # os.system("nmcli con down hotspot")
    #  os.system("nmcli con down telly_con")
    #   ssid_list = get_ssid_list()

    # print(f"found {len(ssid_list)} SSID's")
    hotspot_interface = "wlan0"
    hotspot_conn_name = "iow-con"
    hotspot_ssid = "IoW_Device"
    hotspot_password = "iow"
  #  os.system("nmcli con down {}".format(hotspot_conn_name))
    time.sleep(0.5)
   # os.system("nmcli connection delete {}".format(hotspot_conn_name))
    os.system("nmcli connection add type wifi ifname {} con-name {} autoconnect yes ssid {} mode ap".format(hotspot_interface, hotspot_conn_name,hotspot_ssid))
    os.system("nmcli connection modify {} 802-11-wireless.mode ap 802-11-wireless-security.key-mgmt wpa-psk  ipv4.method shared 802-11-wireless-security.psk {}".format(hotspot_conn_name, hotspot_password))
    #os.system("nmcli connection modify {} wifi-sec.key-mgmt wpa-psk".format(hotspot_conn_name))
    #os.system("nmcli con modify {} wifi-sec.psk {}".format(hotspot_conn_name, hotspot_password))
    os.system("nmcli con up {}".format(hotspot_conn_name))
    #os.system("nmcli connection show {}".format(hotspot_conn_name))

    os.system("nmcli connection add type wifi ifname {} con-name {} autoconnect yes ssid {}")
    app.run(host='0.0.0.0', port=8000)
