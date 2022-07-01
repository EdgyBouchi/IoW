import os.path
import subprocess

if __name__ == "__main__":
    os.chdir("~/Documents/IoW/")
    json_path = 'utils/captive_portal/user_register.json'
    captive_portal_script_path = 'utils/captive_portal.py'
    main_script_path = 'main.py'
    if not os.path.exists(json_path):
        captive_portal_script = subprocess.Popen("sudo python3 {}".format(captive_portal_script_path))
        if captive_portal_script.wait() != 0:
            print("captive portal failed")
        else:
            print("starting main script")
            main_script = subprocess.Popen("echo {} | sudo python3 {}".format("ucllstudent", main_script_path))
    else:
        # json with wifi data already exists
        print("wifi config json found")
        print("starting main script")
        main_script = subprocess.Popen("echo {} | sudo python3 {}".format("ucllstudent", main_script_path))

