/*
 * PSn00bSDK basic graphics example
 * (C) 2020-2023 Lameguy64, spicyjpeg - MPL licensed
 *
 * A comprehensive "advanced hello world" example showing how to set up the
 * screen with double buffering, draw basic graphics (a bouncing square) and use
 * PSn00bSDK's debug font API to quickly print some text, all while following
 * best practices. This is not necessarily the simplest hello world example and
 * may look daunting at first glance, but it is a good starting point for more
 * complex programs.
 *
 * In order to avoid cluttering the program with global variables (as many Sony
 * SDK examples and other PSn00bSDK examples written before this one do) two
 * custom structures are employed:
 *
 * - a RenderBuffer structure containing the DISPENV and DRAWENV objects that
 *   represent the location of the framebuffer in VRAM, as well as the ordering
 *   table (OT) used to sort GPU commands/primitives by their Z index and the
 *   actual buffer commands will be written to;
 * - a RenderContext structure holding two RenderBuffer instances plus some
 *   variables to keep track of which buffer is currently being drawn and how
 *   much of its primitive buffer has been filled up so far.
 *
 * A C++ version of this example is also available (see examples/hellocpp).
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <psxgpu.h>
#include <psxgte.h>
#include <inline_c.h>
#include <psxapi.h>
#include <psxpad.h>
#include <stdio.h>
#include "player.h"
#include "zera_mesh.h"
#include "mascot_materials.h"
#include "mascot_texture.h"
#include "animator.h"
#include "character.h"
#include "menu.h"
#include "audio.h"
#include "trial.h"
#include "pickup_mesh.h"
#ifdef ZERA_LAUNCH_PREVIEW
#include "launch.h"
#include "../previews/launchpad/src/launch_config.h"
static Launch launch;
#endif
#ifdef ZERA_LAUNCH_PREVIEW
#include "../previews/launchpad/src/world_mesh.h"
#define PREVIEW_TITLE "ZERA\nLAUNCHPAD PROTOTYPE"
#define EXPLORE_TEXT "EXPLORE TRAMPOLINE AREA"
#define PAUSE_ITEMS 6
#elif defined(ZERA_LEVEL3_PREVIEW)
#include "../previews/level3/src/world_mesh.h"
#define PREVIEW_TITLE "ZERA\nLEVEL3 PREVIEW"
#define EXPLORE_TEXT "EXPLORE LEVEL3 PATCH"
#define PAUSE_ITEMS 6
#else
#include "world_mesh.h"
#define PREVIEW_TITLE "ZERA\nMYTHS AWAKEN"
#define EXPLORE_TEXT "EXPLORE SPAWN AREA"
#define PAUSE_ITEMS 7
#endif
#include "world.h"
#include "camera.h"
#include "clip.h"
#ifdef ZERA_LAUNCH_PREVIEW
#include "../previews/launchpad/src/world_texture.h"
#elif defined(ZERA_LEVEL3_PREVIEW)
#include "../previews/level3/src/world_texture.h"
#else
#include "world_texture.h"
#endif

// Length of the ordering table, i.e. the range Z coordinates can have, 0-15 in
// this case. Larger values will allow for more granularity with depth (useful
// when drawing a complex 3D scene) at the expense of RAM usage and performance.
#define OT_LENGTH 512

// Size of the buffer GPU commands and primitives are written to. If the program
// crashes due to too many primitives being drawn, increase this value.
#define BUFFER_LENGTH 131072

/* Framebuffer/display list class */

typedef struct {
	DISPENV disp_env;
	DRAWENV draw_env;

	uint32_t ot[OT_LENGTH];
	uint8_t  buffer[BUFFER_LENGTH];
} RenderBuffer;

typedef struct {
	RenderBuffer buffers[2];
	uint8_t      *next_packet;
	int          active_buffer;
} RenderContext;

void setup_context(RenderContext *ctx, int w, int h, int r, int g, int b) {
	// Place the two framebuffers vertically in VRAM.
	SetDefDrawEnv(&(ctx->buffers[0].draw_env), 0, 0, w, h);
	SetDefDispEnv(&(ctx->buffers[0].disp_env), 0, 0, w, h);
	SetDefDrawEnv(&(ctx->buffers[1].draw_env), 0, h, w, h);
	SetDefDispEnv(&(ctx->buffers[1].disp_env), 0, h, w, h);

	// Set the default background color and enable auto-clearing.
	setRGB0(&(ctx->buffers[0].draw_env), r, g, b);
	setRGB0(&(ctx->buffers[1].draw_env), r, g, b);
	ctx->buffers[0].draw_env.isbg = 1;
	ctx->buffers[1].draw_env.isbg = 1;

	// Initialize the first buffer and clear its OT so that it can be used for
	// drawing.
	ctx->active_buffer = 0;
	ctx->next_packet   = ctx->buffers[0].buffer;
	ClearOTagR(ctx->buffers[0].ot, OT_LENGTH);

	// Turn on the video output.
	SetDispMask(1);
}

void flip_buffers(RenderContext *ctx) {
	// Wait for the GPU to finish drawing, then wait for vblank in order to
	// prevent screen tearing.
	DrawSync(0);
	VSync(0);

	RenderBuffer *draw_buffer = &(ctx->buffers[ctx->active_buffer]);
	RenderBuffer *disp_buffer = &(ctx->buffers[ctx->active_buffer ^ 1]);

	// Display the framebuffer the GPU has just finished drawing and start
	// rendering the display list that was filled up in the main loop.
	PutDispEnv(&(disp_buffer->disp_env));
	DrawOTagEnv(&(draw_buffer->ot[OT_LENGTH - 1]), &(draw_buffer->draw_env));

	// Switch over to the next buffer, clear it and reset the packet allocation
	// pointer.
	ctx->active_buffer ^= 1;
	ctx->next_packet    = disp_buffer->buffer;
	ClearOTagR(disp_buffer->ot, OT_LENGTH);
}

void *new_primitive(RenderContext *ctx, int z, size_t size) {
	// Place the primitive after all previously allocated primitives, then
	// insert it into the OT and bump the allocation pointer.
	RenderBuffer *buffer = &(ctx->buffers[ctx->active_buffer]);
	uint8_t      *prim   = ctx->next_packet;

	if (z < 0 || z >= OT_LENGTH || prim + size > buffer->buffer + BUFFER_LENGTH) return NULL;
	addPrim(&(buffer->ot[z]), prim);
	ctx->next_packet += size;

	// Make sure we haven't yet run out of space for future primitives.
	assert(ctx->next_packet <= &(buffer->buffer[BUFFER_LENGTH]));

	return (void *) prim;
}

// A simple helper for drawing text using PSn00bSDK's debug font API. Note that
// FntSort() requires the debug font texture to be uploaded to VRAM beforehand
// by calling FntLoad().
void draw_text(RenderContext *ctx, int x, int y, int z, const char *text) {
	RenderBuffer *buffer = &(ctx->buffers[ctx->active_buffer]);
	if(ctx->next_packet + 8192 > buffer->buffer + BUFFER_LENGTH)return;

	ctx->next_packet = (uint8_t *)
		FntSort(&(buffer->ot[z]), ctx->next_packet, x, y, text);

	assert(ctx->next_packet <= &(buffer->buffer[BUFFER_LENGTH]));
}

static RenderContext ctx;
static ClipCamera clip_camera;
static unsigned int world_codes[WORLD_UNIQUE_COUNT],world_code_stamp[WORLD_UNIQUE_COUNT];
static unsigned int view_stamp=0;
static uint8_t pads[2][34];
static Player player;
static int yaw=512;
static SVECTOR pose[ANIM_VERTICES];
static Animator animator;
static Menu menu;
static Trial trial;
static volatile int facing=0,mascot_visible=1;
static int camera_height=0,camera_distance=CAMERA_DISTANCE;
static int camera_orbit_cooldown=0;
static const char *names[]={"GROUND","JUMP","FALL","GLIDE","DASH"};
static volatile int player_respawn_events=0,simulation_ticks=0,debug_input_x=0,debug_input_z=0,debug_movement_yaw=0,debug_actual_moving=0;
static void reset_view(void){
#ifdef ZERA_LAUNCH_PREVIEW
launch_cancel(&launch);
#endif
animator_init(&animator);camera_height=0;camera_distance=CAMERA_DISTANCE;camera_orbit_cooldown=0;facing=0;yaw=512;mascot_visible=1;}
static int camera_view(int angle,int height,MATRIX *m){
 SVECTOR rot={280,angle,0,0};RotMatrix(&rot,m);
 int x=(-100*m->m[1][0]-CAMERA_DISTANCE*m->m[2][0])/4096;
 int y=(100*m->m[1][1]+CAMERA_DISTANCE*m->m[2][1])/4096;
 int z=(-100*m->m[1][2]-CAMERA_DISTANCE*m->m[2][2])/4096;
 return world_camera_fraction(player.x/FP,height,player.z/FP,x,y,z);
}
/* Clip against near and guarded viewport planes before GTE projection. */
static int project(const ClipVertex *a,const ClipVertex *b,const ClipVertex *c,short xy[6]){
 SVECTOR va={a->x,a->y,a->z,0},vb={b->x,b->y,b->z,0},vc={c->x,c->y,c->z,0};
 int flag,z0,z1,z2,depth;
 gte_ldv3(&va,&vb,&vc);gte_rtpt();gte_stflg(&flag);if(flag&0x80000000)return 0;
 gte_stsz3(&z0,&z1,&z2);if(z0<64 || z1<64 || z2<64)return 0;
 gte_stsxy3(&xy[0],&xy[2],&xy[4]);gte_avsz3();gte_stotz(&depth);
 depth>>=3;if(depth>=OT_LENGTH)depth=OT_LENGTH-1;if(depth<1)depth=1;return depth;
}
static void triangle(SVECTOR a,SVECTOR b,SVECTOR c,int r,int g,int bl){
 /* Character triangles retain conservative GTE rejection. World geometry
    uses the general clipper; avoiding it here reduces repeated CPU work. */
 ClipVertex va={a.vx,a.vy,a.vz,0,0},vb={b.vx,b.vy,b.vz,0,0},vc={c.vx,c.vy,c.vz,0,0};
 short xy[6];int depth=project(&va,&vb,&vc,xy);if(!depth)return;
 POLY_F3 *p=new_primitive(&ctx,depth,sizeof(*p));if(!p)return;
 setPolyF3(p);setRGB0(p,r,g,bl);setXY3(p,xy[0],xy[1],xy[2],xy[3],xy[4],xy[5]);
}

static void world_triangle(int i){
 const unsigned char *u=world_uv[i];ClipVertex in[3],out[10];
 for(int k=0;k<3;k++){const SVECTOR *v=&world_unique[world_corner_ids[i][k]];in[k]=(ClipVertex){v->vx,v->vy,v->vz,u[k*2],u[k*2+1]};}
 unsigned int codes[3];
 for(int k=0;k<3;k++){
  unsigned int id=world_corner_ids[i][k];
  if(world_code_stamp[id]!=view_stamp){world_codes[id]=clip_code(&clip_camera,&in[k]);world_code_stamp[id]=view_stamp;}
  codes[k]=world_codes[id];
 }
 int n=clip_triangle_known(&clip_camera,in,codes,out);
 for(int k=1;k<n-1;k++){
  ClipVertex *a=&out[0],*b=&out[k],*c=&out[k+1];short xy[6];int depth=project(a,b,c,xy);if(!depth)continue;
  POLY_FT3 *p=new_primitive(&ctx,depth,sizeof(*p));if(!p)return;
  const unsigned char *col=world_colors[i];setPolyFT3(p);setRGB0(p,col[0]/2,col[1]/2,col[2]/2);
  setXY3(p,xy[0],xy[1],xy[2],xy[3],xy[4],xy[5]);setUV3(p,a->u,a->v,b->u,b->v,c->u,c->v);
  p->tpage=getTPage(1,0,512,0);p->clut=getClut(512,256);
  DR_TWIN *tw=new_primitive(&ctx,depth,sizeof(*tw));if(!tw)return;
  int tile=world_tile[i];RECT window={(tile%4)*64,(tile/4)*64,64,64};setTexWindow(tw,&window);
 }
}
static void ui_tile(int x,int y,int w,int h,int r,int g,int b){
 TILE *t=new_primitive(&ctx,0,sizeof(*t));if(!t)return;
 setTile(t);setXY0(t,x,y);setWH(t,w,h);setRGB0(t,r,g,b);
}
static void draw_menu(void){
 char text[512];
 if(menu.screen==MENU_CONTROLS){
  draw_text(&ctx,48,58,0,"CONTROLS\n\nDPAD / LEFT STICK   MOVE\nCROSS              JUMP\nHOLD CROSS         GLIDE\nR1                 DASH\nL2 / R2            CAMERA\nL1                 RECENTER\nSTART              PAUSE\nSELECT             RESPAWN\n\nCROSS / CIRCLE     BACK");
#ifdef ZERA_LAUNCH_PREVIEW
  draw_text(&ctx,32,216,0,"TRIANGLE: LAUNCH NEAR TRAMPOLINE");
#endif
  ui_tile(24,42,272,160,14,22,36);ui_tile(22,40,276,164,100,74,110);return;
 }
 if(menu.screen==MENU_TITLE){
  snprintf(text,sizeof(text),PREVIEW_TITLE "\n\n%s " EXPLORE_TEXT "\n\n%s CONTROLS\n\n%s DIAGNOSTICS: %s\n\nCROSS SELECT   UP/DOWN MOVE",menu.selection==0?">":" ",menu.selection==1?">":" ",menu.selection==2?">":" ",menu.debug?"ON":"OFF");
  draw_text(&ctx,48,56,0,text);
  draw_text(&ctx,40,216,0,"PS1 ADAPTATION  WIP09 / PROTOTYPE");
  ui_tile(40,78+menu.selection*16,240,15,58,36,70);
 }else{
  const char *items[]={"RESUME","RESPAWN","CONTROLS","RETURN TO TITLE","DIAGNOSTICS","AUDIO","TEST: PICKUP TRIAL"};
  int used=snprintf(text,sizeof(text),"PAUSED\n\n");
  for(int n=0;n<PAUSE_ITEMS;n++){
   used+=snprintf(text+used,sizeof(text)-used,"%s %s%s%s\n\n",menu.selection==n?">":" ",items[n],n==4 || n==5?": ":"",n==4?(menu.debug?"ON":"OFF"):n==5?(menu.muted?"OFF":"ON"):"");
  }
  draw_text(&ctx,48,48,0,text);ui_tile(40,62+menu.selection*16,240,15,58,36,70);
 }
 ui_tile(24,40,272,160,14,22,36);ui_tile(22,38,276,164,100,74,110);
}
int main(void){
 SetVideoMode(MODE_NTSC); ResetGraph(0); InitGeom(); gte_SetGeomOffset(160,110);gte_SetGeomScreen(256);
 RECT texrect={512,0,128,256},palrect={512,256,256,1};
 LoadImage(&texrect,world_texture);LoadImage(&palrect,world_clut);DrawSync(0);
 RECT mascotrect={640,0,128,128},mascotpal={512,257,256,1};
 LoadImage(&mascotrect,mascot_texture);LoadImage(&mascotpal,mascot_clut);DrawSync(0);
 FntLoad(960,0);setup_context(&ctx,320,240,24,32,56);
 InitPAD(pads[0],34,pads[1],34);StartPAD();ChangeClearPAD(0);
 player_init(&player);animator_init(&animator);menu_init(&menu);trial_clear(&trial);audio_init();uint16_t old=0;
 for(;;){
  PADTYPE *pad=(PADTYPE*)pads[0];uint16_t held=0;
  if(pad->stat==0 && (pad->type==PAD_ID_DIGITAL || pad->type==PAD_ID_ANALOG || pad->type==PAD_ID_ANALOG_STICK))held=(uint16_t)~pad->btn;
  uint16_t pressed=held & ~old;old=held;
  unsigned ui=(pressed&PAD_UP?UI_UP:0)|(pressed&PAD_DOWN?UI_DOWN:0)|(pressed&PAD_CROSS?UI_ACCEPT:0)|(pressed&PAD_CIRCLE?UI_BACK:0)|(pressed&PAD_START?UI_START:0);
  int previous_selection=menu.selection;int before=menu.screen,action=menu_update(&menu,ui);
  audio_set_muted(menu.muted);
  if(before!=MENU_PLAY && (ui&(UI_UP|UI_DOWN)) && menu.selection!=previous_selection)audio_play(SFX_UI_MOVE);
  if(ui&(UI_ACCEPT|UI_BACK|UI_START))if(before!=MENU_PLAY || menu.screen!=MENU_PLAY)audio_play(SFX_UI_ACCEPT);
  if(before==MENU_PLAY && menu.screen==MENU_PLAY && (pressed&PAD_SELECT))action|=MENU_RESET;
  if(action&MENU_RESET){player_init(&player);reset_view();}
  if(action&MENU_TRIAL)trial_start(&trial);
  else if((action&MENU_RESET) && (before==MENU_TITLE || menu.screen==MENU_TITLE))trial_clear(&trial);
  int paused=menu.screen!=MENU_PLAY || before!=MENU_PLAY || (action&MENU_RESET);
  Input in={(!!(held&PAD_RIGHT))-(!!(held&PAD_LEFT)),(!!(held&PAD_UP))-(!!(held&PAD_DOWN)),!!(pressed&PAD_CROSS),!!(held&PAD_CROSS),!!(pressed&PAD_R1)};
  if(pad->stat==0 && (pad->type==PAD_ID_ANALOG || pad->type==PAD_ID_ANALOG_STICK)){
   if(pad->ls_x<96)in.x=-1;else if(pad->ls_x>160)in.x=1;
   if(pad->ls_y<96)in.z=1;else if(pad->ls_y>160)in.z=-1;
  }
  debug_input_x=in.x;debug_input_z=in.z;
  int movement_yaw=yaw;debug_movement_yaw=movement_yaw;
  in.camera_c=rcos(movement_yaw);in.camera_s=rsin(movement_yaw);
  int oldx=player.x,oldz=player.z,respawned=0;
  int oldstate=player.state,olddash=player.dash_ticks;
  if(!paused){
   simulation_ticks++;
#ifdef ZERA_LAUNCH_PREVIEW
   if((pressed&PAD_TRIANGLE) && launch_begin(&launch,&player,&launch_config))facing=LAUNCH_FACING;
   if(launch.active){
    if(launch_tick(&launch,&player,&launch_config)){
     int floor;
     if(world_floor(player.x/FP,player.z/FP,player.y/FP+8,&floor) && floor*FP>=player.y-48*FP){player.y=floor*FP;player.state=GROUND;}
    }
   }else
#endif
   if(player_tick(&player,in)){reset_view();player_respawn_events++;respawned=1;}
   if(held&PAD_L2)yaw-=16;if(held&PAD_R2)yaw+=16;if(pressed&PAD_L1)yaw=0;
  }
  if(!paused){
   if(oldstate==GROUND && player.state==JUMP)audio_play(SFX_JUMP);
   if(oldstate!=GROUND && player.state==GROUND)audio_play(SFX_LAND);
   if(!olddash && player.dash_ticks)audio_play(SFX_DASH);
   if(oldstate!=GLIDE && player.state==GLIDE)audio_play(SFX_FLAP);
  }
  if(trial_update(&trial,&player,!paused))audio_play(SFX_PICKUP);
  audio_update(menu.screen!=MENU_PLAY);
  int moved=!paused && !respawned && (player.x!=oldx || player.z!=oldz);
  debug_actual_moving=moved;
  #ifdef ZERA_LAUNCH_PREVIEW
  if(!launch.active)
#endif
  facing=character_facing_step(facing,in.x,in.z,movement_yaw,!paused && !respawned);
  int desired=character_animation(player.state,moved);
  animator_update(&animator,desired,!paused);
  int fc=rcos(facing),fs=rsin(facing);
  for(int i=0;i<ANIM_VERTICES;i++){
   int vx=animator.local[i].x,vz=animator.local[i].z;
   pose[i].vx=(vx*fc+vz*fs)/4096;pose[i].vy=animator.local[i].y;
   pose[i].vz=(-vx*fs+vz*fc)/4096;
  }
  if(!paused){
#ifdef ZERA_LAUNCH_PREVIEW
   /* The recovered launch rises much faster than a normal jump. Keep the
      character in view instead of carrying a multi-tick vertical lag. */
   if(launch.active)camera_height=player.y/FP;
   else
#endif
   camera_height+=(player.y/FP-camera_height)/8;
  }
  MATRIX m;int fraction=camera_view(yaw,camera_height,&m);
  if(!paused && camera_orbit_cooldown)camera_orbit_cooldown--;
  /* Avoid changing the movement basis under an active movement command.
     Manual camera input and pause always take priority over fallback. */
  if(!paused && !in.x && !in.z && !(held&(PAD_L1|PAD_L2|PAD_R2)) &&
     !camera_orbit_cooldown && fraction<2048){
   MATRIX left,right;
   int lf=camera_view(yaw+512,camera_height,&left);
   int rf=camera_view(yaw-512,camera_height,&right);
   int offset=camera_orbit_offset(fraction,lf,rf);
   if(offset){
    yaw+=offset;m=offset>0?left:right;fraction=offset>0?lf:rf;
    /* An orbit cut is already immediate. Start at the tested side-view
       clearance instead of carrying the old wall's close-up into this view. */
    camera_distance=camera_distance_step(CAMERA_DISTANCE,fraction,0);
    camera_orbit_cooldown=30;
   }
  }
  VECTOR target={player.x/FP,-camera_height,player.z/FP},turned;
  ApplyMatrixLV(&m,&target,&turned);
  camera_distance=camera_distance_step(camera_distance,fraction,paused);
  mascot_visible=character_visible_step(mascot_visible,camera_distance);
  VECTOR pos={-turned.vx,100*camera_distance/CAMERA_DISTANCE-turned.vy,-turned.vz+camera_distance};TransMatrix(&m,&pos);gte_SetRotMatrix(&m);gte_SetTransMatrix(&m);
  for(int r=0;r<3;r++){for(int c=0;c<3;c++)clip_camera.m[r][c]=m.m[r][c];clip_camera.t[r]=m.t[r];}
  if(++view_stamp==0){for(int i=0;i<WORLD_UNIQUE_COUNT;i++)world_code_stamp[i]=0;view_stamp=1;}
  int wx=player.x/FP,wz=player.z/FP;
  for(int cell=0;cell<WORLD_CELL_COUNT;cell++){
   const short *b=world_cells[cell];
   if(b[2]<wx-1280 || b[0]>wx+1280 || b[3]<wz-1280 || b[1]>wz+1280)continue;
   unsigned int common=~0u;
   for(int k=0;k<8;k++){
    ClipVertex corner={k&1?b[2]:b[0],k&2?b[7]:b[6],k&4?b[3]:b[1],0,0};
    common &= clip_code(&clip_camera,&corner);
   }
   if(common)continue;
   for(int i=b[4];i<b[4]+b[5];i++)world_triangle(i);
  }
  if(trial.active){
   for(int id=0;id<TRIAL_PICKUPS;id++){
    if(trial.collected&(1u<<id))continue;
    int angle=trial.ticks*40+id*200,cs=rcos(angle),sn=rsin(angle),bob=rsin(angle*2)*8/4096;
    SVECTOR points[PICKUP_VERTEX_COUNT];
    for(int k=0;k<PICKUP_VERTEX_COUNT;k++){
     const SVECTOR *v=&pickup_vertices[k];
     points[k]=(SVECTOR){trial_positions[id][0]+(v->vx*cs+v->vz*sn)/4096,80-trial_positions[id][1]+v->vy+bob,trial_positions[id][2]+(-v->vx*sn+v->vz*cs)/4096,0};
    }
    for(int k=0;k<PICKUP_FACE_COUNT;k++){
     const unsigned short *f=pickup_faces[k];int light=150+(k%4)*25;
     triangle(points[f[0]],points[f[1]],points[f[2]],light,light*4/5,45);
    }
   }
  }
  int x=player.x/FP,y=80-player.y/FP,z=player.z/FP;
  if(mascot_visible)for(int order=0;order<ZERA_FACE_COUNT;order++){
   int i=mascot_draw_order[order];
   const unsigned short *f=zera_faces[i];
   SVECTOR a=pose[f[0]],b=pose[f[1]],c=pose[f[2]];
   a.vx+=x;b.vx+=x;c.vx+=x;a.vy+=y;b.vy+=y;c.vy+=y;a.vz+=z;b.vz+=z;c.vz+=z;
   ClipVertex va={a.vx,a.vy,a.vz,0,0},vb={b.vx,b.vy,b.vz,0,0},vc={c.vx,c.vy,c.vz,0,0};
   short xy[6];int depth=project(&va,&vb,&vc,xy);if(!depth)continue;
   const unsigned char *col=mascot_corner_colors[i];int material=mascot_material[i];
   if(material){
    POLY_GT3 *p=new_primitive(&ctx,depth,sizeof(*p));if(!p)continue;
    const unsigned char *uv=mascot_uv[i];setPolyGT3(p);
    setRGB0(p,col[0]/2,col[1]/2,col[2]/2);setRGB1(p,col[3]/2,col[4]/2,col[5]/2);setRGB2(p,col[6]/2,col[7]/2,col[8]/2);
    setXY3(p,xy[0],xy[1],xy[2],xy[3],xy[4],xy[5]);setUV3(p,uv[0],uv[1],uv[2],uv[3],uv[4],uv[5]);
    p->tpage=getTPage(1,0,640,0);p->clut=getClut(512,257);
    DR_TWIN *tw=new_primitive(&ctx,depth,sizeof(*tw));if(!tw)continue;
    RECT window={material==2?128:0,0,128,128};setTexWindow(tw,&window);
   }else{
    POLY_G3 *p=new_primitive(&ctx,depth,sizeof(*p));if(!p)continue;
    setPolyG3(p);setRGB0(p,col[0],col[1],col[2]);setRGB1(p,col[3],col[4],col[5]);setRGB2(p,col[6],col[7],col[8]);
    setXY3(p,xy[0],xy[1],xy[2],xy[3],xy[4],xy[5]);
   }
  }
  if(menu.screen==MENU_PLAY){
   if(menu.debug){
    char text[256];snprintf(text,sizeof(text),"ZERA PS1 WIP09\n%s X:%d Y:%d Z:%d\nCLIP:%d BLEND:%d CAM:%d",names[player.state],x,player.y/FP,z,animator.clip,animator.blend_tick,camera_distance);
    draw_text(&ctx,8,8,0,text);
   }
#ifdef ZERA_LAUNCH_PREVIEW
   draw_text(&ctx,8,184,0,launch.active?"ORIGINAL LAUNCH ARC\nIN FLIGHT":launch_can_start(&launch,&player,&launch_config)?"TRIANGLE: LAUNCH\nPROTOTYPE ACTIVATION":launch.completed?"LANDING REACHED\nSELECT: RETURN TO PAD":"RETURN NEAR PAD TO LAUNCH");
#endif
   if(trial.active){
    char status[192],best[40];int tenths=trial.ticks/3;
    if(trial.best_valid){int bt=trial.best_ticks/3;snprintf(best,sizeof(best),"BEST %d.%d S",bt/10,bt%10);}
    else snprintf(best,sizeof(best),"BEST --");
    snprintf(status,sizeof(status),"PICKUP TRIAL %d/%d\nNEW TEST LAYOUT\nSIM TIME %d.%d S\n%s%s",trial.count,TRIAL_PICKUPS,tenths/10,tenths%10,best,trial.completed?"\nTRIAL COMPLETE":"");
    draw_text(&ctx,8,176,0,status);
   }
   draw_text(&ctx,8,224,0,"START MENU    SELECT RESPAWN");
  }else draw_menu();
  DR_TWIN *tw=new_primitive(&ctx,0,sizeof(*tw));if(tw){RECT reset={0,0,0,0};setTexWindow(tw,&reset);}
  VSync(0); /* Together with flip_buffers: 30 Hz NTSC. */
  flip_buffers(&ctx);
 }
}
