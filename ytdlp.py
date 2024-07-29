import sys
import os
import re
from typing import Dict, Optional
import yt_dlp
import requests

VIDEO_AUDIO_EXT_MATCHING_MAP = {'mp4': 'm4a', 'webm': 'webm'}
REQUEST_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'}
CDRM_API = 'https://cdrm-project.com/'

class FormatMixer:
    def __init__(self, target_format_id : str, auto_mix_audio: bool = True):
        self.target_format_id = target_format_id
        self.auto_mix_audio = auto_mix_audio
        self.mixed_format_dict = {}

    def format_selector(self, ctx):
        final_format_id = self.target_format_id
        final_format_list = []
        final_ext = ''

        # formats are already sorted worst to best
        formats = ctx.get('formats')[::-1]

        target_format = next((f for f in formats if f['format_id'] == self.target_format_id), None)
        if target_format:
            final_ext = target_format['ext']
            final_format_list.append(target_format)

            # mix audio if (1) it is video (2) no audio (3) enable auto mixing
            if target_format['vcodec'] != 'none' and target_format['acodec'] == 'none' and self.auto_mix_audio:
                print(f'Try auto mixing audio ...')
                # find compatible audio extension
                matched_audio_ext = VIDEO_AUDIO_EXT_MATCHING_MAP[target_format['ext']]

                print(f'Matched audio ext: {matched_audio_ext}')

                # find best audio from list
                best_audio = next(f for f in formats if (f['acodec'] != 'none' and f['vcodec'] == 'none' and f['ext'] == matched_audio_ext))
                print(f'Best audio id found: {best_audio['format_id']}')

                final_format_list.append(best_audio)

                final_format_id = f'{final_format_id}+{best_audio["format_id"]}'
                print(f'Mixed format id: {final_format_id}')
        else:
            print(f'Format id not availble from source: {self.target_format_id}')
            raise FileNotFoundError(f'Format id not availble from source: {self.target_format_id}')
        
        self.mixed_format_dict = {
            'format_id': f'{final_format_id}',
            'requested_formats': final_format_list,
            'ext': final_ext
        }
        
        yield self.mixed_format_dict

    def get_mixed_format_dict(self) -> Dict[str, str]:
        return self.mixed_format_dict
    
def get_drm_key(mpd_url: str, license_url: str = None) -> Optional[str]:
    '''
    Didn't brother to dump can create own CDM, instead we use online service like https://cdrm-project.com and https://keysdb.net
    However, please noted that those services will cached your key (it's content decryption key correctly)

    Here is the guide to dump Android CDM
    https://forum.videohelp.com/threads/408031-Dumping-Your-own-L3-CDM-with-Android-Studio
    '''

    response = requests.get(mpd_url, headers=REQUEST_HEADERS)

    if response:
        matches = re.findall('<cenc:pssh xmlns:cenc="urn:mpeg:cenc:2013">([^<]+)</cenc:pssh>', response.text)
        if matches:
            pssh = matches[0]
            print(f'PSSH: {pssh}')

            if not license_url:
                print('No license server url is provided, so cannot get the key')
                return None
            
            json_data = {
                'PSSH': pssh,
                'License URL': license_url,
                'Headers': REQUEST_HEADERS,
                'JSON': {},
                'Cookies': {},
                'Data': {},
                'Proxy': ''
            }

            decryption_results = requests.post(CDRM_API, json=json_data)

            if decryption_results:
                return decryption_results.json()['Message']

            raise Exception(f"Non-success status code from CDRM service: {decryption_results.status_code}")
        else :
            raise Exception(f"Cannot parse pssh: {response.text}")
    else:
        raise Exception(f"Non-success status code: {response.status_code}")

def main():
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} [URL] [DRM] [format id] [output filename | license server url]')
        return
    
    '''
    #URL
    #URL format_id
    #URL format_id output_filename
    #URL DRM
    #URL DRM format_id license_server_url
    
    (
    as ytdlp will gives separated video and audio files on DRM content,
    so does not allow DRM + specify output filename, 
    hardcode filename is easier to handle
    )
    '''
    
    current_arg_index = 1
    # See help(yt_dlp.YoutubeDL) for a list of available options and public functions
    ydl_opts_dict: Dict[str, str] = {}
    target_url = sys.argv[current_arg_index]
    target_format_id = None
    allow_unplay_format = False
    license_server_url = None
    output_folder = os.environ['MEDIA_DIR']
    # ytdlp default format
    output_file_fullpath = '%(title)s [%(id)s].%(ext)s'
    if output_folder:
        output_file_fullpath = output_folder + '/' + output_file_fullpath

    print(f'URL: {target_url}')
    print(f'Output folder: {output_folder}')

    #2
    current_arg_index += 1
    if len(sys.argv) >= current_arg_index + 1:
        if sys.argv[current_arg_index] in ['DRM', 'drm']:
            allow_unplay_format = True
            output_file_fullpath = output_folder + '/drm_content'
        else:
            target_format_id = sys.argv[current_arg_index]

    #3
    current_arg_index += 1
    if len(sys.argv) >= current_arg_index + 1:
        # If no DRM arg, then must be filename
        if not allow_unplay_format:
            output_file_fullpath = sys.argv[current_arg_index]
            if output_folder:
                output_file_fullpath = output_folder + '/' + output_file_fullpath
            print(f'Output filename: {output_file_fullpath}')
        else:
            #else format_id
            target_format_id = sys.argv[current_arg_index]

    print(f'Target format id: {target_format_id}')

    ydl_opts_dict['outtmpl'] = output_file_fullpath

    if allow_unplay_format:
        ydl_opts_dict['allow_unplayable_formats'] = True

        # When specify DRM content, license server URL is required to getting the decryption key
        
        #4
        current_arg_index += 1
        if len(sys.argv) >= current_arg_index + 1:
            license_server_url = sys.argv[current_arg_index]
            print(f'License Server URL: {license_server_url}')

    with yt_dlp.YoutubeDL(ydl_opts_dict) as ydl:
        if target_format_id:
            # create auto audio mixer (mix best audio when target format is video only)
            format_mixer = FormatMixer(target_format_id, True)
            ydl.format_selector = format_mixer.format_selector

            #actual download
            print('Start download ...')
            ydl.download([target_url])

            # if target content is DRM protected, try get the key from online service after download
            if allow_unplay_format and target_url.strip().endswith('mpd'):
                print('DRM content require decryption')
                
                drm_key = get_drm_key(target_url, license_server_url)

                if drm_key:
                    print(f'DRM key: {drm_key}')
        else:
            #list formats
            print('List out all available formats ...')
            info_dict = ydl.extract_info(target_url, download=False)
            ydl.list_formats(info_dict)

if __name__ == '__main__':
    main()
