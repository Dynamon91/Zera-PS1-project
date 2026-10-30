"""Classify original material visibility using shader tags before saved defaults."""

def material_flags(alpha,tags,render_queue,floats):
    tags={str(k).lower():str(v).lower() for k,v in tags.items()}
    queue=tags.get('queue','');kind=tags.get('rendertype','')
    transparent=('transparent' in queue or 'overlay' in queue or kind=='transparent' or render_queue>=2500)
    if not tags:
        transparent=transparent or floats.get('_Mode',0)>=2 or floats.get('_ZWrite',1)==0 or floats.get('_DstBlend',0)!=0
    return (4 if alpha<=0.001 else 0)|(2 if transparent else 0)
