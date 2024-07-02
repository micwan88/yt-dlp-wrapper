import sys
from typing import Dict
import yt_dlp

class FormatMixer:
    def __init__(self, target_format_id : str, auto_mix_audio: bool = True):
        self.target_format_id = target_format_id
        self.auto_mix_audio = auto_mix_audio

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
                matched_audio_ext = {'mp4': 'm4a', 'webm': 'webm'}[target_format['ext']]

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
        
        yield {
            'format_id': f'{final_format_id}',
            'requested_formats': final_format_list,
            'ext': final_ext
        }

def main():
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} [URL] [output filename]')
        return
    
    # See help(yt_dlp.YoutubeDL) for a list of available options and public functions
    ydl_opts_dict: Dict[str, str] = {}
    target_url = sys.argv[1]
    target_format_id = None

    print(f'URL: {target_url}')

    if len(sys.argv) >= 3:
        target_format_id = sys.argv[2]

    print(f'Target format id: {target_format_id}')
    
    if len(sys.argv) >= 4:
        ydl_opts_dict['outtmpl'] = sys.argv[3]
        print(f'Output filename: {sys.argv[3]}')

    with yt_dlp.YoutubeDL(ydl_opts_dict) as ydl:
        if target_format_id:
            # create auto audio mixer (mix best audio when target format is video only)
            format_mixer = FormatMixer(target_format_id, True)
            ydl.format_selector = format_mixer.format_selector

            #actual download
            print('Start download ...')
            ydl.download([target_url])
        else:
            #list formats
            print('List out all available formats ...')
            info_dict = ydl.extract_info(target_url, download=False)
            ydl.list_formats(info_dict)

if __name__ == '__main__':
    main()