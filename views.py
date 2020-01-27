import json
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, send, emit
from __main__ import socketIO
from ask_age import AskAge
from ask_drink import AskDrink
from ask_name import AskName
from ask_speciality import AskSpeciality
from ask_to_follow import AskToFollow
from call_human import CallHuman
from confirm import Confirm
from generic import Generic
from go_to import GoTo
from present_person import PresentPerson
from seat_guest import SeatGuest
from show_video import ShowVideo
from ask_open_door import AskOpenDoor
from display_info import DisplayInfo
from wait import Wait


class Views:
    last_action = None
    current_scenario = None
    action_class_map = {
        'askAge': AskAge,
        'askDrink': AskDrink,
        'askName': AskName,
        'askSpeciality': AskSpeciality,
        'displayInfo': DisplayInfo,
        'askOpenDoor': AskOpenDoor, # textToPrint
        'askToFollow': AskToFollow, # 
        'callHuman': CallHuman,
        'confirm': Confirm, # textToPrint
        'detailDrinks': None,
        'findAvailableDrinks': None,
        'findWhoWantsDrinks': None,
        'generic': Generic,
        'goTo': GoTo, # textToPrint
        'openDoor': None,
        'presentPerson': PresentPerson, # textToPrint, people: {who: {name, drinkId}, to: {name, drinkId}}
        'seatGuest': SeatGuest, # 
        'serveDrinks': None,
        'showVideo': ShowVideo,
        'wait': Wait # time
    }


    @staticmethod
    def start(step_name, arguments,  index, dataToUse):
        if step_name in Views.action_class_map and Views.action_class_map[step_name]:
            try:
                Views.last_action = step_name
                Views.action_class_map[step_name].start(step_name, arguments,index,dataToUse)
            except RuntimeError as ex:
                Views.last_action = None
        else:
          print('no action found')
          print(step_name)


    # @staticmethod
    # def received_data(local_manager, data):
    #     if Views.last_action:
    #         try:
    #             logger.log('Received data on "' + str(Views.last_action) + '"', "QiChat", logger.DEBUG)
    #             result = Views.action_class_map[Views.last_action].received_data(local_manager, data)
    #             logger.log('Processed data on "' + str(Views.last_action) + '"', "QiChat", logger.DEBUG)

    #             if result:
    #                 local_manager.send_view_result(Views.last_action, result)
    #                 logger.log("Sent on ActionComplete: " + str({'ok': Views.last_action}), "Views Manager", logger.DEBUG)
    #         except RuntimeError as ex:
    #             logger.log('An error occured while processing data on "' + Views.last_action + '":\n' + str(ex), "Views Manager", logger.ERROR)
    #             local_manager.send_view_result(Views.last_action, {'id': Views.last_action.action_id, 'error': "500"})
                

    # @staticmethod
    # def stop(local_manager):
    #     if Views.last_action:
    #         try:
    #             logger.log('Unloading "' + str(Views.last_action) + '"', "QiChat", logger.DEBUG)
    #             Views.action_class_map[Views.last_action].stop(local_manager)
    #             logger.log('Unloaded "' + str(Views.last_action) + '"', "QiChat", logger.DEBUG)
    #         except RuntimeError as ex:
    #             logger.log('An error occured while unloading "' + str(Views.last_action) + '":\n' + str(ex), "QiChat", logger.ERROR)
    #             local_manager.send_view_result(Views.last_action, {'id': Views.action_class_map[Views.last_action].action_id, 'error': "500"})
    #         Views.last_action = None
