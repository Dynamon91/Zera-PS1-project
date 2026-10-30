/* Original-world CD runtime: inspection, or streamed walking with ZERA_ATLAS_WALK.
   CD loads use a fixed neighborhood buffer rather than keeping a level in RAM. */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include <psxgpu.h>
#include <psxgte.h>
#include <inline_c.h>
#include <psxapi.h>
#include <psxpad.h>
#include <psxcd.h>
#include "clip.h"
#include "atlas_format.h"
#ifdef ZERA_FULL_FRONTEND
#include "frontend.h"
#include "frontend_media.h"
#include "../previews/frontend/src/frontend_assets.h"
#ifdef ZERA_CAMPAIGN_ENTRY
#include "../previews/frontend/src/frontend_text.h"
static volatile int campaign_entry=1;
#endif
static Frontend frontend;
static int frontend_base,frontend_logo_start;
#endif
#ifdef ZERA_ATLAS_WALK
#include "player.h"
#include "world.h"
#include "character.h"
#include "camera.h"
#include "animator.h"
#include "zera_mesh.h"
#include "mascot_materials.h"
#include "mascot_texture.h"
#include "stream_world.h"
#include "relics.h"
#include "checkpoint.h"
#include "../previews/walk/src/checkpoint_config.h"
#include "../previews/level3/src/relic_models.h"
static Relics relics;static Checkpoint checkpoint;
#ifdef ZERA_CAMPAIGN_ENTRY
#include "../previews/cosmic/src/collision_catalog.h"
#else
#include "../previews/walk/src/collision_catalog.h"
#endif
static Player player;static Animator animator;
static volatile int facing=0,mascot_visible=1,camera_distance=850;
static volatile int player_respawn_events=0,simulation_ticks=0,debug_input_x=0,debug_input_z=0,debug_movement_yaw=0,debug_actual_moving=0;
static int camera_height,collision_base,collision_disc_ready,walk_orbit_cooldown,walk_manual_camera;
static CharacterDrawFace character_faces[ZERA_FACE_COUNT];
static short character_heads[1024];
static void walk_camera(void);
static void walk_respawn(void);
static int walk_load(int force);
static void walk_tick(uint16_t held,uint16_t pressed);
static void draw_walking_character(void);
#endif
#ifdef ZERA_LEVIUM_DIALOGUE
#include "dialogue.h"
#include "../previews/levium/src/levium_model.h"
#include "../previews/levium/src/levium_dialogue.h"
static Dialogue npc_dialogue;
static CharacterDrawFace npc_faces[LEVIUM_FACES];
static short npc_heads[1024];
static volatile int levium_drawn;
static void draw_levium(void);
#endif
#include "../previews/atlas/src/atlas_catalog.h"
#define OT_SIZE 1024
#define PACKET_BYTES 131072
#define MAX_RESIDENT 25
static struct {DRAWENV draw;DISPENV disp;uint32_t ot[OT_SIZE];uint8_t packet[PACKET_BYTES];} buffers[2];
static int frame_drawn,frame_budget_drops;
static int active;static uint8_t *packet;static uint8_t pads[2][34];
#ifdef ZERA_FULL_FRONTEND
_Alignas(4) static union {AtlasTriangle triangles[ATLAS_TRIANGLE_CAPACITY+80];uint8_t startup[FRONT_STAGING_BYTES];} shared_world;
#define geometry shared_world.triangles
#else
_Alignas(4) static AtlasTriangle geometry[ATLAS_TRIANGLE_CAPACITY+80];
#endif
_Static_assert(MAX_RESIDENT==(2*ATLAS_NEIGHBOR_RADIUS+1)*(2*ATLAS_NEIGHBOR_RADIUS+1),"Resident sector capacity");
_Static_assert(80*sizeof(AtlasTriangle)>=2048+16,"CD padding reserve");
static struct {int tile,start;} resident[MAX_RESIDENT];
static uint32_t header[512];static int base_sector,disc_ready;
static int yaw,pitch=384,selected,last_tx=0x7fffffff,last_tz=0x7fffffff;
volatile int atlas_scene=0,atlas_menu=1,atlas_camera[3]={0,0,0};
volatile int atlas_loaded_tiles=0,atlas_triangle_count=0,atlas_load_events=0,atlas_errors=0,atlas_ready=0;
volatile int atlas_current_tile=-1,atlas_show_inactive=0,atlas_drawn=0,atlas_budget_drops=0;
static int abs_i(int x){return x<0?-x:x;}
static int floor_cell(int n){int q=n/ATLAS_CELL;if(n<0 && n%ATLAS_CELL)q--;return q;}
static void *primitive(int depth,size_t size){
 if(packet+size>buffers[active].packet+PACKET_BYTES){frame_budget_drops++;return NULL;}
 void *p=packet;addPrim(&buffers[active].ot[depth],p);packet+=size;return p;
}
static void text(int x,int y,const char *s){
 if(packet+8192>buffers[active].packet+PACKET_BYTES)return;
 packet=(uint8_t*)FntSort(&buffers[active].ot[0],packet,x,y,s);
}
static void panel(int y,int height){
 TILE *p=primitive(0,sizeof(*p));if(!p)return;
 setTile(p);setXY0(p,0,y);setWH(p,320,height);setRGB0(p,14,20,32);
}
static void begin_frame(void){ClearOTagR(buffers[active].ot,OT_SIZE);packet=buffers[active].packet;}
static void flip(void){
 DrawSync(0);VSync(0);PutDispEnv(&buffers[active^1].disp);DrawOTagEnv(&buffers[active].ot[OT_SIZE-1],&buffers[active].draw);active^=1;
}
static void status(const char *s){begin_frame();text(12,40,s);flip();}
static int read_cd(int base,int sector,int count,void *target){
 CdlLOC loc;CdIntToPos(base+sector,&loc);
 if(!CdControl(CdlSetloc,(uint8_t*)&loc,NULL) || !CdRead(count,(uint32_t*)target,CdlModeSpeed)){atlas_errors++;return 0;}
 int start=VSync(-1),result;
 while((result=CdReadSync(1,NULL))>0){if(VSync(-1)-start>600){CdReadBreak();atlas_errors++;return 0;}VSync(0);}
 if(result<0){atlas_errors++;return 0;}return 1;
}
static int read_sectors(int sector,int count,void *target){return read_cd(base_sector,sector,count,target);}
#ifdef ZERA_FULL_FRONTEND
static int frontend_read(int sector,int count,void *dest){return read_cd(frontend_base,sector,count,dest);}
static void frontend_boot(void){
 frontend_init(&frontend);status("LOADING ZERA MYTHS AWAKEN");CdlFILE file;
 if(!CdSearchFile(&file,"\\FRONT.DAT;1")){atlas_errors++;frontend_finish_logo(&frontend);return;}
 frontend_base=CdPosToInt(&file.pos);
 if(!frontend_media_load(frontend_read,shared_world.startup,sizeof(shared_world.startup))){atlas_errors++;frontend_finish_logo(&frontend);return;}
 frontend_logo_start=VSync(-1);
}
static void frontend_picture(int logo){
 POLY_FT4 *p=primitive(1,sizeof(*p));if(!p)return;setPolyFT4(p);setRGB0(p,128,128,128);
 if(logo){
  setXY4(p,0,30,320,30,0,210,320,210);setUV4(p,0,0,159,0,0,89,159,89);p->tpage=getTPage(0,0,768,0)|0x400;p->clut=getClut(768,128);
 }else{
  setXY4(p,32,0,288,0,32,144,288,144);setUV4(p,0,64,255,64,0,207,255,207);p->tpage=getTPage(2,0,512,256)|0x400;p->clut=0;
 }
}
static void frontend_draw(void){
 if(frontend.screen==FRONT_LOGO){frontend_picture(1);return;}
#ifdef ZERA_CAMPAIGN_ENTRY
 if(frontend.screen==FRONT_CREDITS || frontend.screen==FRONT_CHANGELOG){
  int credits=frontend.screen==FRONT_CREDITS;
  text(16,16,credits?"CREDITS":"CHANGELOG - ORIGINAL BUILD");
  text(16,40,credits?frontend_credits_pages[frontend.page]:frontend_changelog_pages[frontend.page]);
  char status[80];snprintf(status,sizeof(status),"PAGE %d/%d  DPAD: PAGE  CIRCLE: BACK",frontend.page+1,credits?FRONT_CREDITS_PAGES:FRONT_CHANGELOG_PAGES);text(8,224,status);return;
 }
#endif
 if(front_media_ready)frontend_picture(0);else text(48,64,"ZERA - MYTHS AWAKEN");
 #ifdef ZERA_CAMPAIGN_ENTRY
 const char *title_items[]={"PLAY","OPTIONS","CONTROLS","VIEW CREDITS","CHANGELOG"};
#else
 const char *title_items[]={"NEW GAME","OPTIONS","CONTROLS"};
#endif
 const char *pause_items[]={"RESUME","RESPAWN","OPTIONS","CONTROLS","RETURN TO TITLE"};
 if(frontend.screen==FRONT_TITLE || frontend.screen==FRONT_PAUSE){
  int count=frontend.screen==FRONT_TITLE?3:5;
#ifdef ZERA_CAMPAIGN_ENTRY
  count=5;
#endif
  for(int i=0;i<count;i++){char row[64];snprintf(row,sizeof(row),"%c %s",i==frontend.selection?'>':' ',frontend.screen==FRONT_TITLE?title_items[i]:pause_items[i]);text(80,150+i*13,row);}
 }else if(frontend.screen==FRONT_OPTIONS){
#ifdef ZERA_CAMPAIGN_ENTRY
  const char *items[]={frontend.muted?"SOUND: OFF":"SOUND: ON","AUDIO","GAMEPLAY","BACK"};
  for(int i=0;i<4;i++){char row[64];snprintf(row,sizeof(row),"%c %s",frontend.selection==i?'>':' ',items[i]);text(72,150+i*14,row);}
 }else if(frontend.screen==FRONT_AUDIO_OPTIONS || frontend.screen==FRONT_GAMEPLAY_OPTIONS){
  char first[64],second[64];
  if(frontend.screen==FRONT_AUDIO_OPTIONS){snprintf(first,sizeof(first),"MUSIC: %d/4",frontend.music_volume);snprintf(second,sizeof(second),"SOUND EFFECTS: %d/4",frontend.sfx_volume);}
  else{snprintf(first,sizeof(first),"CAMERA: %s",frontend.camera_mode?"MANUAL":"AUTOMATIC");snprintf(second,sizeof(second),"SENSITIVITY: %d/4",frontend.sensitivity);}
  const char *items[]={first,second,"BACK"};
  for(int i=0;i<3;i++){char row[80];snprintf(row,sizeof(row),"%c %s",frontend.selection==i?'>':' ',items[i]);text(40,150+i*16,row);}
  text(48,208,"LEFT/RIGHT: ADJUST");
#else
  char row[64];snprintf(row,sizeof(row),"%c SOUND: %s",frontend.selection==0?'>':' ',frontend.muted?"OFF":"ON");text(80,158,row);text(80,184,frontend.selection==1?"> BACK":"  BACK");
#endif
 }else if(frontend.screen==FRONT_CONTROLS){
  text(36,148,"DPAD     MOVE\nCROSS    JUMP / HOLD TO GLIDE\nR1       DASH\nL2 / R2  CAMERA    L1 CENTER\nSELECT   RESPAWN   START PAUSE");
 }
 text(36,226,"CROSS: SELECT   CIRCLE: BACK");
 if(frontend.screen==FRONT_PAUSE)text(136,136,"PAUSED");
}
#endif
static int open_disc(void){
 CdlFILE file;if(!CdSearchFile(&file,"\\WORLD.DAT;1")){atlas_errors++;return 0;}
 base_sector=CdPosToInt(&file.pos);
 if(!read_sectors(0,1,header))return 0;
 if(memcmp(header,"ZATL0001",8) || memcmp((uint8_t*)header+8,atlas_tag,16) || header[6]!=ATLAS_SCENES || header[7]!=ATLAS_CELL){atlas_errors++;return 0;}
 return 1;
}
static int find_tile(int scene,int tx,int tz){
 for(int i=0;i<ATLAS_TILE_COUNT;i++)if(atlas_tiles[i].scene==scene && atlas_tiles[i].tx==tx && atlas_tiles[i].tz==tz)return i;
 return -1;
}
static void load_neighborhood(int force){
 int tx=floor_cell(atlas_camera[0]),tz=floor_cell(atlas_camera[2]);
 if(!force && tx==last_tx && tz==last_tz)return;
 last_tx=tx;last_tz=tz;atlas_ready=0;atlas_loaded_tiles=0;atlas_triangle_count=0;atlas_current_tile=find_tile(atlas_scene,tx,tz);atlas_load_events++;
 status("LOADING ORIGINAL MAP SECTORS\nPLEASE WAIT");
 if(!disc_ready){disc_ready=open_disc();if(!disc_ready)return;}
 for(int dz=-ATLAS_NEIGHBOR_RADIUS;dz<=ATLAS_NEIGHBOR_RADIUS;dz++)for(int dx=-ATLAS_NEIGHBOR_RADIUS;dx<=ATLAS_NEIGHBOR_RADIUS;dx++){
  int index=find_tile(atlas_scene,tx+dx,tz+dz);if(index<0)continue;
  const AtlasTile *tile=&atlas_tiles[index];
  if(tile->count>ATLAS_TRIANGLE_CAPACITY-atlas_triangle_count || tile->sectors*2048>(int)(sizeof(geometry)-atlas_triangle_count*sizeof(AtlasTriangle))){atlas_errors++;return;}
  void *dest=&geometry[atlas_triangle_count];
  if(!read_sectors(tile->sector,tile->sectors,dest))return;
  int32_t h[4];memcpy(h,dest,sizeof(h));
  if(h[0]!=atlas_scene || h[1]!=tile->tx || h[2]!=tile->tz || h[3]!=tile->count){atlas_errors++;return;}
  memmove(dest,(uint8_t*)dest+16,tile->count*sizeof(AtlasTriangle));
  resident[atlas_loaded_tiles].tile=index;resident[atlas_loaded_tiles].start=atlas_triangle_count;
  atlas_loaded_tiles++;atlas_triangle_count+=tile->count;
 }
 atlas_ready=1;
}
#ifdef ZERA_ATLAS_WALK
static int collision_read(int sector,int count,void *dest,void *user){(void)user;return read_cd(collision_base,sector,count,dest);}
static int walk_load(int force){
 int x=player.x/FP,z=player.z/FP;
 if(!stream_cache_needs_load(x,z,force))return 1;
 status("LOADING ORIGINAL COLLIDERS\nPLEASE WAIT");
 if(!collision_disc_ready){
  CdlFILE file;
#ifdef ZERA_CAMPAIGN_ENTRY
  const char *collision_path="\\COSMIC.DAT;1";
#else
  const char *collision_path="\\COLLIDE.DAT;1";
#endif
  if(!CdSearchFile(&file,collision_path)){atlas_errors++;return 0;}
  collision_base=CdPosToInt(&file.pos);
  if(!read_cd(collision_base,0,1,header))return 0;
  if(memcmp(header,"ZCOL0001",8) || memcmp((unsigned char*)header+8,stream_collision_tag,16) || header[6]!=STREAM_CELL || header[7]!=STREAM_COLLISION_TILES){atlas_errors++;return 0;}
  collision_disc_ready=1;
 }
 int before=atlas_errors;
 if(!stream_cache_load(x,z,force,collision_read,NULL)){if(atlas_errors==before)atlas_errors++;return 0;}
 return 1;
}
static int floor_half(int n){return n/2-(n<0 && n%2!=0);}
static int walk_view(int angle,MATRIX *m){
 SVECTOR rotation={pitch,angle,0,0};RotMatrix(&rotation,m);
 int dx=(-100*m->m[1][0]-850*m->m[2][0])/4096;
 int dy=(100*m->m[1][1]+850*m->m[2][1])/4096;
 int dz=(-100*m->m[1][2]-850*m->m[2][2])/4096;
 return world_camera_fraction(player.x/FP,camera_height,player.z/FP,dx,dy,dz);
}
static void walk_camera(void){
 MATRIX m;int fraction=walk_view(yaw,&m);
 if(walk_orbit_cooldown)walk_orbit_cooldown--;
 if(!walk_manual_camera && !debug_input_x && !debug_input_z && !walk_orbit_cooldown && fraction<2048){
  MATRIX left,right;int lf=walk_view(yaw+512,&left),rf=walk_view(yaw-512,&right);
  int offset=camera_orbit_offset(fraction,lf,rf);
  if(offset){yaw+=offset;m=offset>0?left:right;fraction=offset>0?lf:rf;camera_distance=850*fraction/4096;walk_orbit_cooldown=30;}
 }
 camera_distance=camera_distance_step(camera_distance,fraction,0);
 mascot_visible=character_visible_step(mascot_visible,camera_distance);
 atlas_camera[0]=floor_half(player.x/FP)+(-100*m.m[1][0]-camera_distance*m.m[2][0])/8192;
 atlas_camera[1]=floor_half(-camera_height)+(-100*m.m[1][1]-camera_distance*m.m[2][1])/8192;
 atlas_camera[2]=floor_half(player.z/FP)+(-100*m.m[1][2]-camera_distance*m.m[2][2])/8192;
}
#endif
static void enter_scene(int scene){
#ifdef ZERA_ATLAS_WALK
#ifdef ZERA_CAMPAIGN_ENTRY
 scene=0;
#else
 scene=1;
#endif
 atlas_scene=scene;atlas_menu=0;atlas_show_inactive=0;yaw=0;pitch=280;
 #ifdef ZERA_CAMPAIGN_ENTRY
 yaw=atlas_scenes[0].yaw;
#endif
#ifdef ZERA_LEVIUM_DIALOGUE
 dialogue_clear(&npc_dialogue);
#endif
 relics_clear(&relics);checkpoint_clear(&checkpoint);
 player_init(&player);animator_init(&animator);facing=0;camera_height=0;camera_distance=850;mascot_visible=1;walk_orbit_cooldown=0;walk_manual_camera=0;debug_input_x=debug_input_z=0;
#ifdef ZERA_CAMPAIGN_ENTRY
 facing=(-yaw)&4095;
#endif
 if(!walk_load(1))return;
 Input still={.camera_c=4096};player_tick(&player,still);camera_height=player.y/FP;walk_camera();
#else
 atlas_scene=scene;atlas_menu=0;atlas_show_inactive=0;yaw=atlas_scenes[scene].yaw;pitch=384;
 for(int i=0;i<3;i++)atlas_camera[i]=atlas_scenes[scene].entry[i];
#endif
 load_neighborhood(1);
}
#ifndef ZERA_ATLAS_WALK
static void next_sector(void){
 int next=(atlas_current_tile+1)%ATLAS_TILE_COUNT;
 for(int n=0;n<ATLAS_TILE_COUNT;n++,next=(next+1)%ATLAS_TILE_COUNT){
  const AtlasTile *t=&atlas_tiles[next];if(t->scene!=atlas_scene)continue;
  atlas_camera[0]=t->center[0];atlas_camera[1]=t->center[1]-ATLAS_CELL/3;atlas_camera[2]=t->center[2];
  load_neighborhood(1);return;
 }
}
#endif
static int clamp_color(int n){return n<0?0:n>255?255:n;}
static void draw_triangle(const AtlasTriangle *tri,const AtlasTile *tile,const ClipCamera *camera){
 ClipVertex input[3],out[10];
 for(int k=0;k<3;k++){
  int x=tri->v[k][0]+tile->center[0]-atlas_camera[0],y=tri->v[k][1]+tile->center[1]-atlas_camera[1],z=tri->v[k][2]+tile->center[2]-atlas_camera[2];
  if(abs_i(x)>16000 || abs_i(y)>16000 || abs_i(z)>16000)return;
  input[k]=(ClipVertex){x,y,z,k==0?256:0,k==1?256:0};
 }
 int n=clip_triangle(camera,input,out);
 for(int k=1;k<n-1;k++){
  ClipVertex *v[3]={&out[0],&out[k],&out[k+1]};
  SVECTOR a={v[0]->x,v[0]->y,v[0]->z,0},b={v[1]->x,v[1]->y,v[1]->z,0},c={v[2]->x,v[2]->y,v[2]->z,0};
  short xy[6];int flag,depth;
  gte_ldv3(&a,&b,&c);gte_rtpt();gte_stflg(&flag);if(flag&0x80000000)continue;
  gte_stsxy3(&xy[0],&xy[2],&xy[4]);
  int area=(xy[2]-xy[0])*(xy[5]-xy[1])-(xy[3]-xy[1])*(xy[4]-xy[0]);if(area>=0)continue;
  gte_avsz3();gte_stotz(&depth);
  depth>>=2;if(depth<1)depth=1;if(depth>=OT_SIZE)depth=OT_SIZE-1;
  POLY_G3 *p=primitive(depth,sizeof(*p));if(!p)return;
  setPolyG3(p);setXY3(p,xy[0],xy[1],xy[2],xy[3],xy[4],xy[5]);
  uint8_t rgb[3][3];
  for(int corner=0;corner<3;corner++)for(int ch=0;ch<3;ch++)rgb[corner][ch]=clamp_color((tri->color[0][ch]*v[corner]->u+tri->color[1][ch]*v[corner]->v+tri->color[2][ch]*(256-v[corner]->u-v[corner]->v))/256);
  setRGB0(p,rgb[0][0],rgb[0][1],rgb[0][2]);setRGB1(p,rgb[1][0],rgb[1][1],rgb[1][2]);setRGB2(p,rgb[2][0],rgb[2][1],rgb[2][2]);frame_drawn++;
 }
}
#ifdef ZERA_ATLAS_WALK
/* Relics/checkpoint survive Select and falls; only a new game clears them. */
static void walk_respawn(void){
#ifdef ZERA_LEVIUM_DIALOGUE
 npc_dialogue.phase=0;npc_dialogue.prompt=0;
#endif
 player_init(&player);yaw=0;pitch=280;
#ifdef ZERA_CAMPAIGN_ENTRY
 yaw=atlas_scenes[0].yaw;
#endif
 if(checkpoint_respawn(&checkpoint,&player))yaw=checkpoint.yaw;
 animator_init(&animator);facing=yaw;
#ifdef ZERA_CAMPAIGN_ENTRY
 facing=(-yaw)&4095;
#endif
 camera_distance=850;mascot_visible=1;
 walk_orbit_cooldown=30;debug_input_x=debug_input_z=0;
 if(!walk_load(1))return;
 Input still={.camera_c=4096};player_tick(&player,still);
 camera_height=player.y/FP;walk_camera();load_neighborhood(1);
}
static void draw_walking_relics(const ClipCamera *camera){
 for(int id=0;id<RELIC_COUNT;id++){
  if(relics.mask&(1<<id))continue;
  if(abs_i(relic_positions[id][0]-player.x/FP)>2560 || abs_i(relic_positions[id][2]-player.z/FP)>2560)continue;
  const unsigned short *span=relic_model_spans[id];
  for(int i=span[2];i<span[2]+span[3];i++){
   ClipVertex input[3],out[10];
   for(int k=0;k<3;k++){
    const SVECTOR *v=&relic_model_vertices[relic_model_faces[i][k]];
    input[k]=(ClipVertex){floor_half(relic_positions[id][0]+v->vx)-atlas_camera[0],floor_half(-relic_positions[id][1]+v->vy)-atlas_camera[1],floor_half(relic_positions[id][2]+v->vz)-atlas_camera[2],0,0};
   }
   int n=clip_triangle(camera,input,out);
   for(int k=1;k<n-1;k++){
    SVECTOR a={out[0].x,out[0].y,out[0].z,0},b={out[k].x,out[k].y,out[k].z,0},c={out[k+1].x,out[k+1].y,out[k+1].z,0};
    short xy[6];int flags,depth;gte_ldv3(&a,&b,&c);gte_rtpt();gte_stflg(&flags);if(flags&0x80000000)continue;
    gte_stsxy3(&xy[0],&xy[2],&xy[4]);gte_avsz3();gte_stotz(&depth);depth>>=2;if(depth<1)depth=1;if(depth>=OT_SIZE)depth=OT_SIZE-1;
    POLY_F3 *p=primitive(depth,sizeof(*p));if(!p)return;const unsigned char *col=relic_model_colors[i];
    setPolyF3(p);setXY3(p,xy[0],xy[1],xy[2],xy[3],xy[4],xy[5]);setRGB0(p,col[0],col[1],col[2]);
   }
  }
 }
}
static void walk_tick(uint16_t held,uint16_t pressed){
#ifdef ZERA_LEVIUM_DIALOGUE
 int phase=npc_dialogue.phase;
 if(dialogue_input(&npc_dialogue,&player,!!(pressed&PAD_TRIANGLE),!!(pressed&PAD_CROSS))){
  if(npc_dialogue.phase==DIALOGUE_APPROACH){
   if(!walk_load(0))return;
   Input in=dialogue_approach_input(&player);int ox=player.x,oz=player.z;simulation_ticks++;
   if(player_tick(&player,in)){player_respawn_events++;walk_respawn();return;}
   animator_update(&animator,character_animation(player.state,player.x!=ox || player.z!=oz),1);
   facing=character_facing_step(facing,in.x,in.z,0,1);
   dialogue_after_approach(&npc_dialogue,&player);if(!walk_load(0))return;
  }
  if(npc_dialogue.phase==DIALOGUE_TALK){
   animator_update(&animator,0,1);
   facing=LEVIUM_TALK_FACING;
   for(int i=0;i<3;i++)atlas_camera[i]=floor_half(i==1?-levium_camera_position[i]:levium_camera_position[i]);
   mascot_visible=1;load_neighborhood(0);return;
  }
  if(phase!=DIALOGUE_NONE && npc_dialogue.phase==DIALOGUE_NONE)frontend_media_effect(1);
  camera_height=player.y/FP;walk_camera();load_neighborhood(0);return;
 }
#endif
 walk_manual_camera=!!(held&(PAD_L1|PAD_L2|PAD_R2));
#ifdef ZERA_CAMPAIGN_ENTRY
 walk_manual_camera|=frontend.camera_mode;
#endif
 int camera_step=16,reset_yaw=0;
#ifdef ZERA_CAMPAIGN_ENTRY
 camera_step=frontend.sensitivity*8;reset_yaw=atlas_scenes[0].yaw;
#endif
 if(held&PAD_L2)yaw-=camera_step;if(held&PAD_R2)yaw+=camera_step;if(pressed&PAD_L1){yaw=reset_yaw;pitch=280;}
 if(!walk_load(0))return;
 Input in={(!!(held&PAD_RIGHT))-(!!(held&PAD_LEFT)),(!!(held&PAD_UP))-(!!(held&PAD_DOWN)),!!(pressed&PAD_CROSS),!!(held&PAD_CROSS),!!(pressed&PAD_R1),rcos(yaw),rsin(yaw)};
 debug_input_x=in.x;debug_input_z=in.z;debug_movement_yaw=yaw;
 int oldx=player.x,oldz=player.z;simulation_ticks++;
#ifdef ZERA_FULL_FRONTEND
 int old_state=player.state,old_mask=relics.mask;
#endif
 if(player_tick(&player,in)){player_respawn_events++;walk_respawn();return;}
 debug_actual_moving=player.x!=oldx || player.z!=oldz;
 facing=character_facing_step(facing,in.x,in.z,yaw,1);
 animator_update(&animator,character_animation(player.state,debug_actual_moving),1);
 if(!walk_load(0))return;
 if(atlas_scene==1){relics_update(&relics,&player,1);checkpoint_update(&checkpoint,&checkpoint_config,&player,1);}
#ifdef ZERA_FULL_FRONTEND
 if(old_state==GROUND && player.state==JUMP)frontend_media_effect(2);
 if(old_state!=GROUND && player.state==GROUND)frontend_media_effect(3);
 if(in.dash_pressed)frontend_media_effect(4);
 if(old_state!=GLIDE && player.state==GLIDE)frontend_media_effect(5);
 if(old_mask!=relics.mask)frontend_media_effect(6);
#endif
 camera_height+=(player.y/FP-camera_height)/8;walk_camera();load_neighborhood(0);
}
static void draw_walking_character(void){
 for(int i=0;i<OT_SIZE;i++)character_heads[i]=-1;
 int count=0,fc=rcos(facing),fs=rsin(facing);
 if(!mascot_visible)return;
 for(int order=0;order<ZERA_FACE_COUNT;order++){
  int face_id=mascot_draw_order[order];const unsigned short *f=zera_faces[face_id];SVECTOR verts[3];
  for(int k=0;k<3;k++){
   const AnimPoint *v=&animator.local[f[k]];
   int x=(v->x*fc+v->z*fs)/4096,z=(-v->x*fs+v->z*fc)/4096;
   verts[k]=(SVECTOR){floor_half(player.x/FP+x)-atlas_camera[0],floor_half(-player.y/FP+v->y)-atlas_camera[1],floor_half(player.z/FP+z)-atlas_camera[2],0};
  }
  short xy[6];int flags,depth,z0,z1,z2;
  gte_ldv3(&verts[0],&verts[1],&verts[2]);gte_rtpt();gte_stflg(&flags);if(flags&0x80000000)continue;
  gte_stsz3(&z0,&z1,&z2);if(z0<64 || z1<64 || z2<64)continue;
  gte_stsxy3(&xy[0],&xy[2],&xy[4]);if(!character_front_face(xy))continue;
  gte_avsz3();gte_stotz(&depth);depth>>=2;if(depth<1)depth=1;if(depth>=OT_SIZE)depth=OT_SIZE-1;
  CharacterDrawFace *record=&character_faces[count];record->face=face_id;record->key=(z0+z1+z2)*4+2-mascot_material[face_id];
  for(int k=0;k<6;k++)record->xy[k]=xy[k];character_link_face(character_faces,&character_heads[depth],count++);
 }
 for(int depth=1;depth<OT_SIZE;depth++)for(int index=character_heads[depth];index>=0;index=character_faces[index].next){
  const CharacterDrawFace *r=&character_faces[index];int i=r->face;const short *xy=r->xy;const unsigned char *col=mascot_corner_colors[i];
  if(mascot_material[i]){
   POLY_GT3 *p=primitive(depth,sizeof(*p));if(!p)return;const unsigned char *uv=mascot_uv[i];setPolyGT3(p);
   setXY3(p,xy[0],xy[1],xy[2],xy[3],xy[4],xy[5]);setRGB0(p,col[0]/2,col[1]/2,col[2]/2);setRGB1(p,col[3]/2,col[4]/2,col[5]/2);setRGB2(p,col[6]/2,col[7]/2,col[8]/2);
   setUV3(p,uv[0],uv[1],uv[2],uv[3],uv[4],uv[5]);p->tpage=getTPage(1,0,640,0);p->clut=getClut(512,257);
   DR_TWIN *tw=primitive(depth,sizeof(*tw));if(!tw)return;RECT window={mascot_material[i]==2?128:0,0,128,128};setTexWindow(tw,&window);
  }else{
   POLY_G3 *p=primitive(depth,sizeof(*p));if(!p)return;setPolyG3(p);setXY3(p,xy[0],xy[1],xy[2],xy[3],xy[4],xy[5]);
   setRGB0(p,col[0],col[1],col[2]);setRGB1(p,col[3],col[4],col[5]);setRGB2(p,col[6],col[7],col[8]);
  }
 }
}
#endif
#ifdef ZERA_LEVIUM_DIALOGUE
static void draw_levium(void){
 levium_drawn=0;if(abs_i(player.x/FP-LEVIUM_X)>2400 || abs_i(player.z/FP-LEVIUM_Z)>2400)return;
 for(int i=0;i<OT_SIZE;i++)npc_heads[i]=-1;
 int count=0;
 for(int face=0;face<LEVIUM_FACES;face++){
  SVECTOR verts[3];
  for(int k=0;k<3;k++){const short *v=levium_vertices[levium_faces[face][k]];verts[k]=(SVECTOR){floor_half(LEVIUM_X+v[0])-atlas_camera[0],floor_half(-LEVIUM_Y+v[1])-atlas_camera[1],floor_half(LEVIUM_Z+v[2])-atlas_camera[2],0};}
  short xy[6];int flag,depth,z0,z1,z2;gte_ldv3(&verts[0],&verts[1],&verts[2]);gte_rtpt();gte_stflg(&flag);if(flag&0x80000000)continue;
  gte_stsz3(&z0,&z1,&z2);if(z0<64 || z1<64 || z2<64)continue;gte_stsxy3(&xy[0],&xy[2],&xy[4]);
  int area=(xy[2]-xy[0])*(xy[5]-xy[1])-(xy[3]-xy[1])*(xy[4]-xy[0]);if(!area || (levium_material[face]!=2 && area>=0))continue;
  gte_avsz3();gte_stotz(&depth);depth>>=2;if(depth<1)depth=1;if(depth>=OT_SIZE)depth=OT_SIZE-1;
  CharacterDrawFace *record=&npc_faces[count];record->face=face;record->key=(z0+z1+z2)*4+(levium_material[face]==1?0:1);
  for(int k=0;k<6;k++)record->xy[k]=xy[k];character_link_face(npc_faces,&npc_heads[depth],count++);
 }
 for(int depth=1;depth<OT_SIZE;depth++)for(int i=npc_heads[depth];i>=0;i=npc_faces[i].next){
  const CharacterDrawFace *r=&npc_faces[i];int face=r->face;const short *xy=r->xy;const unsigned char *c=levium_colors[face];
  if(levium_material[face]==1){
   POLY_GT3 *p=primitive(depth,sizeof(*p));if(!p)return;const unsigned char *uv=levium_uv[face];setPolyGT3(p);setXY3(p,xy[0],xy[1],xy[2],xy[3],xy[4],xy[5]);setUV3(p,uv[0],uv[1],uv[2],uv[3],uv[4],uv[5]);setRGB0(p,c[0]/2,c[1]/2,c[2]/2);setRGB1(p,c[3]/2,c[4]/2,c[5]/2);setRGB2(p,c[6]/2,c[7]/2,c[8]/2);p->tpage=getTPage(1,0,768,256);p->clut=getClut(768,320);
   DR_TWIN *window=primitive(depth,sizeof(*window));if(!window)return;RECT wrap={0,0,24,24};setTexWindow(window,&wrap);
  }else{
   POLY_G3 *p=primitive(depth,sizeof(*p));if(!p)return;setPolyG3(p);setXY3(p,xy[0],xy[1],xy[2],xy[3],xy[4],xy[5]);setRGB0(p,c[0],c[1],c[2]);setRGB1(p,c[3],c[4],c[5]);setRGB2(p,c[6],c[7],c[8]);
  }
  levium_drawn++;
 }
}
#endif
int main(void){
 SetVideoMode(MODE_NTSC);ResetGraph(0);InitGeom();gte_SetGeomOffset(160,110);gte_SetGeomScreen(256);
 for(int i=0;i<2;i++){
  SetDefDrawEnv(&buffers[i].draw,0,i*240,320,240);SetDefDispEnv(&buffers[i].disp,0,i*240,320,240);
  buffers[i].draw.isbg=1;setRGB0(&buffers[i].draw,24,32,56);
 }
 #ifdef ZERA_ATLAS_WALK
 (void)zera_vertices;(void)zera_face_colors;
 RECT tex={640,0,128,128},palette={512,257,256,1};LoadImage(&tex,mascot_texture);LoadImage(&palette,mascot_clut);DrawSync(0);selected=1;
#endif
 FntLoad(960,0);SetDispMask(1);InitPAD(pads[0],34,pads[1],34);StartPAD();ChangeClearPAD(0);CdInit();
#ifdef ZERA_FULL_FRONTEND
 frontend_boot();
#ifdef ZERA_LEVIUM_DIALOGUE
 RECT npc_tex={768,256,32,64},npc_palette={768,320,256,1};LoadImage(&npc_tex,levium_texture);LoadImage(&npc_palette,levium_clut);DrawSync(0);
#endif
#endif
 uint16_t old=0;
 for(;;){
  PADTYPE *pad=(PADTYPE*)pads[0];uint16_t held=pad->stat==0?(uint16_t)~pad->btn:0,pressed=held&~old;old=held;
#ifdef ZERA_FULL_FRONTEND
  int previous=frontend.screen,action=0;
  if(previous==FRONT_LOGO){
   int elapsed=VSync(-1)-frontend_logo_start;
   if(pressed || elapsed>=FRONT_LOGO_TICKS)frontend_finish_logo(&frontend);
   else frontend_media_logo(elapsed);
   if(frontend.screen==FRONT_TITLE)frontend_media_track(2);
  }else{
   unsigned input=(pressed&PAD_LEFT?FRONT_LEFT:0)|(pressed&PAD_RIGHT?FRONT_RIGHT:0)|(pressed&PAD_UP?UI_UP:0)|(pressed&PAD_DOWN?UI_DOWN:0)|(pressed&PAD_CROSS?UI_ACCEPT:0)|(pressed&PAD_CIRCLE?UI_BACK:0)|(pressed&PAD_START?UI_START:0);
   action=frontend_update(&frontend,input);frontend_media_mute(frontend.muted);
#ifdef ZERA_CAMPAIGN_ENTRY
   frontend_media_levels(frontend.music_volume,frontend.sfx_volume);
#endif
   if(previous!=FRONT_PLAY && (input&(UI_UP|UI_DOWN)))frontend_media_effect(0);
   if(previous!=FRONT_PLAY && (input&UI_ACCEPT))frontend_media_effect(1);
  }
  atlas_menu=frontend.screen!=FRONT_PLAY;
  if(action&FRONT_NEW_GAME){frontend_media_track(0);enter_scene(1);}
  if(action&FRONT_RESPAWN)walk_respawn();
  if(action&FRONT_RETURN_TITLE)frontend_media_track(2);
  if(frontend.screen==FRONT_PLAY && previous==FRONT_PLAY){
   if(pressed&PAD_SELECT)walk_respawn();
   walk_tick(held,pressed);
  }
  for(int i=0;i<2;i++)setRGB0(&buffers[i].draw,atlas_menu?0:24,atlas_menu?0:32,atlas_menu?0:56);
#else
  if(atlas_menu){
   #ifndef ZERA_ATLAS_WALK
   if(pressed&PAD_DOWN)selected=(selected+1)%ATLAS_SCENES;
   if(pressed&PAD_UP)selected=(selected+ATLAS_SCENES-1)%ATLAS_SCENES;
   #endif
   if(pressed&PAD_CROSS)enter_scene(selected);
  }else{
   if(pressed&PAD_START){atlas_menu=1;selected=atlas_scene;}
   #ifdef ZERA_ATLAS_WALK
   if(!atlas_menu && (pressed&PAD_SELECT))walk_respawn();
#else
   if(pressed&PAD_SELECT)enter_scene(atlas_scene);
#endif
#ifdef ZERA_ATLAS_WALK
   if(!atlas_menu)walk_tick(held,pressed);
#else
   if(pressed&PAD_TRIANGLE)next_sector();
   if(pressed&PAD_SQUARE)atlas_show_inactive=!atlas_show_inactive;
   if(held&PAD_L2)yaw-=16;if(held&PAD_R2)yaw+=16;
   if(pressed&PAD_L1){yaw=atlas_scenes[atlas_scene].yaw;pitch=384;}
   if(held&PAD_R3)pitch+=8;if(held&PAD_L3)pitch-=8;if(pitch>768)pitch=768;if(pitch< -768)pitch=-768;
   int speed=held&PAD_R1?60:20,forward=(!!(held&PAD_UP))-(!!(held&PAD_DOWN)),side=(!!(held&PAD_RIGHT))-(!!(held&PAD_LEFT));
   atlas_camera[0]+=speed*(side*rcos(yaw)-forward*rsin(yaw))/4096;
   atlas_camera[2]+=speed*(forward*rcos(yaw)+side*rsin(yaw))/4096;
   atlas_camera[1]+=speed*((!!(held&PAD_CIRCLE))-(!!(held&PAD_CROSS)));
   load_neighborhood(0);
#endif
  }
#endif
  begin_frame();frame_drawn=0;frame_budget_drops=0;
  if(atlas_menu){
#ifdef ZERA_FULL_FRONTEND
   frontend_draw();
#elif defined(ZERA_ATLAS_WALK)
   text(20,22,"ZERA - DREARY VALLEY\nSTREAMED WALKING PROTOTYPE");
   text(32,88,"CROSS: NEW GAME / RESET PROGRESS");
   text(12,208,"ORIGINAL MESH COLLIDERS\nWORK IN PROGRESS");
#else
   text(20,22,"ZERA - ORIGINAL WORLD ATLAS\nGEOMETRY INSPECTION PREVIEW");
   for(int i=0;i<ATLAS_SCENES;i++){char label[80];snprintf(label,sizeof(label),"%c %s",selected==i?'>':' ',atlas_scenes[i].name);text(40,72+18*i,label);}
   text(12,208,"CROSS: OPEN MAP\nFREE FLIGHT - GAMEPLAY INCOMPLETE");
#endif
  }else{
   MATRIX m;SVECTOR rotation={pitch,yaw,0,0};RotMatrix(&rotation,&m);
#ifdef ZERA_LEVIUM_DIALOGUE
   if(npc_dialogue.phase==DIALOGUE_TALK)for(int r=0;r<3;r++)for(int c=0;c<3;c++)m.m[r][c]=levium_camera_rotation[r][c];
#endif
   VECTOR zero={0,0,0};TransMatrix(&m,&zero);gte_SetRotMatrix(&m);gte_SetTransMatrix(&m);
   ClipCamera camera;for(int r=0;r<3;r++){camera.t[r]=0;for(int c=0;c<3;c++)camera.m[r][c]=m.m[r][c];}
   /* Insert text first so the prepend ordering keeps it over the map. */
#ifdef ZERA_ATLAS_WALK
#ifdef ZERA_LEVIUM_DIALOGUE
   if(npc_dialogue.phase!=DIALOGUE_TALK){
#endif
#ifdef ZERA_CAMPAIGN_ENTRY
   char label[220];snprintf(label,sizeof(label),"COSMIC CORE\nX %d Y %d Z %d  LOADS %d/%d\n%s%s",player.x/FP,player.y/FP,player.z/FP,atlas_load_events,walk_collision_loads,walk_collision_ready?"ORIGINAL COLLISION READY":"LOADING COLLISION",atlas_errors?" - CD ERROR":"");text(8,8,label);
#else
   char label[220];snprintf(label,sizeof(label),"DREARY VALLEY - ON FOOT\nX %d Y %d Z %d  LOADS %d/%d\nRELICS %d/2 VALUE %d/17 CP %s\n%s%s",player.x/FP,player.y/FP,player.z/FP,atlas_load_events,walk_collision_loads,relics.count,relics.value,checkpoint.active?"ACTIVE":"--",walk_collision_ready?"ORIGINAL COLLISION READY":"LOADING COLLISION",atlas_errors?" - CD ERROR":"");text(8,8,label);
#endif
#ifdef ZERA_LEVIUM_DIALOGUE
   }
   if(npc_dialogue.phase==DIALOGUE_TALK){
    text(16,146,"LEVIUM");char sentence[256];const char *source=dialogue_page(&npc_dialogue);int length=npc_dialogue.visible_chars;if(length>255)length=255;memcpy(sentence,source,length);sentence[length]=0;text(16,162,sentence);
    char footer[96];snprintf(footer,sizeof(footer),"CROSS: CONTINUE    %d/%d",npc_dialogue.visited?1:npc_dialogue.page+1,npc_dialogue.visited?1:LEVIUM_FIRST_PAGES);text(16,226,footer);
   }else if(npc_dialogue.prompt)text(16,184,"TRIANGLE: TALK TO LEVIUM");
   if(npc_dialogue.phase!=DIALOGUE_TALK)
#endif
   text(8,200,"DPAD: MOVE  CROSS: JUMP/GLIDE\nL2/R2: CAMERA L1: RECENTER R1: DASH\nSTART: MENU SELECT: RESPAWN");
#else
   char label[220];snprintf(label,sizeof(label),"%s\nTILES %d  TRIS %d  LOADS %d\n%s%s",atlas_scenes[atlas_scene].name,atlas_loaded_tiles,atlas_triangle_count,atlas_load_events,atlas_show_inactive?"ALL STATIC STATES":"OPAQUE MAP GEOMETRY",atlas_errors?" - CD ERROR":"");text(8,8,label);
   text(8,200,"DPAD: FLY  CROSS/CIRCLE: UP/DOWN\nL2/R2: TURN TRIANGLE: NEXT SECTOR\nSTART: MAPS SELECT: SPAWN SQUARE: STATES");
   #endif
   #ifdef ZERA_ATLAS_WALK
#ifdef ZERA_LEVIUM_DIALOGUE
   if(npc_dialogue.phase!=DIALOGUE_TALK)
#endif
   panel(0,46);
#else
   panel(0,38);
#endif
#ifdef ZERA_LEVIUM_DIALOGUE
   if(npc_dialogue.phase==DIALOGUE_TALK)panel(138,102);else panel(196,44);
#else
   panel(196,44);
#endif
   for(int i=0;i<atlas_loaded_tiles;i++){
    const AtlasTile *tile=&atlas_tiles[resident[i].tile];
    if(abs_i(tile->center[0]-atlas_camera[0])>16000 || abs_i(tile->center[2]-atlas_camera[2])>16000 || tile->ymin-atlas_camera[1]>16000 || tile->ymax-atlas_camera[1]<-16000)continue;
    unsigned common=31;
    for(int k=0;k<8;k++){
     ClipVertex corner={tile->center[0]+(k&1?ATLAS_CELL/2:-ATLAS_CELL/2)-atlas_camera[0],(k&2?tile->ymax:tile->ymin)-atlas_camera[1],tile->center[2]+(k&4?ATLAS_CELL/2:-ATLAS_CELL/2)-atlas_camera[2],0,0};
     common&=clip_code(&camera,&corner);
    }
    if(common)continue;
    for(int j=0;j<tile->count;j++){
#ifdef ZERA_ATLAS_WALK
     if(packet+sizeof(POLY_G3)+
#ifdef ZERA_LEVIUM_DIALOGUE
      (abs_i(player.x/FP-LEVIUM_X)<2400 && abs_i(player.z/FP-LEVIUM_Z)<2400?57344:32768)
#else
      32768
#endif
      >buffers[active].packet+PACKET_BYTES){
#else
     if(packet+sizeof(POLY_G3)>buffers[active].packet+PACKET_BYTES){
#endif
      frame_budget_drops++;break;}
     const AtlasTriangle *tri=&geometry[resident[i].start+j];if(!atlas_show_inactive && (!(tri->flags&1) || (tri->flags&6)))continue;
     draw_triangle(tri,tile,&camera);
    }
   }
#ifdef ZERA_ATLAS_WALK
   if(atlas_scene==1)draw_walking_relics(&camera);
#ifdef ZERA_LEVIUM_DIALOGUE
   draw_levium();
#endif
#endif
  }
#ifdef ZERA_ATLAS_WALK
  if(!atlas_menu){
   draw_walking_character();
   DR_TWIN *reset=primitive(0,sizeof(*reset));if(reset){RECT window={0,0,0,0};setTexWindow(reset,&window);}
  }
#endif
  atlas_drawn=frame_drawn;atlas_budget_drops=frame_budget_drops;
  flip();
 }
}
