/* Offline PCM16 mono -> raw PS1 ADPCM. Exhaustive filter/shift block search. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <limits.h>
static const int f0[]={0,60,115,98,122},f1[]={0,0,-52,-55,-60};
static int clamp(int x,int a,int b){return x<a?a:x>b?b:x;}
int main(int argc,char **argv){
 if(argc!=4){fprintf(stderr,"encode_spu input.pcm output.adpcm chunk_bytes (0=oneshot)\n");return 1;}
 FILE *in=fopen(argv[1],"rb"),*out=fopen(argv[2],"wb");if(!in || !out)return 2;
 int chunk=atoi(argv[3]),h1=0,h2=0,block=0;int16_t samples[28];size_t got;
 while((got=fread(samples,sizeof(int16_t),28,in))){
  for(size_t i=got;i<28;i++)samples[i]=0;
  int64_t best=INT64_MAX;int bp=0,bs=0,bh1=0,bh2=0;unsigned char packed[14]={0};
  for(int p=0;p<5;p++)for(int s=0;s<=12;s++){
   if(!block && p)continue;
   int a=h1,b=h2,step=1<<(12-s);int64_t error=0;unsigned char candidate[14]={0};
   for(int i=0;i<28;i++){
    int pred=(a*f0[p]+b*f1[p]+32)>>6,res=samples[i]-pred;
    int q=res>=0?(res+step/2)/step:-((-res+step/2)/step);q=clamp(q,-8,7);
    int dec=clamp(pred+q*step,-32768,32767),e=samples[i]-dec;error+=(int64_t)e*e;
    candidate[i/2]|=(q&15)<<((i&1)*4);b=a;a=dec;
   }
   if(error<best){best=error;bp=p;bs=s;bh1=a;bh2=b;for(int i=0;i<14;i++)packed[i]=candidate[i];}
  }
  h1=bh1;h2=bh2;fputc((bp<<4)|bs,out);fputc(chunk && ((block+1)*16)%chunk==0?3:0,out);fwrite(packed,1,14,out);block++;
 }
 if(chunk){
  while((block*16)%chunk){unsigned char zero[16]={0};if(((block+1)*16)%chunk==0)zero[1]=3;fwrite(zero,1,16,out);block++;}
 }else{
  /* Separate silent end block, so the last real samples are not truncated. */
  unsigned char end[16]={0,1};fwrite(end,1,16,out);block++;
  while((block*16)%64){unsigned char zero[16]={0};fwrite(zero,1,16,out);block++;}
 }
 fclose(in);fclose(out);return 0;
}
