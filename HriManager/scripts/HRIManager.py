#!/usr/bin/env python


from socketIO_client import SocketIO, LoggingNamespace
import json

from std_msgs.msg import String
import rospy
import os 

  
class HRIManager:
  # def load_scenario_json(self,json):
  #   name_scenario_unicode = json['scenario']
  #   name_scenario = str(name_scenario_unicode)
  #   print(name_scenario,type(name_scenario))
  #   path_scenario_json = '/Users/abdeljabarferdjani/Documents/Robocup/robocup_palbator-hri_python/templates/public/json/' +name_scenario+'/scenario.json'
  #   print(type(path_scenario_json))
  #   print('nom du path',path_scenario_json)
  #   with open(path_scenario_json) as scenar:
  #     print(scenar)
      # chargedScenario = json.load(scenar) ## essayer avec loads
      # print(chargedScenario)
    # return chargedScenario

  def __init__(self):
    rospy.init_node("hri_manager_node",anonymous=True)
    self.pub_result=rospy.Publisher("result",String,queue_size=10)
    self.subscriber=rospy.Subscriber("test",String,self.handle_sub)


    
    dir_path = os.path.dirname(os.path.realpath(__file__))
    ######### SCENARIO JSON LOAD #############

    with open(dir_path+'/templates/public/json/present_school_test/scenario.json') as pres_school:
      self.presentSchool = json.load(pres_school)
      self.presentSchool['name']='present_school'

    with open(dir_path+'/templates/public/json/creation_test/scenario.json') as creationTest:
        self.creation = json.load(creationTest)
        self.creation['name']='creation_test'

    with open(dir_path+'/templates/public/json/inspection/scenario.json') as inspec:
        self.inspection = json.load(inspec)
        self.inspection['name']='inspection'

    with open(dir_path+'/templates/public/json/take_out_the_garbage/scenario.json') as take_garbage:
        self.takeOutGarbage = json.load(take_garbage)
        self.takeOutGarbage['name']='take_out_the_garbage'

    with open(dir_path+'/templates/public/json/receptionist/scenario.json') as recep:
        self.receptionist = json.load(recep)
        self.receptionist['name']='receptionist'


    self.finalStep = None
    self.currentStep = None
    self.currentAction = None
    self.index=0
    self.indexStepCompleted=0
    self.dataToUse=''
    self.indexFailure=None
    self.restart=0
    print("index global",self.index)


      
  ##########
  # On a le current step en json et son index afin de start la vue approprie
  # Si le step n a pas d action, c est que c est le titre d une etape.
  # Dans ce cas la, on update l etat de currentStep et on lance le timer
  # Si le step a une action, on lance la vue
  # A l interieur de la vue on envoie au FLASK la vue a lance et les attributs
  def stepToStart(self,json,index,dataToUse):
    step = json
    # print('---------- STEP DANS STEPTOSTART ------',step)
    # global indexFailure
    # global currentAction
    self.currentAction = step['action']
    if(step['action'] == 'confirm' and 'indexFailure' in step): 
      self.indexFailure = step['indexFailure']
    if step['action'] != '':
      Views.start(self,step['action'],step, index, dataToUse)
    else:
      dataJsonToSendCurrentStep = {
          "index": index,
          "step":step
      }
      socketIO.emit('stepCurrent',dataJsonToSendCurrentStep,broadcast=True)
      if step['id'] != 'FinishScenario':
        dataJsonToSendTimer = {
            "state": 'TOGGLE_TIMER/ON'
        }
        socketIO.emit('startTimer',dataJsonToSendTimer, broadcast=True)
      self.updateNextStep(index)

  
  def handle_sub(self,req):
    rospy.loginfo(req.data)
    self.pub_result.publish("salut")



  ####### On a en parametre, un json provenant du REACT qui contient la liste des steps ordonnees ainsi que le nom du scenario #########
  ####### On initialise le currentStep afin qu il ai le premier step de la liste
  ####### Le currentStep pointe sur une case du tableau de step, cette case varie en fonction de index grace a la fonction updateNextStep
  ####### On fait une boucle. Elle ne s arrete pas tant que le currentStep ne vaut pas le finalStep
  ####### On start le currentStep avec la fonction stepToStart
  def updateCurrentStep(self,json):
    # socketIO.wait(seconds=1)
    lastStep = None
    # global index
    # global currentStep
    # global dataToUse
    # global indexStepCompleted
    # global restart
    self.restart = 0
    if json['data'] != []:
      self.finalStep = json['data'][len(json['data']) - 1]
      self.currentStep = json['data'][self.index]
      while self.currentStep != self.finalStep and self.restart == 0:
        ############# STEP COMPLETED PUSH FOR RECEPTIONIST, on check si on arrive a la fin de l etape et on envoie
        ############# au REACT l index de l etape finie
        if self.currentStep['action'] == '' and self.currentStep['order'] != 0:
          print('on rentre dans step completed')
          stepCompletedJson = {"idSteps": self.indexStepCompleted}
          socketIO.emit('CompleteStep',stepCompletedJson,broadcast=True)
          self.indexStepCompleted = self.currentStep['order']

        if (self.currentStep != None and self.currentStep != lastStep):
          self.stepToStart(self.currentStep,self.index,self.dataToUse)
          lastStep=self.currentStep
        socketIO.wait(seconds=0.1)
        self.currentStep = json['data'][self.index]
    self.restart_hri({""})
  
  def updateNextStep(self,indexForNextStep):
    # global index
    self.index =indexForNextStep+1

  def updatePreviousStep(self,indexForPreviousStep):
    # global index
    # global indexFailure
    if(self.indexFailure != None):
      self.index =self.indexFailure
    else:
      self.index=indexForPreviousStep-1


  ########################## Chargement du scenario selectionne ################


  ######### On recoit depuis le REACT le nom du scenario selectionne et on charge le json approprie pour lui renvoyer ############
  def chargeScenario(self,json):
      # global dataJson
      ####
      # dataJson = self.load_scenario_json(json)
      # print(dataJson)
      ####
      # global socketIO
      choices = {self.receptionist['name']: self.receptionist, self.takeOutGarbage['name']: self.takeOutGarbage, self.inspection['name']: self.inspection, self.presentSchool['name']: self.presentSchool, self.creation['name']: self.creation}
      dataJson = choices.get(json['scenario'], 'default')
      dataJsonToSendScenario = {
        "scenario": dataJson['name'],
        "stepsList": dataJson['steps']
      }
      socketIO.emit('scenarioToCharged',dataJsonToSendScenario, broadcast=True)

  ######### On recoit les donnees que l utilisateur a entre et on appelle la fonction updateNextStep
  ######### La fonction updateNextStep change l index sur lequel currentStep est et met donc a jour le currentStep
  def dataJSstepDone(self,json):
    # global index
    # global dataToUse
    # global currentAction
    if(self.currentAction != 'confirm'):
      self.dataToUse = json['data']
    if(json['data'] != 'false'):
      self.updateNextStep(self.index)
    else:
      self.updatePreviousStep(self.index)
  ###########################


  def restart_hri(self,json):
    # global finalStep
    self.finalStep = None
    # global currentStep
    self.currentStep = None
    # global currentAction
    self.currentAction = None
    # global index
    self.index=0
    # global indexStepCompleted
    self.indexStepCompleted=0
    # global dataToUse
    self.dataToUse=''
    # global indexFailure
    self.indexFailure=None
    # global restart
    self.restart = 1
    socketIO.emit('restartHRI',broadcast=True)


  #############


  

if __name__ == '__main__':
  
  socketIO = SocketIO('http://127.0.0.1', 5000, LoggingNamespace)
  from python_depend.views import Views

  hri = HRIManager()
  socketIO.on('askToChangeScenarioHRIM', hri.chargeScenario)
  socketIO.on('scenarioCharged', hri.updateCurrentStep)
  socketIO.on('NextStep', hri.updateNextStep)
  socketIO.on('dataReceivedJS', hri.dataJSstepDone)
  socketIO.on('resetHRI', hri.restart_hri)

  while not rospy.is_shutdown():
    socketIO.wait(seconds=1)


# socketIO.wait(seconds=100)

