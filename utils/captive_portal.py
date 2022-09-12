import json
import sys

from flask import Flask, request, redirect, render_template, url_for
import os
import subprocess
import time

app = Flask(__name__, template_folder='templates')

ssid_list = []


# popen DOES NOT PARSE WHITESPACES IN NETWORK SSID -> NEEDS TO BE FIXED
def get_ssid_list():
    # Get the list of SSID's available
    ssids = subprocess.run(['nmcli', '-f', 'SSID', 'device', 'wifi'], stdout=subprocess.PIPE)
    ssids_str = ssids.stdout.decode('utf-8')
    ssids_string_list = ssids_str.split('\n')
    ssids = set([ssid.strip() for ssid in ssids_string_list])
    ssids = list(filter(lambda ssid: ssid != '__', ssids))
    print("SSIDS STRIP: {}".format(ssids))
    return ssids


@app.route("/portal", methods=['GET', 'POST'])
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
        if not(ssid.startswith('"')):
            ssid = '"' + ssid + '"'
        if not(password.startswith('"')):
            password = '"' + password + '"'    

        with open('/home/pi/Documents/IoW/utils/captive_portal/user_register.json', 'w') as f:
            json.dump(request.form, f)

        os.system("sudo nmcli connection down iow-con")
        time.sleep(10)

        res = subprocess.Popen(f'sudo nmcli dev wifi connect {ssid} password {password}', stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
        # Wait for the process end and print error in case of failure

        if res.wait() != 0:
            output, error = res.communicate()
            print(error)
            print("connection unsuccessful")
            os.remove('/home/pi/Documents/IoW/utils/captive_portal/user_register.json')
            os.system("sudo nmcli connection up iow-con")
            time.sleep(10)
            sys.exit()
        else:
            print("connection success")
            time.sleep(10)
            sys.exit()

    return render_template("captive_portal_step_form.html", data=ssid_list)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return redirect("http://10.42.0.1:80/portal")

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    sys.exit()


@app.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'


if __name__ == '__main__':
    selected_ssid = ""
    selected_psk = ""

    hotspot_interface = "wlan0"
    hotspot_conn_name = "iow-con"
    hotspot_ssid = "IoW_Device"
    hotspot_password = "iowiowiow"
    os.system("nmcli connection down {}".format(hotspot_conn_name))
    time.sleep(0.5)
    os.system("nmcli connection delete {}".format(hotspot_conn_name))

    os.system(
        "nmcli connection add type wifi ifname {} con-name {} autoconnect yes ssid {} mode ap".format(hotspot_interface,
                                                                                                      hotspot_conn_name,
                                                                                                      hotspot_ssid))
    os.system(
        "nmcli connection modify {} 802-11-wireless.mode ap 802-11-wireless-security.key-mgmt wpa-psk  ipv4.method shared 802-11-wireless-security.psk {}".format(
            hotspot_conn_name, hotspot_password))
    os.system("nmcli connection up {}".format(hotspot_conn_name))

    app.run(host='0.0.0.0', port=80)
