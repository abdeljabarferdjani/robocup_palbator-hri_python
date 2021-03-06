#!/usr/bin/python

from time import sleep

import pyaudio

import rospy

from std_msgs.msg import String


class AudioMessage(object):
    """Class to publish audio to topic"""

    def __init__(self):

        # Initializing publisher with buffer size of 10 messages
        self.pub_ = rospy.Publisher("sphinx_audio", String, queue_size=10)

        # initialize node
        rospy.init_node("audio_control",anonymous=True)
        # Call custom function on node shutdown
        rospy.on_shutdown(self.shutdown)

        # All set. Publish to topic
        self.transfer_audio_msg()

    def transfer_audio_msg(self):
        """Function to publish input audio to topic"""

        rospy.loginfo("audio input node will start after delay of 5 seconds")
        sleep(5)

        # Params
        self._input = "~input"
        _rate_bool = False

        pa=pyaudio.PyAudio()
        stream=None
        # Checking if audio file given or system microphone is needed
        if rospy.has_param(self._input):
            if rospy.get_param(self._input) != ":default":
                _rate_bool = True
                stream = open(rospy.get_param(self._input), 'rb')
                rate = rospy.Rate(5) # 10hz
            else:
                for i in range(pa.get_device_count()):
                    dev = pa.get_device_info_by_index(i)
                    # if dev.get('name')=='USB Audio CODEC: - (hw:1,0)':
                # Initializing pyaudio for input from system microhpone
                    #stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, input_device_index=7, frames_per_buffer=1024)
                    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
                    stream.start_stream()
                    # rospy.logwarn("STREAM OPEN")
                        

                if stream is None:
                    stream = pa.open(format=pyaudio.paInt16, channels=1,
                                                        rate=16000, input=True, frames_per_buffer=1024)
                    stream.start_stream()
                    rospy.logwarn("No mic CODEC device found")
        else:
            rospy.logerr("No input means provided. Please use the launch file instead")


        while not rospy.is_shutdown():
            buf = stream.read(1024)
            if buf:
                # Publish audio to topic
                self.pub_.publish(buf)
                # rospy.logwarn("PUBLISHING STREAM")
		#rospy.logwarn("jbeefibzibuizbvuizevr : config default : "+str(pa.get_default_input_device_info()))
                if _rate_bool:
                    rate.sleep()
            else:
                rospy.loginfo("Buffer returned null")
                break

    @staticmethod
    def shutdown():
        """This function is executed on node shutdown."""
        # command executed after Ctrl+C is pressed
        rospy.loginfo("Stop ASRControl")
        rospy.sleep(1)


if __name__ == "__main__":
    AudioMessage()
