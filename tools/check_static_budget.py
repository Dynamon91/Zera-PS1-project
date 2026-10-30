"""Check ELF text+data+BSS against a conservative static main-RAM budget."""
import hashlib,json,subprocess,sys
from pathlib import Path

def check(path):
    path=Path(path)
    output=subprocess.run(['mipsel-none-elf-size','-B',str(path)],check=True,capture_output=True,text=True).stdout
    fields=output.splitlines()[-1].split();text,data,bss=map(int,fields[:3])
    total=text+data+bss;limit=1536*1024
    if total>=limit:raise ValueError(f'Static budget exceeded: {total} >= {limit}; inspect RAM before increasing content')
    return {'elf':path.name,'elf_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'text':text,'data':data,'bss':bss,'static_bytes':total,'budget_bytes':limit,
            'limitation':'Static sections only; BIOS, dynamic allocation, stack and runtime performance require separate validation'}

if __name__=='__main__':print(json.dumps(check(sys.argv[1]),indent=2))
