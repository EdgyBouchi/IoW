# IoW script to install all prerequisites
sudo systemctl enable ssh
sudo systemctl start ssh



cd ~
git clone https://github.com/Seeed-Studio/grove.py
cd grove.py
sudo pip3 install .

cd ~
git clone https://github.com/EdgyBouchi/IoW.git
cd IoW
pip install -r requirements.txt