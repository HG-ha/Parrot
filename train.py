import sys
import os
import uuid
sys.path.append('third_party/Matcha-TTS')
from cosyvoice.cli.cosyvoice import CosyVoice2
from cosyvoice.utils.file_utils import load_wav
import torchaudio
import glob
import requests
import uuid
import mlog
from pydub import AudioSegment
from static_ffmpeg import add_paths
add_paths()


def clear_cache():
    input_files = glob.glob('input/*')
    output_files = glob.glob('output/*')

    for f in input_files + output_files:
        try:
            os.remove(f)
        except OSError as e:
            print(f"Error: {f} : {e.strerror}")
            mlog.error(f"Error: {f} : {e.strerror}")


def download_file(download_url: str):
    try:
        response = requests.get(download_url)
        response.raise_for_status()
        os.makedirs('input', exist_ok=True)
        file_path = os.path.join('input', f'{uuid.uuid4()}.mp3')
        with open(file_path, 'wb') as f:
            f.write(response.content)
        mlog.info(f"Downloaded file from {download_url} to {file_path}")
        return True, file_path
    except Exception as e:
        return False, str(e)


class CosyVoiceWrapper:
    def __init__(self, model_path, load_jit=False, load_trt=False, fp16=True):
        self.cosyvoice = CosyVoice2(model_path, load_jit=load_jit, load_trt=load_trt, fp16=fp16)

    # 3s极速推理，需要输入音频的文本内容
    def inference_zero_shot(self, text, speaker, prompt_speech_path_or_url, output_path='output', speed=1.0, stream=False):
        try:
            if prompt_speech_path_or_url.startswith('http'):
                success, prompt_speech_path = download_file(prompt_speech_path_or_url)
                if not success:
                    return False, prompt_speech_path
            else:
                prompt_speech_path = prompt_speech_path_or_url

            prompt_speech = load_wav(prompt_speech_path, 16000)
            os.makedirs(output_path, exist_ok=True)
            files = []
            for i, j in enumerate(self.cosyvoice.inference_zero_shot(text, speaker, prompt_speech, speed=speed, stream=stream)):
                file_name = f'zero_shot_{uuid.uuid4()}.wav'
                file_path = os.path.join(output_path, file_name)
                torchaudio.save(file_path, j['tts_speech'], self.cosyvoice.sample_rate)
                files.append(file_path)
                
            combined = AudioSegment.empty()
            for file in files:
                combined += AudioSegment.from_wav(file)
            
            combined_file_path = os.path.join(output_path, f'combined_{uuid.uuid4()}.wav')
            combined.export(combined_file_path, format='wav')
                
            return True, combined_file_path
        except Exception as e:
            return False, str(e)

    # 快速推理，直接根据文本内容生成音频
    def inference_cross_lingual(self, text, prompt_speech_path_or_url, output_path='output', speed=1.0, stream=False):
        try:
            if prompt_speech_path_or_url.startswith('http'):
                success, prompt_speech_path = download_file(prompt_speech_path_or_url)
                if not success:
                    return False, prompt_speech_path
            else:
                prompt_speech_path = prompt_speech_path_or_url

            prompt_speech = load_wav(prompt_speech_path, 16000)
            os.makedirs(output_path, exist_ok=True)
            files = []
            for i, j in enumerate(self.cosyvoice.inference_cross_lingual(text, prompt_speech, speed=speed, stream=stream)):
                file_name = f'fine_grained_control_{uuid.uuid4()}.wav'
                file_path = os.path.join(output_path, file_name)
                torchaudio.save(file_path, j['tts_speech'], self.cosyvoice.sample_rate)
                files.append(file_path)
                
            combined = AudioSegment.empty()
            for file in files:
                combined += AudioSegment.from_wav(file)
            
            combined_file_path = os.path.join(output_path, f'combined_{uuid.uuid4()}.wav')
            combined.export(combined_file_path, format='wav')
                
            return True, combined_file_path
        except Exception as e:
            return False, str(e)

    # 控制自然语言
    def inference_instruct(self, text, instruction, prompt_speech_path_or_url, output_path='output', speed=1.0, stream=False):
        try:
            if prompt_speech_path_or_url.startswith('http'):
                success, prompt_speech_path = download_file(prompt_speech_path_or_url)
                if not success:
                    return False, prompt_speech_path
            else:
                prompt_speech_path = prompt_speech_path_or_url

            prompt_speech = load_wav(prompt_speech_path, 16000)
            os.makedirs(output_path, exist_ok=True)
            files = []
            for i, j in enumerate(self.cosyvoice.inference_instruct2(text, instruction, prompt_speech, speed=speed, stream=stream)):
                file_name = f'instruct_{uuid.uuid4()}.wav'
                file_path = os.path.join(output_path, file_name)
                torchaudio.save(file_path, j['tts_speech'], self.cosyvoice.sample_rate)
                files.append(file_path)
                
            combined = AudioSegment.empty()
            for file in files:
                combined += AudioSegment.from_wav(file)
            
            combined_file_path = os.path.join(output_path, f'combined_{uuid.uuid4()}.wav')
            combined.export(combined_file_path, format='wav')
                
            return True, combined_file_path
        except Exception as e:
            return False, str(e)
    
    # 自动处理生成类型
    def auto_inference(self, params):
        if params.prompt is not None:
            success,filepath = self.inference_zero_shot(params.text,speaker=params.prompt,prompt_speech_path_or_url=str(params.source_url), speed=params.speed)
        elif params.language_control is not None:
            success,filepath = self.inference_instruct(params.text, params.language_control, prompt_speech_path_or_url=str(params.source_url), speed=params.speed)
        else:
            success,filepath = self.inference_cross_lingual(params.text,prompt_speech_path_or_url=str(params.source_url), speed=params.speed)
        
        return success,filepath

    def test_model(self):
        if self.cosyvoice is not None:
            return True
        return False
