from socketIO_client import SocketIO, LoggingNamespace
import json

if __name__ == '__main__':
 socketIO = SocketIO('http://127.0.0.1', 5000, LoggingNamespace)

from views import Views

######### SCENARIO JSON LOAD #############


  
with open('templates/public/json/present_school/scenario.json') as pres_school:
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

def load_scenario_json(json):
  name_scenario = json['scenario']
  print('nom du scenario',name_scenario)
  path_scenario_json = '/Users/abdeljabarferdjani/Documents/Robocup/Flask/templates/public/json/receptionist/scenario.json'
  print('nom du path',path_scenario_json)
  with open(path_scenario_json) as scenar:
    # print(scenar)
    chargedScenario = json.load(scenar) ## essayer avec loads
    print(chargedScenario)
#   # return chargedScenario
  
##########

finalStep = None
currentStep = None
index=0
indexStepCompleted=0
dataToUse=''
print("index global",index)

####### On a en parametre, un json provenant du REACT qui contient la liste des steps ordonnees ainsi que le nom du scenario #########
####### On initialise le currentStep afin qu il ai le premier step de la liste
####### Le currentStep pointe sur une case du tableau de step, cette case varie en fonction de index grace a la fonction updateNextStep
####### On fait une boucle. Elle ne s arrete pas tant que le currentStep ne vaut pas le finalStep
####### On start le currentStep avec la fonction stepToStart
def updateCurrentStep(json):
  # socketIO.wait(seconds=1)
  lastStep = None
  global index
  global currentStep
  global dataToUse
  global indexStepCompleted
  if json['data'] != []:
    finalStep = json['data'][len(json['data']) - 1]
    currentStep = json['data'][index]
    while currentStep != finalStep:
      ############# STEP COMPLETED PUSH FOR RECEPTIONIST, on check si on arrive a la fin de l etape et on envoie
      ############# au REACT l index de l etape finie
      if currentStep['action'] == '' and currentStep['order'] != 0:
        stepCompletedJson = {"idSteps": indexStepCompleted}
        socketIO.emit('CompleteStep',stepCompletedJson,broadcast=True)
        indexStepCompleted = currentStep['order']

      if (currentStep != None and currentStep != lastStep):
        stepToStart(currentStep,index,dataToUse)
        lastStep=currentStep
      socketIO.wait(seconds=0.1)
      currentStep = json['data'][index]

  # dataJsonToSendScenario = {
  #     "scenario": 'None',
  #     "stepsList": []
  # }
  # socketIO.emit('scenarioToEnd',dataJsonToSendScenario, broadcast=True)
  # # global index
  # finalStep = None
  # currentStep = None
  # index=0
  # indexStepCompleted=0
  # dataToUse=''


def updateNextStep(indexForNextStep):
  global index
  index =indexForNextStep+1

def updatePreviousStep(indexForPreviousStep):
  global index
  index =indexForPreviousStep-1

# On a le current step en json et son index afin de start la vue approprie
# Si le step n a pas d action, c est que c est le titre d une etape.
# Dans ce cas la, on update l etat de currentStep et on lance le timer
# Si le step a une action, on lance la vue
# A l interieur de la vue on envoie au FLASK la vue a lance et les attributs

def stepToStart(json,index,dataToUse):
  step = json
  # print('---------- STEP DANS STEPTOSTART ------',step)
  if step['action'] != '':
    Views.start(step['action'],step, index, dataToUse)
  else:
    dataJsonToSendCurrentStep = {
        "index": index,
        "step":step
    }
    socketIO.emit('stepCurrent',dataJsonToSendCurrentStep,broadcast=True)
    dataJsonToSendTimer = {
        "state": 'TOGGLE_TIMER/ON'
    }
    socketIO.emit('startTimer',dataJsonToSendTimer, broadcast=True)
    updateNextStep(index)

########################## Chargement du scenario selectionne ################


######### On recoit depuis le REACT le nom du scenario selectionne et on charge le json approprie pour lui renvoyer ############
def chargeScenario(json):
    global dataJson
    ####
    # dataJson = load_scenario_json(json)
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
def dataJSstepDone(json):
  global index
  global dataToUse
  dataToUse = json['data']
  print(dataToUse)
  if(dataToUse != 'false' ):
    updateNextStep(index)
  else:
    updatePreviousStep(index)
###########################

socketIO.on('askToChangeScenarioHRIM', chargeScenario)
socketIO.on('scenarioCharged', updateCurrentStep)
socketIO.on('NextStep', updateNextStep)
socketIO.on('dataReceivedJS', dataJSstepDone)

socketIO.wait(seconds=100)

