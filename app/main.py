from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
import traceback
import requests
import telebot
import os

from Telegram.bot import createBot, dailyUpdate
from utils import getUsers, removeUser, testServer, loadData, downloadResult, addUser, postError

configVars = loadData()

DEBUG_MODE = True #eval(os.getenv("DEBUG_MODE"))
SAVE_RESPONSE = False

app = Flask(__name__)

if __name__ == "__main__":
    bot = createBot()

    @app.route("/stop")
    def stop():
        shutdown_hook = request.environ.get("werkzeug.server.shutdown")
        try:
            shutdown_hook()
            print("--End--")
        except:
            pass

    @app.route("/" + bot.token, methods=["POST"])
    def getMessage():
        try:
            bot.process_new_updates(
                [telebot.types.Update.de_json(request.stream.read().decode("utf-8"))]
            )
            return "!", 200
        except Exception as e:
            print(e)
            return "?", 500

    @app.route("/", methods=["GET", "POST"])
    def webhook():
        if request.method == "GET":
            bot.remove_webhook()
            print("Setting webhook...")
            try:
                bot.set_webhook(url=os.getenv("PUBLIC_URL") + bot.token)
                return "Webhook set!", 200
            except:
                return "Webhook not set...Try again...", 400
        elif request.method == "POST":
            print("Invalid Method (webhook)...")
            return "!", 400

    @app.route("/getIP", methods=["GET"])
    def _getIP():
        if request.method == "GET":
            URL = 'https://api.ipify.org?format=json'
            return requests.get(URL).json(), 200

    @app.route('/dailyUpdate', methods=['POST'])
    def _dailyUpdate():
        if request.method == 'POST':
            password = os.getenv('PASSWORD') if not configVars else configVars['payload']['password']
            if 'password' in request.json and request.json['password'] == int(password):
                try:
                    # Download result
                    result = downloadResult()
                    users = getUsers() if not configVars else configVars['userIds']

                    # Update subscribers
                    for user in users:
                        print(user, result)
                        dailyUpdate(user, result)
                    return {'status': 'OK'}, 201
                except Exception:
                    error = traceback.format_exc().strip()
                    try:
                        response = postError(error)
                        if response:
                            print(response)
                            return {'status': 'NOT_OK', 'ERROR': 'Error posted successfully!'}, 503
                        else:
                            # INTERNAL SERVER ERROR
                            return {'status': 'NOT_OK', 'ERROR': 'Unknown error!'}, 500
                    except Exception as e:
                        print(e.__repr__())
                        return {'status': 'NOT_OK', 'ERROR': e.__repr__()}, 503
            else:
                return {'status': 'NOT_OK', 'ERROR': 'Wrong password!'}, 401
        else:
            return {'status': 'NOT_OK', 'ERROR': 'Nothing here!'}, 404

    def start():
        bot.remove_webhook()
        print("Setting webhook...", end=" ")
        try:
            bot.set_webhook(url=os.getenv("PUBLIC_URL") + bot.token)
            print("Webhook set!")
            return "Webhook set!"
        except:
            return "Webhook not set...Try again..."

    start()

    if configVars and configVars['runScheduler']:
        scheduler = BackgroundScheduler(timezone='Asia/Singapore')
        scheduler.add_job(testServer, trigger='cron', args=[configVars['localhost'], configVars['payload']], name='dailyUpdate', minute='*/1', timezone='Asia/Singapore')
        scheduler.start()
        DEBUG_MODE = False # Avoid duplicate logs

    app.run(debug=DEBUG_MODE, host="0.0.0.0", port=int(os.environ.get("PORT", 5005)))
