import json
from flask_socketio import SocketIO, send, emit
from templates import app
from flask_cors import CORS, cross_origin
from __main__ import socketIO

global stepCompletedJson

with open('templates/public/json/speciality.json') as spe:
    speciality = json.load(spe)

class AskSpeciality:
    global dataJsonToSendCurrentView
    global dataJsonToSendCurrentView
    @staticmethod
    def start(js_view_key, arguments, index, dataToUse):

        text = arguments['speech']['title']
        
        names = speciality
        AskSpeciality.names = names
        
        dataJsonToSendCurrentView = {
                "view": js_view_key,
                "data": {
                    'textToShow': text,
                    'names' : names
                },
                "step":arguments
        }
        socketIO.emit('currentViewToSend',dataJsonToSendCurrentView,broadcast=True)
        # emit('currentStep',dataJsonToSendCurrentStep)
        # socketio.sleep(5)
        # stepCompletedJson = {"idSteps": index}
        # emit('stepCompleted',stepCompletedJson)

    # @staticmethod
    # def received_data(local_manager, data):
    #     logger.log("AskName: data = " + str(data), "Views Manager", logger.DEBUG)
    #     if hasattr(AskName, 'action_id') and hasattr(AskName, 'names') and data['data'] in AskName.names:
    #         return {'id': AskName.action_id, 'name': data['data']}
    #     return True

    # @staticmethod
    # def stop(local_manager):
    #     if hasattr(AskName, 'topic_name') and AskName.topic_name:
    #         local_manager.dialog.deactivateTopic(AskName.topic_name)
    #         local_manager.dialog.unloadTopic(AskName.topic_name)
    #         if hasattr(AskName, 'reactivateMovement'):
    #             local_manager.autonomous_life.setAutonomousAbilityEnabled("SpeakingMovement", True)
    #             delattr(AskName, 'reactivateMovement')
    #         delattr(AskName, "topic_name")