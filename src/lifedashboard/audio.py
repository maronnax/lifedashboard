# SAMPLE CODE FOR AUDIO

# def audioInput(self, msg):
#     import speech_recognition as sr

#     r = sr.Recognizer()
#     m = sr.Microphone()

#     with m as source:
#         r.adjust_for_ambient_noise(source)
#         try:
#             audio = r.listen(source)
#             value = r.recognize_google(audio)
#             # we need some special handling here to correctly print unicode characters to standard output
#             if str is bytes: # this version of Python uses bytes for strings (Python 2)
#                 conv_val = "{0}".format(value).encode("utf-8")
#             else: # this version of Python uses unicode for strings (Python 3+)
#                 conv_val = value
#         except LookupError:
#             conv_val = ""
#     return conv_val
