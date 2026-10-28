"""Reference SPU ADPCM block decoder used for offline quality checks."""
import numpy as np
def decode(data):
 h1=h2=0;out=[];f0=[0,60,115,98,122];f1=[0,0,-52,-55,-60]
 for k in range(0,len(data),16):
  b=data[k:k+16];f=b[0]>>4;s=b[0]&15
  assert f<=4 and s<=12
  for i in range(28):
   q=(b[2+i//2]>>((i&1)*4))&15;q=q-16 if q>=8 else q
   sample=max(-32768,min(32767,(q*(1<<(12-s)))+((h1*f0[f]+h2*f1[f]+32)>>6)));out.append(sample);h2=h1;h1=sample
 return np.array(out,dtype=np.int16)
