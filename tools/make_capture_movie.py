"""Mux the actual 15 Hz emulator video samples with their matching SPU audio."""
from pathlib import Path
import subprocess,sys,json
p=Path(sys.argv[1]);report=json.loads((p/'capture.json').read_text());frames=report['gif_samples']
assert frames>0
gifinfo=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(p/'gameplay.gif')]))
factor=(frames/15)/float(gifinfo['format']['duration'])
# GIF samples begin at emulator frame 300 (five seconds). Restore the total
# 15 Hz duration while retaining any identical frames coalesced by the GIF writer.
subprocess.run(['ffmpeg','-v','error','-y','-i',str(p/'gameplay.gif'),'-ss','5','-i',str(p/'audio.wav'),'-vf',f'setpts=PTS*{factor:.12f},fps=15','-frames:v',str(frames),'-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(p/'gameplay.mp4')],check=True)
r=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,size:stream=codec_type,nb_frames','-of','json',str(p/'gameplay.mp4')]))
assert {x['codec_type'] for x in r['streams']}=={'video','audio'}
assert abs(float(r['format']['duration'])-frames/15)<0.15
r['provenance']='actual emulator frames 300 onward, sampled every four frames; matching audio starts at five seconds'
(p/'movie_verification.json').write_text(json.dumps(r,indent=2));print('MP4 video/audio verified:',r['format'])
