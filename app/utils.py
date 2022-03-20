from cryptography.fernet import Fernet
import os

def getToken():
    key = bytes(os.getenv("KEY"), "utf-8")
    encrypted = bytes(os.getenv("SECRET_TELEGRAM"), "utf-8")
    return Fernet(key).decrypt(encrypted).decode()

import pendulum
import requests
import json
import yaml

def testServer(localhost, payload):
    URL = localhost + '/dailyUpdate'
    response = requests.post(URL, json=payload)
    print(response.json())

def loadData():
    try:
        with open('secrets.yaml', 'r') as stream:
            yamlData = yaml.safe_load(stream)
        return yamlData
    except Exception as e:
        print(e)
        return ''

def getAuth(response):
    token = response['data']['createTengahCCSSSWApplication']['token']
    applicationId = response['data']['createTengahCCSSSWApplication']['node']['id']
    return token, applicationId

def updateConfig(token, applicationId, headers, payload):
    headers['Authorization'] = f'Bearer {token}'
    payload['variables']['applicationId'] = applicationId
    return headers, payload

def formatResult(result: dict) -> dict:
    data = result['data']['tengahSSWConfigValues']['node']
    # d = {k[-1]: {kk: (f'${int(_)/100:.2f}' if kk != 'savings' else f'{int(_)/100:.2f}%') for kk,_ in v.items()} for k,v in data.items()}
    d = {int(k[-1]): {kk: (int(_)/100 if kk != 'savings' else int(_)/100) for kk,_ in v.items()} for k,v in data.items()}
    return d

def downloadResult() -> dict:
    if 'config.yaml' not in os.listdir():
        raise Exception('"config.yaml" not found, aborting...')

    with open('config.yaml', 'r') as stream:
        yamlData = yaml.safe_load(stream)
        URL = yamlData['url']
        REG_HEADERS, REG_PAYLOAD = yamlData['registration'].values()
        HEADERS, PAYLOAD = yamlData['download'].values()

    response = requests.post(URL, json=REG_PAYLOAD).json()
    HEADERS, PAYLOAD = updateConfig(*getAuth(response), HEADERS, PAYLOAD)
    NOW = pendulum.now(tz='Asia/Singapore')

    result = requests.post(URL, headers=HEADERS, json=PAYLOAD).json()

    formattedResult = {'time': ', '.join(NOW.to_day_datetime_string().split(', ')[1:]), **formatResult(result)}
    return formattedResult

# Manage subscribers (JSON)
def getUsers():
    with open('config.yaml', 'r') as stream:
        yamlData = yaml.safe_load(stream)
    
    userDb = yamlData['directory']['users']
    if os.path.exists(userDb):
        with open(userDb, 'r') as file:
            content = file.read()
            userList = content.split()
            return userList
    else:
        return []

def addUser(userId):
    # Mongo DB Commands
    print(f'{userId} added..')
    return

def removeUser(userId):
    # Mongo DB Commands
    print(f'{userId} removed..')
    return

if __name__ == '__main__':
    with open('config.yaml', 'r') as stream:
        yamlData = yaml.safe_load(stream)
        URL = yamlData['url']
        REG_HEADERS, REG_PAYLOAD = yamlData['registration'].values()
        HEADERS, PAYLOAD = yamlData['download'].values()

    response = requests.post(URL, json=REG_PAYLOAD).json()
    HEADERS, PAYLOAD = updateConfig(*getAuth(response), HEADERS, PAYLOAD)
    NOW = pendulum.now()

    result = requests.post(URL, headers=HEADERS, json=PAYLOAD).json()

    formattedResult = {'time': ', '.join(NOW.to_day_datetime_string().split(', ')[1:]), **formatResult(result)}
    print(formatResult(result))

    with open(f'data/result_{NOW.to_date_string()}.json', 'w') as file:
        file.write(json.dumps(formattedResult, indent=4))
