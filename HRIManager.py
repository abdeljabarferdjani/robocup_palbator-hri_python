from socketIO_client import SocketIO, LoggingNamespace
import json

if __name__ == '__main__':
 socketIO = SocketIO('http://127.0.0.1', 5000, LoggingNamespace)

from views import Views

######### SCENARIO JSON LOAD #############
# Test push


  
with open('templates/public/json/present_school_test/scenario.json') as pres_school:
    presentSchool = json.load(pres_school)
    presentSchool['name']='present_school'

with open('templates/public/json/creation_test/scenario.json') as creationTest:
    creation = json.load(creationTest)
    creation['name']='creation_test'

with open('templates/public/json/inspection/scenario.json') as inspec:
    inspection = json.load(inspec)
    inspection['name']='inspection'

with open('templates/public/json/take_out_the_garbage/scenario.json') as take_garbage:
    takeOutGarbage = json.load(take_garbage)
    takeOutGarbage['name']='take_out_the_garbage'

with open('templates/public/json/receptionist/scenario.json') as recep:
    receptionist = json.load(recep)
    receptionist['name']='receptionist'

finalStep = None
currentStep = None
currentAction = None
index=0
indexStepCompleted=0
dataToUse=''
indexFailure=None
restart=0
print("index global",index)
  
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
    pass  
  ##########
  # On a le current step en json et son index afin de start la vue approprie
  # Si le step n a pas d action, c est que c est le titre d une etape.
  # Dans ce cas la, on update l etat de currentStep et on lance le timer
  # Si le step a une action, on lance la vue
  # A l interieur de la vue on envoie au FLASK la vue a lance et les attributs
  def stepToStart(self,json,index,dataToUse):
    step = json
    # print('---------- STEP DANS STEPTOSTART ------',step)
    global indexFailure
    global currentAction
    currentAction = step['action']
    if(step['action'] == 'confirm' and 'indexFailure' in step): 
      indexFailure = step['indexFailure']
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

    

  ####### On a en parametre, un json provenant du REACT qui contient la liste des steps ordonnees ainsi que le nom du scenario #########
  ####### On initialise le currentStep afin qu il ai le premier step de la liste
  ####### Le currentStep pointe sur une case du tableau de step, cette case varie en fonction de index grace a la fonction updateNextStep
  ####### On fait une boucle. Elle ne s arrete pas tant que le currentStep ne vaut pas le finalStep
  ####### On start le currentStep avec la fonction stepToStart
  def updateCurrentStep(self,json):
    # socketIO.wait(seconds=1)
    lastStep = None
    global index
    global currentStep
    global dataToUse
    global indexStepCompleted
    global restart
    restart = 0
    if json['data'] != []:
      finalStep = json['data'][len(json['data']) - 1]
      currentStep = json['data'][index]
      while currentStep != finalStep and restart == 0:
        ############# STEP COMPLETED PUSH FOR RECEPTIONIST, on check si on arrive a la fin de l etape et on envoie
        ############# au REACT l index de l etape finie
        if currentStep['action'] == '' and currentStep['order'] != 0:
          print('on rentre dans step completed')
          stepCompletedJson = {"idSteps": indexStepCompleted}
          socketIO.emit('CompleteStep',stepCompletedJson,broadcast=True)
          indexStepCompleted = currentStep['order']

        if (currentStep != None and currentStep != lastStep):
          self.stepToStart(currentStep,index,dataToUse)
          lastStep=currentStep
        socketIO.wait(seconds=0.1)
        currentStep = json['data'][index]
    self.restart_hri({""})
  
  def updateNextStep(self,indexForNextStep):
    global index
    index =indexForNextStep+1

  def updatePreviousStep(self,indexForPreviousStep):
    global index
    global indexFailure
    if(indexFailure != None):
      index =indexFailure
    else:
      index=indexForPreviousStep-1


  ########################## Chargement du scenario selectionne ################


  ######### On recoit depuis le REACT le nom du scenario selectionne et on charge le json approprie pour lui renvoyer ############
  def chargeScenario(self,json):
      global dataJson
      ####
      # dataJson = self.load_scenario_json(json)
      # print(dataJson)
      ####
      choices = {receptionist['name']: receptionist, takeOutGarbage['name']: takeOutGarbage, inspection['name']: inspection, presentSchool['name']: presentSchool, creation['name']: creation}
      dataJson = choices.get(json['scenario'], 'default')
      dataJsonToSendScenario = {
        "scenario": dataJson['name'],
        "stepsList": dataJson['steps']
      }
      socketIO.emit('scenarioToCharged',dataJsonToSendScenario, broadcast=True)

  ######### On recoit les donnees que l utilisateur a entre et on appelle la fonction updateNextStep
  ######### La fonction updateNextStep change l index sur lequel currentStep est et met donc a jour le currentStep
  def dataJSstepDone(self,json):
    global index
    global dataToUse
    global currentAction
    if(currentAction != 'confirm'):
      dataToUse = json['data']
    if(json['data'] != 'false'):
      self.updateNextStep(index)
    else:
      self.updatePreviousStep(index)
  ###########################


  def restart_hri(self,json):
    global finalStep
    finalStep = None
    global currentStep
    currentStep = None
    global currentAction
    currentAction = None
    global index
    index=0
    global indexStepCompleted
    indexStepCompleted=0
    global dataToUse
    dataToUse=''
    global indexFailure
    indexFailure=None
    global restart
    restart = 1
    socketIO.emit('restartHRI',broadcast=True)


  #############

hri = HRIManager()

socketIO.on('askToChangeScenarioHRIM', hri.chargeScenario)
socketIO.on('scenarioCharged', hri.updateCurrentStep)
socketIO.on('NextStep', hri.updateNextStep)
socketIO.on('dataReceivedJS', hri.dataJSstepDone)
socketIO.on('resetHRI', hri.restart_hri)

socketIO.wait(seconds=100)

