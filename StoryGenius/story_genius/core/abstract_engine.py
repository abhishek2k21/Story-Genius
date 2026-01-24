import os
from abc import ABC, abstractmethod
from story_genius.gui.voice_module import VoiceModule # Placeholder
# from story_genius.config.languages import Language # Placeholder

class AbstractContentEngine(ABC):
    def __init__(self, content_type: str, voiceModule=None):
        self.content_type = content_type
        self.voiceModule = voiceModule
        self.stepDict = {}
        self.logger = lambda x: print(x)
        self.dynamicAssetDir = f".story_assets/{content_type}/{os.getpid()}/"
        if not os.path.exists(self.dynamicAssetDir):
            os.makedirs(self.dynamicAssetDir)

    def verifyParameters(self, **kargs):
        for key, value in kargs.items():
            if not value:
                raise Exception(f"Parameter {key} is null or empty")

    def makeContent(self):
        total_steps = len(self.stepDict)
        for currentStep, step_func in sorted(self.stepDict.items()):
            yield currentStep, f"Step {currentStep}/{total_steps}: {step_func.__name__}"
            if self.logger:
                self.logger(f"Executing Step {currentStep}: {step_func.__name__}")
            step_func()

    def get_video_output_path(self):
        return getattr(self, "_video_output_path", None)
    
    def set_logger(self, logger):
        self.logger = logger
