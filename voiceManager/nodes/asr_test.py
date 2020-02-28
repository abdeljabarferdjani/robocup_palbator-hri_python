#!/usr/bin/python

import os

import rospy
import time
from std_msgs.msg import String
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *
from statistics import mean 
from voiceManager.srv import SendVocalCommand
import json
from rapp_platform_ros_communications.srv import TextToSpeechSrv
from std_msgs.msg import Header
from HriManager.msg import DataToSay
import actionlib

import rapp_platform_ros_communications.msg


class ASRModule(object):
    """Class to add jsgf grammar functionality."""

    def __init__(self):

        # Initializing publisher with buffer size of 10 messages
        
        # initialize node
        rospy.init_node("asr_control")
        self.sub_mode_dictionary=rospy.Subscriber("CurrentView",DataToSay,self.handle_change_view)
        self.pub=rospy.Publisher("SendData",String,queue_size=10)

        self.dictionary_choose=None
        self.current_view_id=None
        self.current_view_action=None
        self.enable_publish_detection_output=None
        
        self.current_directory=os.path.dirname(os.path.realpath(__file__))
        # Call custom function on node shutdown
        rospy.on_shutdown(self.shutdown)
        
        self.client_action_tts=actionlib.SimpleActionClient("action_TTS",rapp_platform_ros_communications.msg.SayVocalSpeechAction)
        self.client_action_tts.wait_for_server()
        rospy.loginfo("Wait for current view reception ...")
        rospy.wait_for_message("CurrentView", String)
    


    def parser_view_action_to_dic_mode(self,view_action):
        dic_mode=""
        if view_action=="askAge":
            dic_mode="age"
            self.enable_publish_detection_output=False
        
        elif view_action=="askDrink":
            dic_mode="drinks"
            self.enable_publish_detection_output=True
        
        elif view_action=="askSomething":
            self.enable_publish_detection_output=False

        elif view_action=="askName":
            dic_mode="names"
            self.enable_publish_detection_output=True

        elif view_action=="confirm":
            dic_mode="confirmation"
            self.enable_publish_detection_output=True

        elif view_action==None:
            self.enable_publish_detection_output=False
        return dic_mode

    def publish_detection_output(self,detection_output):
        if self.enable_publish_detection_output==True and detection_output != "":
            json_output={u'dataToUse': detection_output, u'index': self.current_view_id}
            json_str=json.dumps(json_output)
            self.pub.publish(json_str)

    def handle_change_view(self,req):
        # data=req.data
        
        d=json.loads(req.json_in_string)
        dataToUse=req.data_to_use_in_string
        if self.current_view_id is None or self.current_view_id != d['order']:
            self.client_action_tts.cancel_all_goals()
            rospy.logwarn("KILLING ACTION REQUESTED")
            rospy.loginfo("--------")
            try:
                tts=d['speech']['said']
                # if tts and "{drink}" in tts:
                #     tts=tts.format(drink=dataToUse)
                # elif tts and "{name}" in tts:
                #     tts=tts.format(name=dataToUse)

            ###########################"
            # ACTION ESPEAK"

                goal=rapp_platform_ros_communications.msg.SayVocalSpeechGoal(tts)
                self.client_action_tts.send_goal(goal)
                # self.client_action_tts.wait_for_result()
                result_action=self.client_action_tts.get_result()
                rospy.loginfo("Action result "+str(result_action))


            # rospy.wait_for_service("/rapp/rapp_text_to_speech_espeak/text_to_speech_service")
            ##############################
            # SERVICE PYTTSX3
            # proxy_vocal_service=rospy.ServiceProxy('vocal_command_service',SendVocalCommand)
            # signal_output=proxy_vocal_service(tts)
            # rospy.loginfo('vocal service finished with signal :' +str(signal_output.output_signal))
            ##############################
            # 
            # SERVICE ESPEAK
            # header_tts=Header()
            # proxy_tts=rospy.ServiceProxy("/rapp/rapp_text_to_speech_espeak/text_to_speech_service",TextToSpeechSrv)
            # rospy.loginfo("TTS : "+tts)
            # output_tts=proxy_tts(header_tts,tts)
            # if output_tts.error =="":
            #     rospy.loginfo("TTS ended without errors")

            except:
                pass
            ###################################
            #   DECOMMENTER POUR SETUP DETECTION
            # view_id=d['order']
            # self.current_view_id=view_id

            # view_action=d['action']
            # self.current_view_action=view_action
            # self.dictionary_choose=self.parser_view_action_to_dic_mode(view_action)
            # if self.dictionary_choose != "":
            # 	rospy.loginfo("Load new dict config ...")
            #     self.setup_params()


    def setup_params(self):
        # Params

        # File containing language model
        _lm_param = "~lm"
        # Dictionary
        _dict_param = "~dict"
        # Hidden markov model. Default has been provided below
        _hmm_param = "~hmm"
        # Gram file contains the rules and grammar
        _gram = "~gram"
        # Name of rule within the grammar
        _rule = "~rule"

        _grammar = "~grammar"

        _database = "~database"
        # check if lm or grammar mode. Default = grammar
        self._use_lm = 0

        self.in_speech_bf = False

        # Setting param values
        if rospy.has_param(_hmm_param):
            self.hmm = rospy.get_param(_hmm_param)
            if rospy.get_param(_hmm_param) == ":default":
                if os.path.isdir("/usr/local/share/pocketsphinx/model"):
                    rospy.loginfo("Loading the default acoustic model")
                    self.hmm = "/usr/local/share/pocketsphinx/model/en-us/en-us"
                    rospy.loginfo("Done loading the default acoustic model")
                else:
                    rospy.logerr(
                        "No language model specified. Couldn't find default model.")
                    return
        else:
            rospy.logerr(
                "No language model specified. Couldn't find default model.")
            return

        if rospy.has_param(_dict_param) and rospy.get_param(_dict_param) != ":default":
            for dict_mode,dict_path in rospy.get_param(_dict_param).iteritems():
                print(dict_mode)
                print(dict_path)
                if dict_mode==self.dictionary_choose:
                    self.dict=self.current_directory+"/"+dict_path
                    rospy.loginfo("Loading "+str(dict_mode)+" dictionary file...")
                    rospy.loginfo("Dict path : "+str(dict_path))
        else:
            rospy.logerr(
                "No dictionary found. Please add an appropriate dictionary argument.")
            return

        if rospy.has_param(_grammar) and rospy.get_param(_grammar) != ":default":
            pass
        else:
            rospy.logerr(
                "No grammar found. Please add an appropriate grammar along with gram file.")
            return

        if rospy.has_param(_lm_param) and rospy.get_param(_lm_param) != ':default':
            self._use_lm = 1
            for lm_mode,lm_path in rospy.get_param(_lm_param).iteritems():
                if lm_mode==self.dictionary_choose:
                    self.class_lm=self.current_directory+"/"+lm_path
                    rospy.loginfo("Loading "+str(lm_mode)+" lm file...")
                    rospy.loginfo("LM path : "+str(lm_path))
        elif rospy.has_param(_gram) and rospy.has_param(_rule):
            self._use_lm = 0
            self.gram = rospy.get_param(_gram)
            self.rule = rospy.get_param(_rule)
        else:
            rospy.logerr(
                "Couldn't find suitable parameters. Please take a look at the documentation")
            return

        if rospy.has_param(_database):
            for database_mode,database_path in rospy.get_param(_database).iteritems():
                if database_mode==self.dictionary_choose:
                    file_database=open(self.current_directory+"/"+database_path,"r")
                    self.database_words=[]
                    
                    for line in file_database:
                        data=line.split("\n")[0]
                        data2=data.split("\t")
                        if len(data2)>1:
                            self.database_words.append([data2[0],float(data2[1])])
                        else:
                            self.database_words.append(data2[0])
                    file_database.close()
                    print(self.database_words)

        rospy.loginfo("ASR Module initialized ...")
        rospy.loginfo("Configuration Set : "+self.dictionary_choose)
        self.FAKE_POSITIVE=None
        # All params satisfied. Starting recognizer
        self.start_recognizer()

    def start_recognizer(self):
        """Function to handle lm or grammar processing of audio."""
        config = Decoder.default_config()
        rospy.loginfo("Done initializing pocketsphinx")

        # Setting configuration of decoder using provided params
        config.set_string('-hmm', self.hmm)
        config.set_string('-dict', self.dict)

        # Check if language model to be used or grammar mode
        if self._use_lm:
            rospy.loginfo('Language Model Found.')
            config.set_string('-lm', self.class_lm)
            self.decoder = Decoder(config)
        else:
            rospy.loginfo(
                'language model not found. Using JSGF grammar instead.')
            self.decoder = Decoder(config)

            # Switch to JSGF grammar
            jsgf = Jsgf(self.gram + '.gram')
            rule = jsgf.get_rule(rospy.get_param('~grammar') + '.' + self.rule)
            # Using finite state grammar as mentioned in the rule
            rospy.loginfo(rospy.get_param('~grammar') + '.' + self.rule)
            fsg = jsgf.build_fsg(rule, self.decoder.get_logmath(), 7.5)
            rospy.loginfo("Writing fsg to " +
                          self.gram + '.fsg')
            fsg.writefile(self.gram + '.fsg')

            self.decoder.set_fsg(self.gram, fsg)
            self.decoder.set_search(self.gram)

        # Start processing input audio
        self.decoder.start_utt()
        rospy.loginfo("Decoder started successfully")

        # Subscribe to audio topic
        rospy.Subscriber("jsgf_audio", String, self.process_audio)
        # rospy.spin()

    def process_audio(self, data):
        """Audio processing based on decoder config."""
        
        # Check if input audio has ended
        self.FAKE_POSITIVE=None
        self.decoder.process_raw(data.data, False, False)
        if self.decoder.get_in_speech() != self.in_speech_bf:
            self.in_speech_bf = self.decoder.get_in_speech()
            if not self.in_speech_bf:
                self.decoder.end_utt()
                if self.decoder.hyp() != None:
                    logmath=self.decoder.get_logmath()
                    rospy.loginfo([(seg.word, logmath.exp(seg.prob))for seg in self.decoder.seg()])
                    rospy.loginfo('OUTPUT: \"' + self.decoder.hyp().hypstr + '\"')
                    rospy.loginfo("DICT PATH  : "+str(self.dict))
                    rospy.loginfo('Score: ' + str(logmath.exp(self.decoder.hyp().best_score)))
                    self.score_detection=logmath.exp(self.decoder.hyp().best_score)
                    rospy.loginfo('Proba : '+str(logmath.exp(self.decoder.hyp().prob)))
                    self.output=self.decoder.hyp().hypstr


       ##########################  A DECOMMENTER POUR APPELER LE SERVICE TEXT TO SPEECH
                    # test_database=[]
                    # for word in self.database_words:
                    #     # WORD=word.upper()
                    #     if word[0]==self.output:
                    #         test_database.append(word[0])
                    #         break
                    # if len(test_database)>0:
                    #     rospy.loginfo("DETECTED WORD IS IN THE LIST")
                    #     self.FAKE_POSITIVE=False
                    # else:
                    #     rospy.loginfo("FAKE POSITIVE")
                    #     self.FAKE_POSITIVE=True
                    
                    self.FAKE_POSITIVE=True
                    for object in self.database_words:
                        if type(object) is list:
                            if object[0]==self.output:
                                self.FAKE_POSITIVE=False
                                detection_seuil=object[1]
                                break
                        else:
                            if object==self.output:
                                self.FAKE_POSITIVE=False
                                break
                    
                    # if self.FAKE_POSITIVE==False and self.score_detection>=detection_seuil:
                    #     if self.output=='NO':
                    #         self.publish_detection_output('false')
                    #     elif self.output=='YES':
                    #         self.publish_detection_output('true')
                    #     else:
                    #         self.publish_detection_output(self.output)
                    # elif self.FAKE_POSITIVE==True:
                    #     rospy.logwarn("WORD NOT IN DICT: "+self.output)
                    
                    # elif self.score_detection<detection_seuil:
                    #     rospy.logwarn("SEUIL TROP FAIBLE: "+str(round(self.score_detection,4))+" AU LIEU DE "+str(round(detection_seuil,4)))

                    ####################################################################
                    # PERMET DE STOCKER LES RESULTATS DES DETECTIONS POUR AFFINER LES SEUILS
                    if self.FAKE_POSITIVE==False:
                        if not os.path.exists("/home/student/Bureau/result_mic/"+self.dictionary_choose):
                            os.makedirs("/home/student/Bureau/result_mic/"+self.dictionary_choose)
                        file_result=open("/home/student/Bureau/result_mic/"+self.dictionary_choose+"/"+self.output+"_result.txt","a+")
                        file_result.write(self.output+"\t"+str(self.score_detection)+"\n")
                        file_result.close()
                    #######################################################################
        #########################
                self.decoder.start_utt()

    @staticmethod
    def shutdown():
        """This function is executed on node shutdown."""
        # command executed after Ctrl+C is pressed
        rospy.loginfo("Stop ASRControl")
        rospy.sleep(1)


if __name__ == "__main__":

    
    a=ASRModule()
    while not rospy.is_shutdown():
        rospy.spin()
