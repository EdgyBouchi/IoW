# README #
# installation/patching

excecute git clone -b test https://github.com/RobrechtUlenaersPXL/IoW.git 

* in the ./documents/IoW directory execute ./IowPatchscript.sh
* should install all necessary files
* reboot after script => hotspot is setup upon reboot
* after filling in network info reboot again to startup service
* crontab job should check for new code every day at 02am

## how to acces terminal
* crontab starts a tmux session, to acces it run the following command:
* tmux attach-session -t iow
* to leave use keys ctrl+b then D to detach
* ctrl+b then X to delete session

### What is this repository for? ###

* Quick summary
* Version
* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)

### How do I get set up? ###

* Summary of set up
* Configuration
* Dependencies
* Database configuration
* How to run tests
* Deployment instructions

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact
