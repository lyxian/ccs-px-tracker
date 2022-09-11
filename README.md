# ccs-tracker

## TO-DO

- manage subscribers (v2)
- provide alert (v2)
- mongoDB integration (v3)
- update telebot reactions + more UI-friendly (v3)
- provide logs + optimized message

## Branches

- _master_
  - v1b
  - v2
- scheduler (for testing)
- v1b (heroku-deploy ready)
  - no `secrets.yaml`
  - set timezone
  - fixed userIds
  - check password
- v2
  - manage subscribers
  - provide alert (edit if no change = no alert, else new)
- v3
  - mongoDB integration
  - update telebot reactions (start/join/quit)
- v4
  - push data to mongoDB then compare

## Extra

- integrate encryptionStore

## Bugfix

- duplicate addUser
- duplicate tele messages
- ccs-api error (unit taken)
  - alert if error
- missing pinnedMessage

##Packages (list required packages & run .scripts/python-pip.sh)
flask
pyyaml
pymongo
pendulum
dnspython
apscheduler
cryptography
PyTelegramBotAPI

##Packages
