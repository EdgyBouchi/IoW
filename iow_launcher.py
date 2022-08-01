import os.path
import subprocess

if __name__ == "__main__":
    print(os.getcwd())
    os.chdir("/home/pi/Documents/IoW")
    json_path = '/home/pi/Documents/IoW/utils/captive_portal/user_register.json'
    captive_portal_script_path = '/home/pi/Documents/IoW/utils/captive_portal.py'
    main_script_path = '/home/pi/Documents/IoW/main.py'
    if not os.path.exists(json_path):
        captive_portal_script = subprocess.Popen("sudo python3 {}".format(captive_portal_script_path), shell=True)
        if captive_portal_script.wait() != 0:
            print("captive portal failed")
            os.remove(json_path)
        else:
            print("starting main script")
            main_script = subprocess.Popen("echo {} | sudo python3 {}".format("ucllstudent", main_script_path),shell=True)
    else:
        # json with wifi data already exists
        print("wifi config json found")
        print("starting main script")
        main_script = subprocess.Popen("echo {} | sudo python3 {}".format("ucllstudent", main_script_path), shell=True)

