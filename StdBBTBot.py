import requests  
import json
import wave
import os
from pathlib import Path
import random

MAIN_BUTTON_CALLBACK_DATA = 'get_audio_bm'
CURRENTDIR = Path(__file__).parent.absolute()
AUDIODIR = CURRENTDIR / 'vox_military'

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def getUpdates(self, offset=None, timeout=100): 
        url = self.api_url + 'getUpdates'
        data = {
            'timeout': timeout, 
            'offset': offset
        }

        resp = requests.get(url, data)
        result_json = resp.json()['result']
        return result_json

    def sendMessage(self, chat_id, text):
        print('Sending message: ' + text)

        url = self.api_url + 'sendMessage'
        data = {
            'chat_id': chat_id,
            'text': text
        }

        resp = requests.post(url, data)
        print(resp.text)
        return resp

    def sendMessageButton(self, chat_id, text, btnText):
        print('Sending message with button: ' + text)

        keyboard =  [
                        [
                            { 'text' : btnText, 'callback_data' : MAIN_BUTTON_CALLBACK_DATA}
                        ]
                    ]

        keyboardDict = {}
        
        # 'inline_keyboard' is an array of rows
        keyboardDict['inline_keyboard'] = []
        for row in keyboard:
            keyboardDict['inline_keyboard'].append(row)

        url = self.api_url + 'sendMessage'
        data = {
            'chat_id': chat_id, 
            'text': text,
            'reply_markup' : json.dumps(keyboardDict)
        }

        resp = requests.post(url, data)
        return resp

    def sendMessageAudio(self, chat_id, audioFileName):
        print('Sending message with audio')
        
        with open(audioFileName, 'rb') as f:
            files = { 'audio' : f }
            url = self.api_url + 'sendAudio?chat_id=' + str(chat_id)

            resp = requests.post(url, files = files)
            return resp

    def getLastUpdate(self):
        updates = self.getUpdates()

        if len(updates) > 0:
            return updates[-1]
        else:
            return None


# returns name
def generateAudio(chatId, sentence) :
    outfileNameWav = str(CURRENTDIR / ('sounds' + str(chatId) + '.wav'))

    data = []
    for wName in sentence:
        w = wave.open(str(AUDIODIR / (wName + '.wav')), 'rb')
        data.append( [w.getparams(), w.readframes(w.getnframes())] )
        w.close()

    output = wave.open(outfileNameWav, 'wb')
    output.setparams(data[0][0])
   
    for i in range(0, len(data)):
        output.writeframes(data[i][1])

    output.close()

    return outfileNameWav


def sendRandomAudio(bot, chatId, sentences):
    # generate file with random sentence
    audioFileName = generateAudio(chatId, random.choice(sentences))
    # send
    bot.sendMessageAudio(chatId, audioFileName)
    # delete generated file
    os.remove(audioFileName)


def loadSentences(filePath):
    with open(filePath) as f:
        sentences = [line.split() for line in f.readlines()]

    # check words in library
    for sentence in sentences:
        for word in sentence:
            if not (AUDIODIR / (word + '.wav')).exists():
                print(word + '.wav not found!')

    return sentences


def main(): 
    print('Current dir: ' + str(CURRENTDIR))
    print('Audio dir: ' + str(AUDIODIR))

    a = str(AUDIODIR / ('all' + '.wav'))

    token = str(os.environ.get('STDBBT_BOT_TOKEN'))
    stdbbt_bot = TelegramBot(token)
    new_offset = None

    sentences = loadSentences(str(CURRENTDIR / 'sentences.txt'))

    while True:
        try:
            stdbbt_bot.getUpdates(new_offset)

            lastUpdate = stdbbt_bot.getLastUpdate()

            lastUpdateId = lastUpdate['update_id']


            if 'callback_query' in lastUpdate:
                # if callback from button
                # get data from callback
                callbackData = lastUpdate['callback_query']['data']

                chatId = lastUpdate['callback_query']['message']['chat']['id']
                #chatUserName = lastUpdate['callback_query']['message']['chat']['first_name']

                if callbackData == MAIN_BUTTON_CALLBACK_DATA:
                    sendRandomAudio(stdbbt_bot, chatId, sentences)

                new_offset = lastUpdateId + 1

            elif 'message' in lastUpdate:
                chatId = lastUpdate['message']['chat']['id']
                #chatUserName = lastUpdate['message']['chat']['first_name']

                chatText = lastUpdate['message']['text']
                chatText = chatText.lower()

                if (chatText != '/get'):
                    stdbbt_bot.sendMessageButton(chatId, 'Press the button to get auto-generated audio', 'Get audio')
                else:
                    sendRandomAudio(stdbbt_bot, chatId, sentences)

                new_offset = lastUpdateId + 1
        
        except Exception as e:
            print(str(e))


if __name__ == '__main__':  
    try:
        main()
    except KeyboardInterrupt:
        exit()