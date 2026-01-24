from story_genius.gui.voice_module import VoiceModule
import edge_tts
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

def run_async_func(loop, func):
    return loop.run_until_complete(func)

class EdgeTTSVoiceModule(VoiceModule):
    def __init__(self, voiceName="en-AU-WilliamNeural"):
        self.voiceName = voiceName
        super().__init__()

    def generate_voice(self, text, outputfile):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            with ThreadPoolExecutor() as executor:
                loop.run_in_executor(executor, run_async_func, loop, self.async_generate_voice(text, outputfile))
        finally:
            loop.close()
            
        if not os.path.exists(outputfile):
            raise Exception("EdgeTTS failed to generate audio file.")
        return outputfile

    async def async_generate_voice(self, text, outputfile):
        communicate = edge_tts.Communicate(text, self.voiceName)
        await communicate.save(outputfile)
        return outputfile
