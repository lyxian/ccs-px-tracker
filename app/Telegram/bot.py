import pendulum
import requests
import telebot
import re

from utils import getToken, addUser, removeUser, getPinnedMessageId, updatePinnedMessageId

TRACKED_NUM = ['1', '2', '3', '4', '5']

# TODO
# + clean code
# + test server response
# + manage subscribers 
# + enable notif (edit Vs. delete & send)
# - condense YEAR then MONTH
# - bugfix: duplicate addUser
# - bugfix: duplicate sendMsg

def createBot():
    TOKEN = getToken()

    bot = telebot.TeleBot(token=TOKEN)

    @bot.message_handler(commands=["start"])
    def _start(message):
        text = "Welcome to CCS-Price-Tracker-Bot! ☺ Here are the list of commands to get you started: \n/join - Subscribe to daily updates of CCS prices\n/quit - Un-subscribe from daily updates"
        bot.send_message(message.chat.id, text)
        pass

    @bot.message_handler(commands=["join"])
    def _join(message):
        if addUser(message.chat.username, message.chat.id):
            unpinChat(message.chat.id)
            text = "You have subscribed to ccs-px-tracker! You will be receiving daily updates on cost of CCS at 11pm SGT! ☺"
            bot.send_message(message.chat.id, text)
            pass
        else:
            pass

    @bot.message_handler(commands=["quit"])
    def _quit(message):
        if removeUser(message.chat.id):
            unpinChat(message.chat.id)
            text = "You have UN-subscribed from ccs-px-tracker!"
            bot.send_message(message.chat.id, text)
            pass
        else:
            pass

    @bot.message_handler(func= lambda message: True)
    def _reply(message):
        pass

    return bot

def getMessage(data):
    STARTING_TEXT = '<b>CCS-Price-Tracker</b>\n'
    ENDING_TEXT = '<i>Updated on</i>: {}'

    def getNumbers(d, num):
        keys = ['conventional', 'ccs']
        return [d[num][_] for _ in keys]
    
    currentTime = data['time']
    currentDate = re.search(r'(.*20\d\d) .*', currentTime).group(1) 

    TEXT = STARTING_TEXT
    for i in TRACKED_NUM:
        conventional, ccs = map(int, getNumbers(data, i))
        TEXT += f'''<u>Conventional-{i}</u>
<b>${conventional}</b> @ {currentDate} - Present
<u>CCS-{i}</u>
<b>${ccs}</b> @ {currentDate} - Present
<u>Latest Savings-{i}</u>
<b>${conventional-ccs}</b> ({100-100*ccs/conventional:.2f}%)

'''

    return TEXT + ENDING_TEXT.format(currentTime)

def formatMessage(splitText):
    # Bold/Underline first , Underline heading , Bold cost , Italic last
    for _ in range(len(splitText)):
        if 'Tracker' in splitText[_]:
            splitText[_] = re.sub('(CCS-Price-Tracker)', r'<b><u>\1</u></b>', splitText[_])
        elif re.search(r'Conventional-\d|CCS-\d|Latest Savings-\d', splitText[_]):
            splitText[_] = re.sub(r'(Conventional-\d|CCS-\d|Latest Savings-\d)', r'<u>\1</u>', splitText[_])
        elif re.search(r'\$\d+', splitText[_]):
            splitText[_] = re.sub(r'(\$\d+)', r'<b>\1</b>', splitText[_])
        elif 'Updated on' in splitText[_]:
            splitText[_] = re.sub(r'(Updated on.*)', r'<i>\1</i>', splitText[_])
    return '\n'.join(splitText)

# TODO
# - how to migrate existing users
CHECK_TELE = False
def dailyUpdate(chatId, data):
    isChanged = False
    # Check for Pinned Message
    if CHECK_TELE:
        method = 'getChat'
        params = {
            'chat_id': chatId,
        }
        chat = callTelegramAPI(method, params).json()
    else:
        result = getPinnedMessageId(chatId)
        if result: # GET message + messageId
            chat = {
                'result': {
                    'pinned_message': {
                        'text': result['pinnedText'],
                        'message_id': result['pinnedMessageId']
                    }
                }
            }
        else: # Init empty dict
            chat = {
                'result': {}
            }
    if 'pinned_message' in chat['result'].keys():
        message = chat['result']['pinned_message']['text']
        messageId = chat['result']['pinned_message']['message_id']

        lines = message.split('\n')
        for num in TRACKED_NUM:
            row_conv = lines.index(f'CCS-{num}') - 1
            row_ccs = lines.index(f'Latest Savings-{num}') - 1
            row_savings = lines.index(f'Latest Savings-{num}') + 1
            row_update = len(lines) - 1

            prev_conventional = int(re.search(r'^\$(\d+) .*', message.split('\n')[row_conv]).group(1))
            prev_ccs = int(re.search(r'^\$(\d+) .*', message.split('\n')[row_ccs]).group(1))

            currentDate = re.search(r'(.*20\d\d) .*', data['time']).group(1)
            prevDate = pendulum.from_format(currentDate, 'MMM DD, YYYY').subtract(days=1).format('MMM DD, YYYY')
            curr_conventional, curr_ccs = map(int, [data[num][_] for _ in ['conventional', 'ccs']])

            # Check CONVENTIONAL
            if prev_conventional == curr_conventional:
                conv_lines = lines[row_conv]
            else:
                new_conv = f'\n${curr_conventional} @ {currentDate} - Present'
                conv_lines = re.sub('Present', prevDate, lines[row_conv]) + new_conv
                lines[row_savings] = f'${curr_conventional-curr_ccs} ({100-100*curr_ccs/curr_conventional:.2f}%)'
                isChanged = True

            # Check CCS
            if prev_ccs == curr_ccs:
                ccs_lines = lines[row_ccs]
            else:
                new_ccs = f'\n${curr_ccs} @ {currentDate} - Present'
                ccs_lines = re.sub('Present', prevDate, lines[row_ccs]) + new_ccs
                lines[row_savings] = f'${curr_conventional-curr_ccs} ({100-100*curr_ccs/curr_conventional:.2f}%)'
                isChanged = True

            # Format Message
            lines[row_conv] = conv_lines
            lines[row_ccs] = ccs_lines
            lines[row_update] = f'Updated on: {data["time"]}'

        message = formatMessage(lines)
        
        if isChanged: 
            # Delete Message in Tele
            params = {
                'chat_id': chatId,
                'message_id': messageId,
            }
            method = 'deleteMessage'
            _ = callTelegramAPI(method, params)

            # Send Message in Tele
            method = 'sendMessage'
            params = {
                'chat_id': chatId,
                'parse_mode': 'HTML',
                'text': message
            }
            response = callTelegramAPI(method, params)
        else:
            # Edit Message in Tele (No Alert)
            method = 'editMessageText'
            params = {
                'chat_id': chatId,
                'message_id': messageId,
                'parse_mode': 'HTML',
                'text': message
            }
            # Bad Response if same text
            response = callTelegramAPI(method, params)
    else:
        # Format Message
        message = getMessage(data)

        # Send Message in Tele
        method = 'sendMessage'
        params = {
            'chat_id': chatId,
            'parse_mode': 'HTML',
            'text': message
        }
        response = callTelegramAPI(method, params)

    # Update DB
    messageId = response.json()['result']['message_id']
    updatePinnedMessageId(chatId, messageId, re.sub(r'<.*?>', '', message))

def callTelegramAPI(method, params):
    url = 'https://api.telegram.org/bot{}/{}'.format(getToken(), method)
    response = requests.post(url=url, params=params)
    # print(response.json())
    return response

# MISC FUNCTION

def pinMessage(chatId, messageId, pin):
    if pin:
        method = 'pinChatMessage'
    else:
        method = 'unpinChatMessage'
    url = 'https://api.telegram.org/bot{}/{}'.format(getToken(), method)

    params = {
        'chat_id': chatId,
        'message_id': messageId,
        # 'disable_notification': False
    }
    response = requests.post(url=url, params=params)
    print(response.json())

def unpinChat(chatId):
    method = 'getChat'
    url = 'https://api.telegram.org/bot{}/{}'.format(getToken(), method)

    params = {
        'chat_id': chatId,
    }
    
    responseJson = requests.post(url=url, params=params).json()
    if 'pinned_message' in responseJson['result'].keys():
        messageId = requests.post(url=url, params=params).json()['result']['pinned_message']['message_id']
    
        method = 'unpinChatMessage'
        url = 'https://api.telegram.org/bot{}/{}'.format(getToken(), method)

        params = {
            'chat_id': chatId,
            'message_id': messageId,
            # 'disable_notification': False
        }
        
        response = requests.post(url=url, params=params)
        print(response.json())
    
if __name__ == "__main__":
    bot = createBot()