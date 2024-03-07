import sys
from typing import Dict
import yt_dlp

def main():
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} [URL] [format id] [output filename]')
        return
    
    # ℹ️ See help(yt_dlp.YoutubeDL) for a list of available options and public functions
    ydl_opts_dict: Dict[str, str] = {}
    target_url = sys.argv[1]

    print(f'URL: {target_url}')

    if len(sys.argv) >= 3:
        ydl_opts_dict['format'] = sys.argv[2]
        print(f'Target format: {sys.argv[2]}')
    
    if len(sys.argv) >= 4:
        ydl_opts_dict['outtmpl'] = sys.argv[3]
        print(f'Output filename: {sys.argv[3]}')

    with yt_dlp.YoutubeDL(ydl_opts_dict) as ydl:
        target_format = ydl_opts_dict.get('format')
        if target_format:
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