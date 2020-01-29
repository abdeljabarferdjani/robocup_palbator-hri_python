import json
from flask_socketio import SocketIO, send, emit
from templates import app
from flask_cors import CORS, cross_origin
from __main__ import socketIO

global stepCompletedJson

class AskOpenDoor:
    @staticmethod
    def start(js_view_key, arguments, index, dataToUse):
        # AskOpenDoor.action_id = arg_fetcher.get_argument(arguments, 'id')
        # if not AskOpenDoor.action_id:
        #     # logger.log("Missing id in {0} action arguments".format(js_view_key), "Views Manager", logger.ERROR)
        #     # local_manager.send_view_result(js_view_key, {'error': 400})
        #     print('error 400')
        
        ##########

        # args = arg_fetcher.get_argument(arguments, 'args')
        # speech = arg_fetcher.get_argument(args, 'speech')
        
        # text = arg_fetcher.get_argument(speech, 'title')
        # said = arg_fetcher.get_argument(speech, 'said')
        # desc = arg_fetcher.get_argument(speech, 'description')

        text = arguments['speech']['title']
        desc = arguments['speech']['description']
        #######
        print(arguments)
        dataJsonToSendCurrentView = {
                "view": js_view_key,
                "data": {
                    'textToShow': {
                        'title': text,
                        'description': [desc]
                    }
                },
                "step":arguments ## For putOneStep
        }
        socketIO.emit('currentViewToSend',dataJsonToSendCurrentView,broadcast=True)
        


    # @staticmethod
    # def received_data(local_manager, data):
    #     if hasattr(AskOpenDoor, 'action_id'):
    #         return {'id': AskOpenDoor.action_id}
    #     return True

    # @staticmethod
    # def stop(local_manager):
    #     if hasattr(AskOpenDoor, 'topic_name') and AskOpenDoor.topic_name:
    #         local_manager.dialog.deactivateTopic(AskOpenDoor.topic_name)
    #         local_manager.dialog.unloadTopic(AskOpenDoor.topic_name)
    #         if hasattr(AskOpenDoor, 'reactivateMovement'):
    #             local_manager.autonomous_life.setAutonomousAbilityEnabled("SpeakingMovement", True)
    #             delattr(AskOpenDoor, 'reactivateMovement')
    #         delattr(AskOpenDoor, "topic_name")