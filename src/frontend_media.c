#include <stdint.h>
#include <string.h>
#include <psxgpu.h>
#include <psxspu.h>
#include <hwregs_c.h>
#include "frontend_media.h"
#include "../previews/frontend/src/frontend_assets.h"
static unsigned char *logo_data;
volatile int front_media_ready,front_audio_track,front_logo_frame=-1,front_media_errors;
int front_sfx_events[7];
static int music_level=4,effects_level=4;
void frontend_media_levels(int music,int effects){
 music_level=music<0?0:music>4?4:music;effects_level=effects<0?0:effects>4?4:effects;
 SPU_CH_VOL_L(0)=SPU_CH_VOL_R(0)=0x2000*music_level/4;
 for(int ch=2;ch<9;ch++)SPU_CH_VOL_L(ch)=SPU_CH_VOL_R(ch)=0x2000*effects_level/4;
}
void frontend_media_mute(int muted){SPU_MASTER_VOL_L=SPU_MASTER_VOL_R=muted?0:0x3fff;}
void frontend_media_track(int track){
 SpuSetKey(0,3);front_audio_track=track;
 if(!front_media_ready || !track)return;
 int id=track==1?0:1,ch=track==1?1:0;
 SPU_CH_ADDR(ch)=getSPUAddr(frontend_samples[id].address);
 SPU_CH_LOOP_ADDR(ch)=getSPUAddr(frontend_samples[id].address);
 SPU_CH_FREQ(ch)=getSPUSampleRate(frontend_samples[id].rate);
 SPU_CH_VOL_L(ch)=SPU_CH_VOL_R(ch)=0x2000*(track==1?4:music_level)/4;
 SPU_CH_ADSR1(ch)=0x00ff;SPU_CH_ADSR2(ch)=0;
 SpuSetKey(1,1u<<ch);
}
void frontend_media_effect(int effect){
 if(!front_media_ready || effect<0 || effect>=7)return;
 int id=effect+2,ch=effect+2;
 SpuSetKey(0,1u<<ch);SPU_CH_ADDR(ch)=getSPUAddr(frontend_samples[id].address);SPU_CH_LOOP_ADDR(ch)=getSPUAddr(0x1000);
 SPU_CH_FREQ(ch)=getSPUSampleRate(frontend_samples[id].rate);SPU_CH_VOL_L(ch)=SPU_CH_VOL_R(ch)=0x2000*effects_level/4;
 SPU_CH_ADSR1(ch)=0x00ff;SPU_CH_ADSR2(ch)=0;SpuSetKey(1,1u<<ch);front_sfx_events[effect]++;
}
int frontend_media_load(FrontendRead read,void *staging,size_t size){
 front_media_ready=0;if(size<FRONT_STAGING_BYTES)return 0;
 if(!read(0,1,staging))return 0;
 uint32_t h[12];memcpy(h,staging,sizeof(h));
 if(memcmp(h,"ZFE00001",8) || memcmp((unsigned char*)h+8,frontend_tag,16) || h[6]!=FRONT_LOGO_WIDTH || h[7]!=FRONT_LOGO_HEIGHT || h[8]!=FRONT_LOGO_FPS || h[9]!=FRONT_LOGO_FRAMES || h[10]!=FRONT_LOGO_TICKS || h[11]!=FRONT_FRAME_BYTES){front_media_errors++;return 0;}
 SpuInit();SpuSetKey(0,0xffffff);frontend_media_mute(0);SpuSetTransferMode(SPU_TRANSFER_BY_DMA);
 if(!read(FRONT_TITLE_SECTOR,FRONT_TITLE_SECTORS,staging))return 0;
 RECT title={512,320,256,144};LoadImage(&title,staging);DrawSync(0);
 for(unsigned i=0;i<sizeof(frontend_samples)/sizeof(*frontend_samples);i++){
  if((size_t)frontend_samples[i].sectors*2048>size || frontend_samples[i].address+frontend_samples[i].size>0x80000){front_media_errors++;return 0;}
  if(!read(frontend_samples[i].sector,frontend_samples[i].sectors,staging))return 0;
  SpuSetTransferStartAddr(frontend_samples[i].address);SpuWrite(staging,frontend_samples[i].size);SpuIsTransferCompleted(SPU_TRANSFER_WAIT);
 }
 if(!read(FRONT_LOGO_SECTOR,FRONT_LOGO_SECTORS,staging))return 0;
 logo_data=staging;front_media_ready=1;frontend_media_logo(0);frontend_media_track(1);return 1;
}
void frontend_media_logo(int tick){
 if(!front_media_ready)return;
 int frame=tick*FRONT_LOGO_FPS/60;if(frame>=FRONT_LOGO_FRAMES)frame=FRONT_LOGO_FRAMES-1;
 if(frame==front_logo_frame)return;
 DrawSync(0);unsigned char *source=logo_data+frame*FRONT_FRAME_BYTES;
 RECT palette={768,128,16,1},image={768,0,FRONT_LOGO_WIDTH/4,FRONT_LOGO_HEIGHT};
 LoadImage(&palette,(uint32_t*)source);LoadImage(&image,(uint32_t*)(source+32));DrawSync(0);front_logo_frame=frame;
}
