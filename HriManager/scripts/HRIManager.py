#!/usr/bin/env python
from socketIO_client import SocketIO, LoggingNamespace
from python_depend.views import Views
import json as js

from std_msgs.msg import String
import rospy
import os 
import actionlib
from HriManager.msg import GmToHriAction, GmToHriFeedback, GmToHriResult
import time
from copy import deepcopy

from python_depend.views import Views
import speechToTextPalbator.msg
import ttsMimic.msg

class HRIManager:

  def __init__(self):
    """
        Initialize the HRI Manager
    """
    rospy.init_node("ROS_HRI_node",anonymous=True)

    self.setup_config_yaml()
    
    self.connection_ON=None
    self.nameToUse=[]
    self.drinkToUse=[]
    self.ageToUse = []
    self.choosenName = None
    self.choosenDrink = None
    self.choosenAge = None
    self.choosenRoom = None
    self.nameAction = None
    self.currentStep = None
    self.currentAction = None
    self.index=0
    self.indexStepCompleted=0
    self.dataToUse=''
    self.data_received=False
    self.currentIndexDataReceivedJS=0
    self.end_guest_procedure=None
    self.json_for_GM=None
    self.event_detected_flag=False

    self.stepsList=None
    self.enable_choice_scenario=True
    self.event_touch = False

    self.init_socket_listeners()

    self.view_launcher=Views(self.socketIO)

    self.action_GM_TO_HRI_server.start()
    self.enable_changing_connection=True
    self.sub_connection_state = rospy.Subscriber(rospy.get_param('~topic_connection_state'),String,self.handle_change_connection_state)
    rospy.loginfo('HRI MANAGER LAUNCHED')

  def setup_config_yaml(self):
    """
        Load the configuration parameters from YAML.
    """
    self.enable_vocal_detection = rospy.get_param("~enable_STT")

    _socketIO_ip_param = "~socketIO_IP"
    _socketIO_port_param = "~socketIO_port"
    _topic_choice_scenario = rospy.get_param("~topic_choice_scenario")
    _stt_online_server_name = rospy.get_param("~stt_online")
    _stt_offline_server_name = rospy.get_param("~stt_offline")
    _tts_mimic_server_name = rospy.get_param("~tts_mimic")
    _action_server_hri_name = rospy.get_param("~action_server_hri")
    socketIP = None
    socketPort = None
    if rospy.has_param(_socketIO_ip_param):
      socketIP = rospy.get_param(_socketIO_ip_param)
    else:
      rospy.logerr("No IP specified for socketIO. Couldn't open the socket communication.")
      return

    if rospy.has_param(_socketIO_port_param):
      socketPort = rospy.get_param(_socketIO_port_param)
    else:
      rospy.logerr("No port specified for socketIO. Couldn't open the socket communication")
      return

    self.socketIO = SocketIO(socketIP, socketPort, LoggingNamespace)
    self.pub_choice_scenario=rospy.Publisher(_topic_choice_scenario,String,queue_size=1)
    self.action_online_client = actionlib.SimpleActionClient(_stt_online_server_name,speechToTextPalbator.msg.SttOnlineAction)
    self.action_offline_client = actionlib.SimpleActionClient(_stt_offline_server_name,speechToTextPalbator.msg.SttOfflineAction)
    self.client_TTS=actionlib.SimpleActionClient(_tts_mimic_server_name,ttsMimic.msg.TtsMimicAction)
    self.action_GM_TO_HRI_server=actionlib.SimpleActionServer(_action_server_hri_name,GmToHriAction,self.action_GmToHri_callback,auto_start=False)
    self.action_GM_TO_HRI_feedback=GmToHriFeedback()
    self.action_GM_TO_HRI_result=GmToHriResult()
    if self.enable_vocal_detection == True:
      rospy.loginfo("Waiting for online server...")
      self.action_online_client.wait_for_server()
      rospy.loginfo("Connected to server")

      rospy.loginfo("Waiting for offline server...")
      self.action_offline_client.wait_for_server()
      rospy.loginfo("Connected to offline server")

    rospy.loginfo("Waiting for TTS server...")
    self.client_TTS.wait_for_server()
    rospy.loginfo("TTS server connected")

  def init_socket_listeners(self):
    """
        Initialize all the event listeners for the socketIO
    """
    #callback quand user choisit scenario sur tablette
    self.socketIO.on(rospy.get_param('~socket_choose_scenario'),self.chooseScenario)
    #callback reponse quand scenario choisit et charge
    self.socketIO.on(rospy.get_param('~socket_scenario_loaded'),self.scenarioCharged)
    #callback quand on recoit des donnees de la tablette
    self.socketIO.on(rospy.get_param('~socket_index_view_received'), self.indexDataJSstepDone)
    self.socketIO.on(rospy.get_param('~socket_data_received'), self.dataJSstepDone)
    #recuperation de l'order de la view chargee par la tablette
    self.socketIO.on(rospy.get_param('~socket_view_loaded'), self.send_gm_view_launched)
    # self.socketIO.on(rospy.get_param('~socket_hri_reset'), self.restart_hri)

  def handle_change_connection_state(self,req):
    """
        Callback function when a connection state change is detected
    """
    if self.enable_changing_connection==True:
      if req.data=='Connected':
        self.action_offline_client.cancel_all_goals()
        self.connection_ON=True
          
      elif req.data=='Disconnected':
        self.action_online_client.cancel_all_goals()
        self.connection_ON=False


  def tts_action(self,speech):
    """
        Send the speech to say to the TTS ActionServer

        :param speech: text to say
        :type speech: string
    """
    self.goal_TTS=ttsMimic.msg.TtsMimicGoal(speech)
    self.client_TTS.send_goal(self.goal_TTS)
    self.client_TTS.wait_for_result()


  def parser_scenario_step(self,scenario,goal):
    """
        Decide how to launch a step according to its action and its name.

        If new views or new scenarios are added, add them in the parser below.

        self.dynamic_view is for views which require additional data or an event

        self.static_view is for views which don't require any data or event

        self.load_multiple_views is to launch a sequence of views managed by HRI only

        :param scenario: scenario name
        :type scenario: string
        :param goal: Step informations
        :type goal: dict
    """
    which_step_action=deepcopy(self.stepsList[goal['stepIndex']]['action'])
    which_step_name=deepcopy(self.stepsList[goal['stepIndex']]['name'])

    if scenario == 'receptionist':
        ##### rajouter des conditions si nouvelles actions importantes
      if which_step_action != '':
        if which_step_action=='askOpenDoor':
          self.dynamic_view(goal['stepIndex'],None,wait_for_event=True)

        elif which_step_action=='presentPerson':
          self.dynamic_view(goal['stepIndex'],goal['data'])

        elif which_step_action=='seatGuest':
          self.dynamic_view(goal['stepIndex'],goal['data'])

        elif which_step_action=="pointTo":
          self.dynamic_view(goal['stepIndex'],goal['data'])

        elif which_step_action=='askToFollow':
          self.dynamic_view(goal['stepIndex'],goal['data'])

        else:
          self.static_view(goal['stepIndex'])
      
      else:
        if "Ask infos" in which_step_name:
          self.load_multiple_views(goal['stepIndex'],procedure_type='guestInfos')

        else:
          self.static_view(goal['stepIndex'])

    elif scenario == 'cleanup':
      if 'Ask room' in which_step_name:
        self.load_multiple_views(goal['stepIndex'],procedure_type='chooseRoom')
      else:
        self.static_view(goal['stepIndex'])

  def action_GmToHri_callback(self,goal):
    """
        Callback function for ActionServer HRI. Receive a goal and load the correct view according its step index.

        :param goal: A json containing parameters in order to load a specific view 
        :type goal: GmToHriGoal
    """
    rospy.loginfo("Action initiating ...")
    success=True
    json_output=None
    self.action_GM_TO_HRI_feedback.Gm_To_Hri_feedback=''
    json_goal=js.loads(goal.json_request)
    if json_goal['action']=="stepsList":
      self.scenario_loaded=False
      rospy.loginfo("Getting steps list...")
      self.stepsList=json_goal['stepsList']
      self.choosen_scenario=json_goal['scenario']
      self.json_for_GM={
        "result": "Steps received"
      }

    elif json_goal['action']=="currentStep":
      if json_goal['stepIndex']==0:
        json_charge_scenario={
          'scenario': self.choosen_scenario
        }
        self.chargeScenario(json_charge_scenario)
        
      self.parser_scenario_step(self.choosen_scenario,json_goal)

    json_output=self.json_for_GM
    if 'result' in json_output and json_output['result']=='PREEMPTED':
      success=False

    self.action_GM_TO_HRI_server.publish_feedback(self.action_GM_TO_HRI_feedback)
    if success:
      self.action_GM_TO_HRI_result.Gm_To_Hri_output=js.dumps(json_output)
      rospy.loginfo("Action GM TO HRI succeeded")
      
      self.action_GM_TO_HRI_server.set_succeeded(self.action_GM_TO_HRI_result)


  def load_step_without_action(self):
    """
        Load a view which doesn't have any action name.
    """
    if self.index != 0:
      stepCompletedJson = {"idSteps": self.indexStepCompleted}
      self.socketIO.emit(rospy.get_param("~socket_emit_step_complete"),stepCompletedJson,broadcast=True)
      rospy.loginfo("ETAPE TERMINEE: "+str(self.currentStep['name']))
      self.indexStepCompleted = self.index
    else:
      self.indexStepCompleted = self.index

    rospy.loginfo("ETAPE COURANTE A DEMARRER: "+self.currentStep['name'])
    dataJsonToSendCurrentStep = {
        "index": self.index,
        "step":self.currentStep
    }
    self.socketIO.emit(rospy.get_param("~socket_emit_current_step"),dataJsonToSendCurrentStep,broadcast=True)
    if self.currentStep['id'] != 'FinishScenario':
      dataJsonToSendTimer = {
          "state": 'TOGGLE_TIMER/ON'
      }
      self.socketIO.emit(rospy.get_param("~socket_emit_start_timer"),dataJsonToSendTimer, broadcast=True)
    rospy.loginfo("ETAPE DEMARREE: "+self.currentStep['name'])
      

  def load_view_with_action(self):
    """
        Load a view with an action name.
    """
    self.view_launcher.start(self.currentStep['action'],self.currentStep, self.currentStep['order'], self.dataToUse)
    rospy.loginfo("CHARGEMENT VUE SOUS ETAPE:"+self.currentStep['name'] +" SUR TABLETTE")

    speech=deepcopy(self.currentStep['speech']['said'])
    self.tts_action(speech)
    

  def static_view(self,stepIndex):
    """
        Load a static view (a view which doesn't wait for an event)

        :param stepIndex: the index of the step to load
        :type stepIndex: int
    """
    rospy.logwarn("STATIC VIEW : "+str(stepIndex))
    self.currentStep=deepcopy(self.stepsList[stepIndex])
    self.index=deepcopy(self.currentStep['order'])
    self.currentAction=deepcopy(self.currentStep['action'])
    if self.currentAction == '':
      self.load_step_without_action()
    else:
      self.load_view_with_action()

    self.json_for_GM={
        "indexStep": self.index,
        "actionName": '',
        "NextToDo": "next",
        "NextIndex": self.index+1
    }
    self.event_detected_flag=True
    self.socketIO.wait(seconds=0.1)

  def dynamic_view(self,stepIndex,data=None,wait_for_event=False,in_procedure=False):
    """
        Load a dynamic view (a view which will wait for an event or a view which needs additional data to be loaded)

        :param stepIndex: the index of the step to load
        :type stepIndex: int
        :param data: Additional data could be sent by GeneralManager to be used in the view
        :type data: dict
        :param wait_for_event: Flag to decide if the view will wait for an event or not
        :type wait_for_event: Boolean
        :param in_procedure: Flag to know if the view is part of a procedure (sequence of views managed by HRI) or not
        :type in_procedure: Boolean
    """
    rospy.logwarn("DYNAMIC VIEW : "+str(stepIndex))
    self.currentStep=deepcopy(self.stepsList[stepIndex])
    self.index=deepcopy(self.currentStep['order'])
    self.currentAction=deepcopy(self.currentStep['action'])

    if wait_for_event == False:

      if self.currentAction == "askToFollow":
        key=self.currentStep['arguments']['who']
        self.currentStep['speech']['said']=self.currentStep['speech']['said'].replace(key+"_name",data[key]['name'])
      
      elif self.currentAction == "presentPerson":
        speech=self.currentStep['speech']['said']
        number_know_guests=len(self.currentStep['arguments']['to'])

        for key in data.keys():
          for i in range(0,number_know_guests):
            if key in self.currentStep['arguments']['to'][i]['name']:
              self.currentStep['arguments']['to'][i]['name']=data[key]['name']
              self.currentStep['arguments']['to'][i]['guestPhotoPath']=data[key]['guestPhotoPath']
              self.currentStep['arguments']['to'][i]['drink']['name']=data[key]['drink']
              self.currentStep['arguments']['to'][i]['drink']['pathOnTablet']=data[key]['pathOnTablet']

              rospy.logwarn("KEY "+str(key)+" DRINK "+str(data[key]['drink'])+" DRINKPATH "+str(data[key]['pathOnTablet']))

          if key in self.currentStep['arguments']['who']['name']:
            self.currentStep['arguments']['who']['name']=data[key]['name']
            self.currentStep['arguments']['who']['guestPhotoPath']=data[key]['guestPhotoPath']
            self.currentStep['arguments']['who']['drinkObj']['name']=data[key]['drink']
            self.currentStep['arguments']['who']['drinkObj']['pathOnTablet']=data[key]['pathOnTablet']
            rospy.logwarn("KEY "+str(key)+" DRINK "+str(data[key]['drink'])+" DRINKPATH "+str(data[key]['pathOnTablet']))

          speech=speech.replace(key+'_name',data[key]['name'])
          speech=speech.replace(key+'_drink',data[key]['drink'])
        self.currentStep['speech']['said']=speech
      
      elif self.currentAction == "seatGuest":
        for key in data.keys():
          if key in self.currentStep['arguments']['who']['name']:
            self.currentStep['arguments']['who']['name']=data[key]['name']
            self.currentStep['arguments']['who']['guestPhotoPath']=data[key]['guestPhotoPath']
            self.currentStep['speech']['said']=self.currentStep['speech']['said'].replace(key+"_name",data[key]['name'])
            self.currentStep['speech']['title']=self.currentStep['speech']['title'].replace(key+"_name",data[key]['name'])

      elif self.currentAction == "pointTo":
        object_to_point=deepcopy(self.currentStep['arguments']['what'])
        if object_to_point=='chair':
          pass
        elif object_to_point=='human':
          for key in data.keys():
            if key in self.currentStep['arguments']['who']['name']:
              self.currentStep['arguments']['who']['name']=data[key]['name']
              self.currentStep['arguments']['who']['guestPhotoPath']=data[key]['guestPhotoPath']
              self.currentStep['speech']['said']=self.currentStep['speech']['said'].replace(key+"_name",data[key]['name'])
              self.currentStep['speech']['title']=self.currentStep['speech']['title'].replace(key+"_name",data[key]['name'])

      self.load_view_with_action()

      self.json_for_GM={
          "indexStep": self.index,
          "actionName": '',
          "NextToDo": "next",
          "NextIndex": self.index+1
      }
      self.event_detected_flag=True
      self.socketIO.wait(seconds=0.1)

    else:
      speech = deepcopy(self.currentStep['speech']['said'])
      title = deepcopy(self.currentStep['speech']['title'])

      if self.currentAction == 'confirm':
        if self.currentStep['name'] == 'Confirm room':
          speech=speech.replace("location_name",self.choosenRoom)
          title=title.replace("location_name",self.choosenRoom)

        elif "drink" in self.currentStep['name']:
          speech=speech.format(drink=str(self.choosenDrink))
          title=title.format(drink=str(self.choosenDrink))

        elif "name" in self.currentStep['name']:
          speech=speech.format(name=self.choosenName)
          title=title.format(name=self.choosenName)
      else:
        if "drink" in self.currentStep['name']:
          speech=speech.format(name=str(self.nameToUse[-1]))

      self.currentStep['speech']['said'] = speech
      self.currentStep['speech']['title'] = title
      
      self.load_view_with_action()
      self.event_touch = False

      if self.enable_vocal_detection == True:
        if self.connection_ON==True:
          self.routine_online()

        elif self.connection_ON==False:
          self.routine_offline()
      else:
        while self.event_touch == False:
          self.socketIO.wait(0.1)
        self.event_touch = False

      if in_procedure == False:
        self.json_for_GM={
                        "indexStep": self.index,
                        "actionName": self.currentAction,
                        "dataToUse": self.dataToUse,
                        "NextToDo": "next",
                        "NextIndex": self.index+1
        }


  def load_multiple_views(self,indexStep,procedure_type):
    """
        A sequence of views is loaded by HRI without GeneralManager's intervention.

        :param indexStep: the index of the step to load
        :type indexStep: int
        :param procedure_type: name of the loaded sequence 
        :type procedure_type: string 
    """
    
    rospy.logwarn("STARTING PROCEDURE VIEW : "+procedure_type)

    end_procedure = False
    index_procedure=indexStep

    while end_procedure == False:
      self.currentStep=deepcopy(self.stepsList[index_procedure])
      self.index=deepcopy(self.currentStep['order'])
      self.currentAction=deepcopy(self.currentStep['action'])
      rospy.loginfo("CURRENT ACTION "+str(self.currentAction))
      if self.currentAction == '':
        self.load_step_without_action()
        index_procedure=index_procedure+1
        rospy.logwarn("NEXT PROCEDURE INDEX "+str(index_procedure))
      else:
        self.dynamic_view(index_procedure,data=None,wait_for_event=True,in_procedure=True)

        if self.currentAction == 'confirm':
          if self.dataToUse=='false' or self.dataToUse=='NO':
              rospy.loginfo("RECEIVED DATA -> FALSE")
              if "name" in self.currentAction:
                self.choosenName=''
              elif "drink" in self.currentAction:
                self.choosenDrink=''
              index_procedure=index_procedure-1
          elif self.dataToUse=='true' or self.dataToUse=='YES':
            rospy.loginfo("RECEIVED DATA -> TRUE")
            if "name" in self.currentStep['name']:
              self.nameToUse.append(self.choosenName)
            elif "drink" in self.currentStep['name']:
              self.drinkToUse.append(self.choosenDrink)
            index_procedure=index_procedure+1
            if procedure_type == 'chooseRoom':
              end_procedure=True
        
        else:
          if self.currentAction == 'askRoomToClean':
            self.choosenRoom = self.dataToUse

          elif self.currentAction == 'askName':
            self.choosenName = self.dataToUse
          
          elif self.currentAction == 'askDrink':
            self.choosenDrink = self.dataToUse
          
          elif self.currentAction == 'askAge':
            self.choosenAge = self.dataToUse
            end_procedure=True
          
          index_procedure=index_procedure+1

    if procedure_type == 'chooseRoom':
      self.json_for_GM={
        "indexStep": self.index,
        "actionName": self.currentAction,
        "dataToUse": self.dataToUse,
        "NextToDo": "next",
        "NextIndex": self.index+1,
        "saveData":{
          "where": self.choosenRoom
        }
      }
    elif procedure_type == 'guestInfos':
      self.json_for_GM={
        "indexStep": self.index,
        "actionName": self.currentAction,
        "dataToUse": self.dataToUse,
        "NextToDo": "next",
        "NextIndex": self.index+1,
        "saveData":{
          "who": self.currentStep['arguments']['who'],
          "name": self.nameToUse[-1],
          "drink": self.drinkToUse[-1],
          "age": self.choosenAge
        }
      }
    rospy.loginfo("END PROCEDURE "+str(procedure_type))

  def routine_online(self):
    """
        Function to use the online Speech Detection. If the counter reaches the timeout, the system will switch to offline Speech Detection. 
    """
    rospy.loginfo("----------- DEBUT ROUTINE ONLINE--------------------------------")
    self.goal_online = speechToTextPalbator.msg.SttOnlineGoal()
    rospy.loginfo("Sending goal to online ...")
    order={
        'order': self.index,
        'action': self.currentAction
    }
    json_in_str=js.dumps(order)
    self.goal_online.order=json_in_str
    self.action_online_client.send_goal(self.goal_online)
    cp=0
    while self.action_online_client.get_result() is None and not rospy.is_shutdown():
      if cp==20 or self.connection_ON==False:
        self.action_online_client.cancel_all_goals()
        self.tts_action('Switching to offline mode')
        break
      elif self.event_touch == True:
        self.action_online_client.cancel_all_goals()
        break

      rospy.loginfo("Waiting for online detect ....")
      cp=cp+1
      self.socketIO.wait(seconds=0.1)

    rospy.loginfo(str(self.action_online_client.get_result()))
    if not self.action_online_client.get_result() is None and self.action_online_client.get_result().stt_result != '':
      self.dataToUse=str(self.action_online_client.get_result().stt_result)
    elif self.event_touch==True:
      self.event_touch = False
      rospy.logwarn("EVENT TOUCH "+str(self.event_touch))
    else:
      self.enable_changing_connection=False
      self.routine_offline()
      self.enable_changing_connection=True

    rospy.loginfo("----------- FIN ROUTINE ONLINE--------------------------------")

  def routine_offline(self):
    """
        Function to use the offline Speech Detection. 
    """
    rospy.loginfo("----------- DEBUT ROUTINE OFFLINE--------------------------------")
    self.goal_offline = speechToTextPalbator.msg.SttOfflineGoal()
    rospy.loginfo("Sending goal to offline ...")
    order={
        'order': self.index,
        'action': self.currentAction
    }
    json_in_str=js.dumps(order)
    self.goal_offline.order=json_in_str
    self.action_offline_client.send_goal(self.goal_offline)
    while self.action_offline_client.get_result() is None and not rospy.is_shutdown():
      if self.event_touch == True:
        self.action_offline_client.cancel_all_goals()
        self.event_touch = False
        rospy.logwarn("EVENT TOUCH "+str(self.event_touch))
        break
      rospy.loginfo("Waiting for OFFLINE detect ....")
      self.socketIO.wait(seconds=0.1)
    rospy.loginfo(str(self.action_offline_client.get_result()))
    if str(self.action_offline_client.get_result().stt_result) != '':
      self.dataToUse=str(self.action_offline_client.get_result().stt_result)
    rospy.loginfo("----------- FIN ROUTINE OFFLINE--------------------------------")

  def indexDataJSstepDone(self,json):
    """
        When a view is loaded, the React send back a JSON containing informations about the view. This function gets the index of the last view successfully loaded.

        :param json: JSON with data of last loaded view
        :type json: dict
    """
    if('data' in json):
      self.currentIndexDataReceivedJS = json['data']

##################################### DATA RECEIVED FROM TOUCH MANAGER #################################################
  def dataJSstepDone(self,json):
    """
        This function will get the data sent by React after a view is loaded. If the view was associated to an event, the received data is collected.

        :param json: JSON with data of last loaded view
        :type json: dict
    """
    self.client_TTS.cancel_all_goals()
    self.event_detected_flag=True
    
    if (self.data_received is False and self.index == self.currentIndexDataReceivedJS):
      self.event_touch = True
      rospy.logwarn("EVENT TOUCH "+str(self.event_touch))
      rospy.loginfo("DONNEE RECUE DEPUIS TOUCH MANAGER")
      self.action_online_client.cancel_all_goals()
      self.action_offline_client.cancel_all_goals()
      self.data_received=True
      self.dataToUse = json['data']
      rospy.loginfo("DONNEE TOUCH MANAGER: "+str(self.dataToUse))

    else:
      rospy.logwarn('Le touch Manager envoie une donnee a la mauvaise etape: '+str(self.currentIndexDataReceivedJS)+' au lieu de '+str(self.index))

    self.data_received=False
    
  ###########################

  def scenarioCharged(self,json):
    """
        Callback function when a scenario is successfully loaded on the screen by the React. 

        :param json: JSON with data of the loaded scenario
        :type json: dict 
    """
    rospy.loginfo("HRI : SCENARIO CHARGED")
    self.json_for_GM=json
    self.scenario_loaded=True

  def chooseScenario(self,json):
    """
        Callback function when a scenario button is clicked on the screen. The scenario choice is sent to HRI by the React.

        :param json: JSON with data of the choosen scenario
        :type json: dict 
    """
    if self.enable_choice_scenario==True:
      self.enable_choice_scenario=False
      rospy.loginfo("choosing scenario...")
      self.choosen_scenario = json['scenario']
      self.pub_choice_scenario.publish(self.choosen_scenario)


  ########################## Chargement du scenario selectionne ################

  ######### On recoit depuis le REACT le nom du scenario selectionne et on charge le json approprie pour lui renvoyer ############
  def chargeScenario(self,json):
    """
        Callback function to send the data of the scenario to load to the React. 

        :param json: JSON with data of the scenario to load
        :type json: dict 
    """
    self.socketIO.emit(rospy.get_param('~socket_emit_scenario_to_charge'),json, broadcast=True)
  
  def send_gm_view_launched(self,json):
    """
        Callback function when a view is loaded on the screen. Gets the index of the loaded view.

        :param json: JSON with data of the loaded view
        :type json: dict 
    """
    self.json_confirm_View_launch=json
    rospy.loginfo(str(json['data']))
    rospy.loginfo("Index de la vue lancee sur le Touch : "+str(json['index']))

  def restart_hri(self,json):    
    """
        NOT WORKING FOR NOW.
        Callback function when the STOP button is clicked on the screen. Launches a reset of HRI and React.

        :param json: JSON with data of the last event
        :type json: dict 
    """
    socketIO.emit(rospy.get_param('~socket_emit_restart_hri'),broadcast=True)
    self.pub_restart_request.publish("RESTART")


if __name__ == '__main__':

  hri = HRIManager()

  while not rospy.is_shutdown():
    rospy.spin()

