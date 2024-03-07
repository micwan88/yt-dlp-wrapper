import sys
import json
import yt_dlp

def main():
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} URL')
        return
    
    target_url = sys.argv[1]

    # ℹ️ See help(yt_dlp.YoutubeDL) for a list of available options and public functions
    ydl_opts = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(target_url, download=False)
        
        ydl.list_formats(info_dict)

        # ydl.download()

if __name__ == '__main__':
    main()