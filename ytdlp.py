import sys
import os
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
        print(f'Usage: {sys.argv[0]} [URL] [DRM] [format id] [output filename]')
        return
    
    '''
    #URL
    #URL format_id
    #URL format_id output_filename
    #URL DRM
    #URL DRM format_id
    #URL DRM format_id output_filename
    '''
    
    current_arg_index = 1
    # See help(yt_dlp.YoutubeDL) for a list of available options and public functions
    ydl_opts_dict: Dict[str, str] = {}
    target_url = sys.argv[current_arg_index]
    target_format_id = None
    allow_unplay_format = False
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
        if sys.argv[current_arg_index] in [ 'DRM', 'drm']:
            allow_unplay_format = True
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
    
    #4
    current_arg_index += 1
    if len(sys.argv) >= current_arg_index + 1:
        output_file_fullpath = sys.argv[current_arg_index]
        if output_folder:
            output_file_fullpath = output_folder + '/' + output_file_fullpath
        print(f'Output filename: {output_file_fullpath}')

    ydl_opts_dict['outtmpl'] = output_file_fullpath

    if allow_unplay_format:
        ydl_opts_dict['allow_unplayable_formats'] = True

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