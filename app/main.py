from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
import telebot
import os

from Telegram.bot import createBot, dailyUpdate
from utils import testServer, loadData, downloadResult

configVars = loadData()

DEBUG_MODE = False #eval(os.getenv("DEBUG_MODE"))
SAVE_RESPONSE = False

app = Flask(__name__)

if __name__ == "__main__":
    bot = createBot()
    weburl = os.getenv("PUBLIC_URL") + bot.token
    print(weburl)

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
                bot.set_webhook(url=weburl)
                return "Webhook set!", 200
            except:
                return "Webhook not set...Try again...", 400
        elif request.method == "POST":
            print("Wating...")
            return "!", 200

    @app.route('/dailyUpdate', methods=['POST'])
    def _dailyUpdate():
        if request.method == 'POST':
            if 'password' in request.json and request.json['password'] == configVars['password']:
                # Download result
                result = downloadResult()
                # Get subscribers
                users = configVars['userIds']

                # Update subscribers
                for user in users:
                    print(user, result)
                    dailyUpdate(user, result)

                return {'status': 'OK'}, 200
            else:
                return {'ERROR': 'Wrong password!'}, 404
        else:
            return {'ERROR': 'Nothing here!'}, 404

    def start():
        bot.remove_webhook()
        print("Setting webhook...", end=" ")
        try:
            bot.set_webhook(url=weburl)
            print("Webhook set!")
            return "Webhook set!"
        except:
            return "Webhook not set...Try again..."

    start()

    if configVars and configVars['runScheduler']:
        scheduler = BackgroundScheduler(timezone='Asia/Singapore')
        scheduler.add_job(testServer, trigger='cron', args=[configVars['localhost'], configVars['payload']], name='dailyUpdate', hour='23', timezone='Asia/Singapore')
        scheduler.start()

    app.run(debug=DEBUG_MODE, host="0.0.0.0", port=int(os.environ.get("PORT", 5005)))
