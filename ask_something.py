import json
from flask_socketio import SocketIO, send, emit
from templates import app
from flask_cors import CORS, cross_origin
from __main__ import socketIO

global stepCompletedJson

with open('templates/public/json/drinks.json') as d:
    drink = json.load(d)

with open('templates/public/json/people.json') as p:
    people = json.load(p)

with open('templates/public/json/speciality.json') as spe:
    speciality = json.load(spe)
  
class AskSomething:
    @staticmethod
    def start(js_view_key, arguments, index, dataToUse):

        text = arguments['speech']['title']
    
        if js_view_key == 'askDrink':

            drinks = drink
            AskSomething.drinks = drinks
            

            dataJsonToSendCurrentView = {
                    "view": 'askSomething',
                    "data": {
                        'textToShow': text,
                        'drinks' : drinks
                    },
                    "step":arguments
            }

        if js_view_key == 'askName':
            names = people
            AskSomething.names = names
        
            dataJsonToSendCurrentView = {
                    "view": 'askSomething',
                    "data": {
                        'textToShow': text,
                        'names' : names
                    },
                    "step":arguments
            }

        if js_view_key == 'askSpeciality':
            name = speciality
            AskSomething.name = name
            
            dataJsonToSendCurrentView = {
                    "view": 'askSomething',
                    "data": {
                        'textToShow': text,
                        'names' : name
                    },
                    "step":arguments
            }

        socketIO.emit('currentViewToSend',dataJsonToSendCurrentView,broadcast=True)


