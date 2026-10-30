"""Run a software libretro PS1 core and save actual emulator video frames.
Usage: python capture_libretro.py CORE CONTENT OUTPUT_DIR
No retail BIOS bundled: this checkpoint uses PCSX-ReARMed HLE.
"""
import ctypes as C,sys,json,hashlib,struct,wave,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
scenario=json.loads(Path(sys.argv[4]).read_text()) if len(sys.argv)>4 else {}
run_frames=scenario.get('frames',720);shots=scenario.get('shots',[239,359,399,445,475,599,719])
sample_interval=scenario.get('sample_interval',30)
if not isinstance(sample_interval,int) or sample_interval<1:raise ValueError('sample_interval must be a positive integer')
gif_start=scenario.get('gif_start_frame',300);gif_end=scenario.get('gif_end_frame',run_frames);gif_step=scenario.get('gif_sample_step',4)
if not isinstance(gif_step,int) or gif_step<1:raise ValueError('gif_sample_step must be a positive integer')
core=C.CDLL(str(Path(sys.argv[1]).resolve()));out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
class Var(C.Structure):_fields_=[('key',C.c_char_p),('value',C.c_char_p)]
class Game(C.Structure):_fields_=[('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]
ENV=C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p);VID=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t);AUDIO=C.CFUNCTYPE(None,C.c_int16,C.c_int16);BATCH=C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t);POLL=C.CFUNCTYPE(None);INPUT=C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint)
ram=0;symbols={};movement_stopped=False
corridor_jump_held=False
corridor_second_jump_held=False
corridor_checkpoint_phase=0;corridor_third_jump_sent=False;corridor_fourth_jump_sent=False;corridor_checkpoint_jump_until=-1
options={};keep=[];fmt=0;frame=None;tick=0;audio_writer=None;audio_count=0;audio_peak=0;audio_energy=0;audio_clips=0;audio_written=0
folder=str(out.resolve()).encode();keep.append(folder)
@ENV
def env(cmd,data):
 global fmt
 if cmd in (9,31,30):C.cast(data,C.POINTER(C.c_char_p))[0]=folder;return True
 if cmd==10:fmt=C.cast(data,C.POINTER(C.c_int))[0];return True
 if cmd==3:C.cast(data,C.POINTER(C.c_bool))[0]=True;return True
 if cmd==15:
  v=C.cast(data,C.POINTER(Var)).contents
  if v.key==b'pcsx_rearmed_bios':v.value=b'HLE';return True
  if v.key in options:v.value=options[v.key];return True
  return False
 if cmd==16:
  a=C.cast(data,C.POINTER(Var));i=0
  while a[i].key:
   options[a[i].key]=a[i].value.split(b'; ',1)[-1].split(b'|')[0];i+=1
  return True
 if cmd==17:C.cast(data,C.POINTER(C.c_bool))[0]=False;return True
 if cmd==52:C.cast(data,C.POINTER(C.c_uint))[0]=0;return True
 if cmd in (18,24,27,35,36,37,44,53,55,62):return False
 return False
@VID
def video(data,w,h,pitch):
 global frame
 if not data or data==C.c_void_p(-1).value:return
 b=C.string_at(data,pitch*h)
 if fmt==1:
  v=np.frombuffer(b,np.uint8).reshape(h,pitch)[:,:w*4].reshape(h,w,4);frame=Image.fromarray(v[:,:,[2,1,0]].copy())
 else:
  a=np.frombuffer(b,np.uint16).reshape(h,pitch//2)[:,:w].astype(np.uint32)
  if fmt==2:r=((a>>11)&31)*255//31;g=((a>>5)&63)*255//63;b=(a&31)*255//31
  else:r=((a>>10)&31)*255//31;g=((a>>5)&31)*255//31;b=(a&31)*255//31
  frame=Image.fromarray(np.stack([r,g,b],-1).astype(np.uint8))
def write_audio(data,n):
 global audio_count,audio_peak,audio_energy,audio_clips,audio_written
 samples=np.frombuffer(data,dtype='<i2').astype(np.int32);audio_count+=len(samples)
 if len(samples):audio_peak=max(audio_peak,int(np.abs(samples).max()));audio_energy+=int(np.sum(samples.astype(np.int64)**2));audio_clips+=int(np.count_nonzero(np.abs(samples)>=32767))
 start=scenario.get('audio_start_frame',0)*1470
 if audio_writer and audio_count>start:
  skip=max(0,start-(audio_count-len(samples)));chunk=data[skip*2:]
  audio_writer.write(chunk);audio_written+=len(chunk)
@AUDIO
def audio(l,r):write_audio(struct.pack('<hh',l,r),1)
@BATCH
def batch(data,n):
 if data and n:write_audio(C.string_at(data,n*4),n)
 return n
@POLL
def poll():pass
@INPUT
def inp(port,device,index,id):
 global movement_stopped,corridor_jump_held,corridor_second_jump_held,corridor_checkpoint_phase,corridor_third_jump_sent,corridor_fourth_jump_sent,corridor_checkpoint_jump_until
 if port:return 0
 # Scenario feedback changes controller input only; never write emulated RAM.
 if scenario.get('frontend_auto_start') and 450<=tick<scenario.get('frontend_auto_start_end',1000000000) and ram and 'frontend' in symbols:
  screen=C.c_int.from_address(ram+symbols['frontend']).value
  if screen in (0,1):return int(id==0 and (tick//15)%2==0)

 if scenario.get('levium_route') and 1000<=tick<scenario.get('levium_route_until',18000) and ram and 'npc_dialogue' in symbols and id in (0,4,5,6,7,9):
  phase,page,visited,completions,prompt=struct.unpack('<5i',C.string_at(ram+symbols['npc_dialogue'],20))
  if 'frontend' in symbols and C.c_int.from_address(ram+symbols['frontend']).value!=2:return 0
  if completions>=scenario.get('levium_target_completions',2):return 0
  if phase==1:return 0
  if phase==2:return int(id==0 and tick%180<8)
  if prompt:return int(id==9 and tick%24<8)
  x,z=C.c_int.from_address(ram+symbols['player']).value/256,C.c_int.from_address(ram+symbols['player']+8).value/256
  return int((id==4 and x<4910) or (id==6 and x>4500 and z<230) or (id==7 and x>4500 and z>240))
 if 'stream_jump_start' in scenario and ram and 'player' in symbols and id==0 and tick>=1000:
  axis=scenario.get('stream_jump_axis','z');assert axis in ('x','z')
  value=C.c_int.from_address(ram+symbols['player']+(0 if axis=='x' else 8)).value/256
  return int(scenario['stream_jump_end']<=value<=scenario['stream_jump_start'])
 if ram and 'yaw' in symbols and id in (12,13):
  for target in scenario.get('camera_targets',[]):
   if target['start']<=tick<target['end']:
    angle=C.c_int.from_address(ram+symbols['yaw']).value&4095
    delta=(target['yaw']-angle)&4095
    if delta>2048:delta-=4096
    return int((id==13 and delta>=16) or (id==12 and delta<=-16))
 if scenario.get('corridor_relic_route') and 460<=tick<scenario.get('corridor_route_end',3600) and ram and 'player' in symbols and 'relics' in symbols and id in (0,4,5,6,7,13):
  x,y,z,_,_,state=struct.unpack('<6i',C.string_at(ram+symbols['player'],24));x/=256;z/=256
  mask=C.c_int.from_address(ram+symbols['relics']).value
  to_checkpoint=scenario.get('corridor_to_checkpoint',False) and mask==3
  if mask==scenario.get('corridor_target_mask',1) and not to_checkpoint:return 0
  if to_checkpoint and 'checkpoint' in symbols and C.c_int.from_address(ram+symbols['checkpoint']).value:return 0
  desired_yaw=scenario.get('corridor_camera_yaw',0)
  if desired_yaw not in (0,2048):raise ValueError('corridor_camera_yaw must be 0 or 2048')
  angle=C.c_int.from_address(ram+symbols['yaw']).value&4095
  if angle!=desired_yaw:return int(id==13)
  if id==13:return 0
  if to_checkpoint:
   waypoints=[(0,-6473),(0,-5000),(1000,-5000),(1000,-7101),(1356,-7101)]
   while corridor_checkpoint_phase<4:
    tx,tz=waypoints[corridor_checkpoint_phase]
    if abs(x-tx)>=20 or abs(z-tz)>=20:break
    corridor_checkpoint_phase+=1
   tx,tz=waypoints[corridor_checkpoint_phase]
   if corridor_checkpoint_phase==2 and x>=350 and state==0 and not corridor_third_jump_sent:
    corridor_third_jump_sent=True;corridor_checkpoint_jump_until=tick+12
   if corridor_checkpoint_phase==3 and z<=-6200 and state==0 and not corridor_fourth_jump_sent:
    corridor_fourth_jump_sent=True;corridor_checkpoint_jump_until=tick+12
   if id==0:return int(tick<corridor_checkpoint_jump_until)
   dx=tx-x;dz=tz-z
   if desired_yaw==2048:return int((id==6 and dx>10) or (id==7 and dx< -10) or (id==4 and dz< -10) or (id==5 and dz>10))
   return int((id==7 and dx>10) or (id==6 and dx< -10) or (id==5 and dz< -10) or (id==4 and dz>10))
  second=bool(mask&1)
  if second:
   if z<=-6300 and state==0:corridor_second_jump_held=True
   jump_held=corridor_second_jump_held
   target=-49 if z> -5700 else -980
   target_z=-6473
  else:
   if z<=-2100 and state==0:corridor_jump_held=True
   jump_held=corridor_jump_held
   target=400 if z> -3200 else -49
   target_z=-3794
  if id==0:return int(jump_held)
  dx=target-x if z<=-1400 else 0
  if desired_yaw==2048:return int((id==6 and dx>10) or (id==7 and dx< -10) or (id==4 and z>target_z))
  return int((id==7 and dx>10) or (id==6 and dx< -10) or (id==5 and z>target_z))
 if scenario.get('stop_movement_at_z') is not None and ram and 'player' in symbols:
  target=scenario['stop_movement_at_z'];value=C.c_int.from_address(ram+symbols['player']+8).value
  if (target<0 and value<=target*256) or (target>=0 and value>=target*256):movement_stopped=True
  if movement_stopped and id in (4,5,6,7):return 0
 if scenario.get('stop_movement_below_y') is not None and ram and 'player' in symbols:
  if C.c_int.from_address(ram+symbols['player']+4).value < scenario['stop_movement_below_y']*256 and C.c_int.from_address(ram+symbols['player']).value >= scenario.get('stop_movement_after_x',-1000000)*256:movement_stopped=True
  if movement_stopped and id in (4,5,6,7):return 0
 if scenario.get('stop_movement_at_x') is not None and ram and 'player' in symbols:
  if C.c_int.from_address(ram+symbols['player']).value >= scenario['stop_movement_at_x']*256:movement_stopped=True
  if movement_stopped and id in (4,5,6,7):return 0
 if scenario.get("stop_on_trial_complete") and ram and "trial" in symbols and id in (4,5,6,7):
  if C.c_int.from_address(ram+symbols["trial"]+12).value and "menu" in symbols and C.c_int.from_address(ram+symbols["menu"]).value==1:return 0
 if scenario.get('relic_route') and ram and 'player' in symbols:
  phase=0 if 900<=tick<1900 else 1 if 2300<=tick<3300 else 2 if 3700<=tick<4700 else -1
  if phase>=0 and id in (0,4,5,6,7):
   x,y,z=struct.unpack('<3i',C.string_at(ram+symbols['player'],12));x/=256;z/=256
   mask=C.c_int.from_address(ram+symbols['relics']).value
   if mask&(1<<phase):return 0
   target=[(-256,786),(678,497),(-141,-804)][phase]
   if id==0:return int(phase==2 and z< -430)
   dx=target[0]-x;dz=target[1]-z
   return int((id==7 and dx>12) or (id==6 and dx< -12) or (id==4 and dz>12) or (id==5 and dz< -12))
 if 'actions' in scenario:
  return int(any(a['start']<=tick<a['end'] and id in a['buttons'] for a in scenario['actions']))
 # Start from title, then move, jump and glide.
 if 300<=tick<320 and id==0:return 1
 if 360<=tick<400 and id==7:return 1 # right
 if 405<=tick<605 and id==0:return 1 # Cross (libretro B)
 return 0
for name,cb in [('environment',env),('video_refresh',video),('audio_sample',audio),('audio_sample_batch',batch),('input_poll',poll),('input_state',inp)]:
 f=getattr(core,'retro_set_'+name);f.argtypes=[type(cb)];f(cb)
core.retro_init();core.retro_set_controller_port_device(0,1)
g=Game(str(Path(sys.argv[2]).resolve()).encode(),None,0,None)
core.retro_load_game.argtypes=[C.POINTER(Game)];core.retro_load_game.restype=C.c_bool
if not core.retro_load_game(C.byref(g)):raise RuntimeError('core rejected content')
symbols={}
trial_words=5
frontend_words=5
atlas_scalars=('levium_drawn','campaign_entry','front_media_ready','front_audio_track','front_logo_frame','front_media_errors','walk_collision_ready','walk_collision_loads','walk_collision_tiles','walk_collision_triangles','atlas_scene','atlas_menu','atlas_ready','atlas_loaded_tiles','atlas_triangle_count','atlas_load_events','atlas_errors','atlas_current_tile','atlas_show_inactive','atlas_drawn','atlas_budget_drops')
mapfile=Path(sys.argv[2]).with_name(scenario.get('map_file','zera.map'))
if mapfile.exists():
 for line in mapfile.read_text().splitlines():
  fields=line.split()
  if len(fields)>=4 and fields[0]=='frontend':frontend_words=int(fields[3],16)//4
  if len(fields)>=4 and fields[0]=='trial':trial_words=7 if int(fields[3],16)>=28 else 5
  if len(fields)>=3 and fields[0] in ('npc_dialogue','frontend','front_sfx_events','player','checkpoint','camera_distance','camera_height','player_respawn_events','simulation_ticks','debug_input_x','debug_input_z','debug_movement_yaw','debug_actual_moving','facing','mascot_visible','launch','relics','yaw','menu','animator','audio_music_ready','audio_underruns','audio_cd_errors','audio_refills','audio_wraps','audio_muted','audio_sfx_events','trial'):symbols[fields[0]]=int(fields[2],16)&0x1fffff
  if len(fields)>=3 and fields[0] in atlas_scalars+('atlas_camera',):symbols[fields[0]]=int(fields[2],16)&0x1fffff
core.retro_get_memory_data.argtypes=[C.c_uint];core.retro_get_memory_data.restype=C.c_void_p
core.retro_get_memory_size.argtypes=[C.c_uint];core.retro_get_memory_size.restype=C.c_size_t
ram=core.retro_get_memory_data(2);ramsize=core.retro_get_memory_size(2)
if scenario.get('audio',True):
 audio_writer=open(out/'audio.raw','wb')
observed=[];gif_frames=[];event_captures=[];event_pending={};event_done=set()
for event in scenario.get('capture_events',[]):
 name=event['name']
 if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name):raise ValueError('Invalid capture event name')
for tick in range(run_frames):
 core.retro_run()
 if scenario.get('gif',True) and gif_start<=tick<gif_end and tick%gif_step==0 and frame:gif_frames.append(frame.resize((640,480),Image.Resampling.NEAREST))
 if (tick>=300 and tick%sample_interval==0 or tick in shots) and ram and ('player' in symbols or 'atlas_scene' in symbols):
  row={'frame':tick,'scenario_movement_stopped':movement_stopped}
  if 'player' in symbols:
   addr=symbols['player'];assert addr+24<=ramsize
   values=struct.unpack('<6i',C.string_at(ram+addr,24));row.update(dict(zip(['x_fp','y_fp','z_fp','vy_fp','dash_ticks','state'],values)))
  for name in atlas_scalars:
   if name in symbols:row[name]=struct.unpack('<i',C.string_at(ram+symbols[name],4))[0]
  if 'atlas_camera' in symbols:row['atlas_camera']=list(struct.unpack('<3i',C.string_at(ram+symbols['atlas_camera'],12)))
  if 'camera_distance' in symbols:row['camera_distance']=struct.unpack('<i',C.string_at(ram+symbols['camera_distance'],4))[0]
  if 'menu' in symbols:
   ms=struct.unpack('<4i',C.string_at(ram+symbols['menu'],16));row.update(dict(zip(['menu_screen','menu_selection','menu_return','diagnostics'],ms)))
  if 'animator' in symbols:
   av=struct.unpack('<3i',C.string_at(ram+symbols['animator'],12));row.update(dict(zip(['animation_clip','animation_tick','blend_tick'],av)))
  for name in ('audio_music_ready','audio_underruns','audio_cd_errors','audio_refills','audio_wraps','audio_muted','camera_height','player_respawn_events','simulation_ticks','debug_input_x','debug_input_z','debug_movement_yaw','debug_actual_moving','facing','mascot_visible','yaw'):
   if name in symbols:row[name]=struct.unpack('<i',C.string_at(ram+symbols[name],4))[0]
  if 'audio_sfx_events' in symbols:row['sfx_events']=list(struct.unpack('<7i',C.string_at(ram+symbols['audio_sfx_events'],28)))
  if 'npc_dialogue' in symbols:
   values=struct.unpack('<7i',C.string_at(ram+symbols['npc_dialogue'],28));row.update(dict(zip(['dialogue_phase','dialogue_page','dialogue_visited','dialogue_completions','dialogue_prompt','dialogue_ticks','dialogue_chars'],values)))
  if 'frontend' in symbols:
   values=struct.unpack('<5i',C.string_at(ram+symbols['frontend'],20));row.update(dict(zip(['frontend_screen','frontend_selection','frontend_return','frontend_muted','frontend_has_game'],values)))
  if 'frontend' in symbols and frontend_words==10:
   values=struct.unpack('<5i',C.string_at(ram+symbols['frontend']+20,20));row.update(dict(zip(['frontend_music_volume','frontend_sfx_volume','frontend_camera_mode','frontend_sensitivity','frontend_page'],values)))
  if 'front_sfx_events' in symbols:row['front_sfx_events']=list(struct.unpack('<7i',C.string_at(ram+symbols['front_sfx_events'],28)))
  if 'relics' in symbols:
   values=struct.unpack('<3i',C.string_at(ram+symbols['relics'],12));row.update(dict(zip(['relic_mask','relic_count','relic_value'],values)))
  if 'checkpoint' in symbols:
   values=struct.unpack('<6i',C.string_at(ram+symbols['checkpoint'],24));row.update(dict(zip(['checkpoint_id','checkpoint_x','checkpoint_y','checkpoint_z','checkpoint_yaw','checkpoint_activations'],values)))
  if 'launch' in symbols:
   values=struct.unpack('<5i',C.string_at(ram+symbols['launch'],20));row.update(dict(zip(['launch_active','launch_time','launch_started','launch_completed','launch_cancelled'],values)))
  if 'trial' in symbols:
   values=struct.unpack('<'+str(trial_words)+'i',C.string_at(ram+symbols['trial'],trial_words*4));row.update(dict(zip(['trial_mask','trial_active','trial_count','trial_complete','trial_ticks','trial_best_ticks','trial_best_valid'],values)))
  observed.append(row)
 if tick in shots and frame:
  frame.save(out/f'frame_{tick:04d}.png');print('Captured',tick,frame.size,flush=True)
 if frame and ram and 'player' in symbols:
  for event in scenario.get('capture_events',[]):
   name=event['name']
   if name in event_done:continue
   x,y,z=struct.unpack('<3i',C.string_at(ram+symbols['player'],12))
   mask=C.c_int.from_address(ram+symbols['relics']).value if 'relics' in symbols else None
   checkpoint_id=C.c_int.from_address(ram+symbols['checkpoint']).value if 'checkpoint' in symbols else 0
   ready=tick>=event.get('min_frame',0) and ('max_z' not in event or z<=event['max_z']*256) and ('relic_mask' not in event or mask==event['relic_mask']) and ('checkpoint_id' not in event or checkpoint_id==event['checkpoint_id'])
   for key,offset in [('dialogue_phase',0),('dialogue_page',4),('dialogue_completions',12)]:
    if key in event:ready=ready and 'npc_dialogue' in symbols and C.c_int.from_address(ram+symbols['npc_dialogue']+offset).value==event[key]
   if 'min_x' in event:ready=ready and x>=event['min_x']*256
   if 'min_collision_loads' in event:
    ready=ready and 'walk_collision_loads' in symbols and C.c_int.from_address(ram+symbols['walk_collision_loads']).value>=event['min_collision_loads'] and C.c_int.from_address(ram+symbols['walk_collision_ready']).value==1
   if 'player_state' in event:ready=ready and C.c_int.from_address(ram+symbols['player']+20).value==event['player_state']
   if ready and name not in event_pending:event_pending[name]=tick
   if name in event_pending and ready and tick>=event_pending[name]+event.get('delay_frames',0):
    frame.save(out/f'{name}.png');event_done.add(name)
    event_captures.append({'name':name,'frame':tick,'trigger_frame':event_pending[name],'position_fp':[x,y,z],'relic_mask':mask,'checkpoint_id':checkpoint_id})
    print('Captured event',name,tick,flush=True)
if gif_frames:
 # GIF timing is quantized to 10 ms; distribute rounding instead of speeding
 # up every sampled frame by truncating 66.7 ms to 60 ms.
 delays=[(round((i+1)*gif_step*100/60)-round(i*gif_step*100/60))*10 for i in range(len(gif_frames))]
 gif_frames[0].save(out/'gameplay.gif',save_all=True,append_images=gif_frames[1:],duration=delays,loop=0)
core.retro_unload_game();core.retro_deinit()
if audio_writer:
 audio_writer.close();raw=(out/'audio.raw').read_bytes();assert len(raw)==audio_written
 with wave.open(str(out/'audio.wav'),'wb') as wav:
  wav.setnchannels(2);wav.setsampwidth(2);wav.setframerate(44100);wav.writeframes(raw)
 (out/'audio.raw').unlink()
(out/'capture.json').write_text(json.dumps({'frames_run':run_frames,'state_samples':observed,'event_captures':event_captures,'content':Path(sys.argv[2]).name,'bin_sha256':hashlib.sha256(Path(sys.argv[2]).with_suffix('.bin').read_bytes()).hexdigest(),'emulator':'PCSX-ReARMed c881679 HLE BIOS interpreter software GPU','gif_samples':len(gif_frames),'audio_output':{'interleaved_samples':audio_count,'peak':audio_peak,'rms':round((audio_energy/max(1,audio_count))**0.5,2),'clipped_samples':audio_clips,'saved_pcm_bytes':audio_written}},indent=2))
print('Capture completed:',run_frames,'frames',flush=True)
