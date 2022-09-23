from cryptography.fernet import Fernet
import requests
import os

def retrieveKey():
    required = ['APP_NAME', 'APP_PASS', 'STORE_PASS', 'STORE_URL']
    if all(param in os.environ for param in required):
        payload = {
            'url': '{}/{}'.format(os.getenv('STORE_URL'), 'getPass'),
            'payload': {
                'password': int(os.getenv('STORE_PASS')),
                'app': os.getenv('APP_NAME'),
                'key': int(os.getenv('APP_PASS'))
            }
        }
        response = requests.post(payload['url'], json=payload['payload']).json()
        if response.get('status') == 'OK':
            return response.get('KEY')
        else:
            raise Exception('Bad response from KEY_STORE, please try again ..')
    else:
        raise Exception('No key store found, please check config ..')

def getToken():
    key = bytes(retrieveKey(), 'utf-8')
    encrypted = bytes(os.getenv('SECRET_TELEGRAM'), 'utf-8')
    return Fernet(key).decrypt(encrypted).decode()

import pendulum
import json
import yaml

def testServer(localhost, payload):
    URL = localhost + '/dailyUpdate'
    response = requests.post(URL, json=payload)
    try:
        print(response.json())
    except:
        print(response.content)

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

import pymongo

# Manage subscribers
class MongoDb:
    def __init__(self, configData):
        self.collection = self.connect(configData)

    def connect(self, configData):
        configVars = loadData()
        key = bytes(os.getenv("KEY"), "utf-8")
        password = Fernet(key).decrypt(bytes(os.getenv("SECRET_MONGODB"), "utf-8")).decode()
        databaseConfig = configData['application']['database']
        databaseConfig = {
            'host': os.getenv('HOST') if not configVars else configVars['application']['database']['host'],
            'password': password, **databaseConfig}
        connection = pymongo.MongoClient(**databaseConfig)
        database, collection = configData['query'].values()
        return connection[database][collection]

    def read(self):
        return [_['chatId'] for _ in self.collection.find()]

    def has(self, chatId):
        return chatId in self.read()

    def insert(self, chatId, name):
        data = {'chatId': chatId, 'name': name}
        try:
            response = self.collection.insert_one(data)
            print(f'chatId-{chatId} added successfully..')
            # print(response.inserted_id, data)
            # return response
        except pymongo.errors.DuplicateKeyError:
            print('chatId exists, aborting..')
        return

    def delete(self, chatId):
        query = {'chatId': chatId}
        result = list(self.collection.find(query))
        print(result)
        if result:
            if len(result) == 1:
                response = self.collection.delete_one(query)
                print(f'chatId-{chatId} deleted successfully..')
                # return response
            else:
                print(f'Duplicate chatId-{chatId} found, aborting..')
        else:
            print('chatId not found..')
        return

    def update(self, chatId, payload):
        try:
            self.collection.find_one_and_update(
                {'chatId': chatId},
                payload
            )
            print(f'\'pinnedMessageId\', \'pinnedText\' set successfully for chatId-{chatId}..')
        except Exception as e:
            print(f'Error when updating document ({chatId}): {e}')
        return

def getUsers():
    # Mongo DB Commands
    with open('config.yaml', 'r') as stream:
        try:
            configData = yaml.safe_load(stream)
        except yaml.YAMLError as ERROR:
            print(ERROR)
    
    obj = MongoDb(configData)
    return obj.read()

def addUser(name, chatId):
    # Mongo DB Commands
    with open('config.yaml', 'r') as stream:
        try:
            configData = yaml.safe_load(stream)
        except yaml.YAMLError as ERROR:
            print(ERROR)
    
    obj = MongoDb(configData)
    if not obj.has(chatId):
        obj.insert(chatId, name)
        # print(f'{userId} added..')
        return True
    else:
        return False

def removeUser(chatId):
    # Mongo DB Commands
    with open('config.yaml', 'r') as stream:
        try:
            configData = yaml.safe_load(stream)
        except yaml.YAMLError as ERROR:
            print(ERROR)

    obj = MongoDb(configData)
    if obj.has(chatId):
        obj.delete(chatId)
        # print(f'{userId} removed..')
        return True
    else:
        return False

def updateMessageId(chatId, messageId):
    # Mongo DB Commands
    with open('config.yaml', 'r') as stream:
        try:
            configData = yaml.safe_load(stream)
        except yaml.YAMLError as ERROR:
            print(ERROR)

    obj = MongoDb(configData)
    if obj.has(chatId):
        obj.update(chatId, {'$set': {'messageId': messageId}})
        return True
    else:
        return False

def getPinnedMessageId(chatId):
    # Mongo DB Commands
    with open('config.yaml', 'r') as stream:
        try:
            configData = yaml.safe_load(stream)
        except yaml.YAMLError as ERROR:
            print(ERROR)

    obj = MongoDb(configData)
    result = obj.collection.find_one({'chatId': chatId})
    if result:
        if 'pinnedMessageId' in result.keys():
            return result
        else:
            return None
    else:
        return None

def updatePinnedMessageId(chatId, messageId, text):
    # Mongo DB Commands
    with open('config.yaml', 'r') as stream:
        try:
            configData = yaml.safe_load(stream)
        except yaml.YAMLError as ERROR:
            print(ERROR)

    obj = MongoDb(configData)
    if obj.has(chatId):
        obj.update(chatId, {'$set': {'pinnedMessageId': messageId, 'pinnedText': text}})
        return True
    else:
        return False

# with open('config.yaml', 'r') as stream:
#     configData = yaml.safe_load(stream)
# obj = MongoDb(configData)

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
