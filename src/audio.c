/* SPU music feed follows PSn00bSDK cdstream example, spicyjpeg, MPL-2.0. */
#include <stdint.h>
#include <string.h>
#include <psxspu.h>
#include <psxcd.h>
#include <psxgpu.h>
#include <hwregs_c.h>
#include "stream.h"
#include "audio.h"
#include "audio_samples.h"
static Stream_Context music;
static struct {int lba,sectors,next,last;volatile int pending,refill;} reader;
static int sample_addr[7],next_voice=1;
volatile int audio_music_ready,audio_underruns,audio_cd_errors,audio_refills,audio_wraps;
int audio_sfx_events[7];
int audio_muted;
void audio_set_muted(int muted){
 muted=!!muted;
 if(muted==audio_muted)return;
 audio_muted=muted;
 if(muted){
  /* Silence resident tails as well as music; keep CD/SPU stream state alive. */
  SpuSetKey(0,0x1fe);
  for(int ch=0;ch<=8;ch++)SPU_CH_VOL_L(ch)=SPU_CH_VOL_R(ch)=0;
 }
}
static void underrun(void){audio_underruns++;}
static void read_done(CdlIntrResult event,uint8_t *payload){
 (void)payload;
 if(event==CdlDiskError){audio_cd_errors++;reader.next=reader.last;}
 else{Stream_Feed(&music,reader.refill*2048);audio_refills++;}
 reader.pending=0;
}
static int feed(void){
 if(reader.pending || CdReadSync(1,0)>0)return 1;
 if(Stream_GetRefillLength(&music)<8192)return 0;
 uint8_t *ptr;int sectors=Stream_GetFeedPtr(&music,&ptr)/2048;
 if(!sectors)return 0;
 int next=reader.next;if(next>=reader.sectors){next=0;audio_wraps++;}
 int available=reader.sectors-next;if(sectors>available)sectors=available;
 if(sectors<=0)return 0;
 CdlLOC pos;CdIntToPos(reader.lba+next,&pos);
 reader.last=next;reader.refill=sectors;reader.pending=1;reader.next=next+sectors;
 CdControl(CdlSetloc,&pos,0);CdReadCallback(read_done);
 if(!CdRead(sectors,(uint32_t*)ptr,CdlModeSpeed)){reader.pending=0;reader.next=next;audio_cd_errors++;return 0;}
 return 1;
}
void audio_play(int sample){
 if(audio_muted || sample<0 || sample>=7)return;
 int ch=next_voice;next_voice=next_voice==8?1:next_voice+1;
 SpuSetKey(0,1u<<ch);SPU_CH_FREQ(ch)=getSPUSampleRate(22050);
 SPU_CH_ADDR(ch)=getSPUAddr(sample_addr[sample]);SPU_CH_LOOP_ADDR(ch)=getSPUAddr(0x1000);
 SPU_CH_VOL_L(ch)=0x2400;SPU_CH_VOL_R(ch)=0x2400;
 SPU_CH_ADSR1(ch)=0x00ff;SPU_CH_ADSR2(ch)=0x0000;
 SpuSetKey(1,1u<<ch);audio_sfx_events[sample]++;
}
void audio_init(void){
 SpuInit();SpuSetKey(0,0xffffff);
 for(int ch=0;ch<24;ch++){SPU_CH_ADDR(ch)=getSPUAddr(0x1000);SPU_CH_FREQ(ch)=0x1000;SPU_CH_VOL_L(ch)=SPU_CH_VOL_R(ch)=0;}
 SpuSetKey(1,0xffffff);
 int addr=0x6000;SpuSetTransferMode(SPU_TRANSFER_BY_DMA);
 for(int i=0;i<7;i++){
  sample_addr[i]=addr;SpuSetTransferStartAddr(addr);SpuWrite(sfx_samples[i].data,sfx_samples[i].size);SpuIsTransferCompleted(SPU_TRANSFER_WAIT);addr+=sfx_samples[i].size;
 }
 if(addr>=0x80000)return;
 CdInit();CdlFILE file;if(!CdSearchFile(&file,"\\MUSIC.VAG;1"))return;
 uint32_t header[512];CdReadCallback(0);CdControl(CdlSetloc,&file.pos,0);CdRead(1,header,CdlModeSpeed);
 if(CdReadSync(0,0)<0)return;
 const uint8_t *v=(const uint8_t*)header;
 if(memcmp(v,"VAGi",4) || header[2]!=4096)return;
 int length=__builtin_bswap32(header[3]),rate=__builtin_bswap32(header[4]);
 if(length<=0 || length%4096 || rate!=22050)return;
 Stream_Config config;memset(&config,0,sizeof(config));
 config.spu_address=0x1010;config.channel_mask=1;config.interleave=4096;config.buffer_size=65536;config.sample_rate=rate;config.underrun_callback=underrun;
 Stream_Init(&music,&config);reader.lba=CdPosToInt(&file.pos)+1;reader.sectors=length/2048;
 int start=VSync(-1);
 while(feed()){if(VSync(-1)-start>180 || audio_cd_errors>3)return;}
 SPU_CH_VOL_L(0)=SPU_CH_VOL_R(0)=0x1200;
 if(Stream_Start(&music,0))audio_music_ready=1;
}
void audio_update(int duck){
 if(!audio_music_ready)return;
 feed();SPU_CH_VOL_L(0)=SPU_CH_VOL_R(0)=audio_muted?0:duck?0x0900:0x1200;
}
