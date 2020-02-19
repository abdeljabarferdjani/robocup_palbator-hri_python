#!/usr/bin/python

import os

import rospy
import time
from std_msgs.msg import String
from pocketsphinx.pocketsphinx import *
import sphinxbase
from statistics import mean 
from own_speech_recognition.srv import SendVocalCommand
from own_speech_recognition.msg import VocalDataType



class ASRModule(object):
    """Class to add jsgf grammar functionality."""

    def __init__(self):

        # Initializing publisher with buffer size of 10 messages
        
        # initialize node
        rospy.init_node("asr_control")
        self.sub_mode_dictionary=rospy.Subscriber("mode_dictionary",String,self.handle_change_mode_dictionary)
        self.pub=rospy.Publisher("test_dict_mode",String,queue_size=10)
        self.dictionary_choose=None

        # Call custom function on node shutdown
        rospy.on_shutdown(self.shutdown)
        rospy.loginfo("Wait for dict mode reception ...")
        rospy.wait_for_message("mode_dictionary", String)
    


    def handle_change_mode_dictionary(self,req):
        if self.dictionary_choose is None:
            self.dictionary_choose=req.data
            rospy.loginfo("Load new dict config ...")
            self.setup_params()
        elif self.dictionary_choose != req.data:
            self.dictionary_choose=req.data
            rospy.loginfo("Load new dict config ...")
            self.setup_params()


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
                    self.dict=dict_path
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
                    self.class_lm=lm_path
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
                    file_database=open(database_path,"r")
                    self.database_words=[]
                    for line in file_database:
                        data=line.split("\t")[0]
                        self.database_words.append(data)
                    file_database.close()
                    # print(self.database_words)

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
                    test_database=[]
                    for word in self.database_words:
                        WORD=word.upper()
                        if WORD==self.output:
                            test_database.append(WORD)
                            break
                    if len(test_database)>0:
                        rospy.loginfo("DETECTED WORD IS IN THE LIST")
                        self.FAKE_POSITIVE=False
                    else:
                        rospy.loginfo("FAKE POSITIVE")
                        self.FAKE_POSITIVE=True
                    
                    if self.FAKE_POSITIVE==False:
                        message=VocalDataType()
                        message.vocal_output=self.decoder.hyp().hypstr
                        message.data_type=self.dictionary_choose
                        rospy.wait_for_service('vocal_command_service')
                        rospy.loginfo('vocal service initialized')
                        try:
                            proxy_vocal_service=rospy.ServiceProxy('vocal_command_service',SendVocalCommand)
                            if self.score_detection>=0.65:
                                signal_output=proxy_vocal_service(message)
                                rospy.loginfo('vocal service finished with signal :' +str(signal_output.output_signal))
                                time.sleep(2)
                        except rospy.ServiceException, e:
                            print "Service call failed: %s"%e
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
