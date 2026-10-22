#!/usr/bin/env python3
"""Create separate 4K wallpaper copies with local Real-ESRGAN and ImageMagick.

No network calls, system package installs or changes to input images.
Portable binary/models live outside dotfiles in ~/.local/share/dreamcore-upscale.
"""
import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from PIL import Image

ITEMS = [
    ('cce9997ecaa149e638dc482472d8383d.jpg','field-clouds'),
    ('wallhaven-d8vy3m.png','pink-door'),
    ('9ae6c9a81183bbc4d684afbfa4ae8e3a.jpg','tree-clouds'),
    ('thumb-1920-1360895.jpeg','poolrooms'),
    ('wp13652320.jpg','cloud-room'),
]
# Keep the original wall/cloud texture where full neural enhancement looked too strong.
FIDELITY_BLEND = {'cloud-room': .35}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def size(path):
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return list(image.size)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path.home()/'Wallpapers/Dreamcore')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--only',choices=[key for _,key in ITEMS])
    parser.add_argument('--tile',type=int,default=200)
    parser.add_argument('--fast',action='store_true',help='Disable the eight-pass TTA quality mode')
    args=parser.parse_args()
    output=args.output or args.input/'enhanced-4k'
    output.mkdir(parents=True,exist_ok=True)
    tool=Path.home()/'.local/share/dreamcore-upscale'
    binary=tool/'realesrgan-ncnn-vulkan'
    assert binary.is_file() and (tool/'models/realesrgan-x4plus.bin').is_file()
    state=Path.home()/'.local/state/dreamcore-upscale'/time.strftime('%Y%m%d-%H%M%S')
    state.mkdir(parents=True,mode=0o700)
    rawdir=state/'raw';rawdir.mkdir()
    records=[]
    items=[item for item in ITEMS if not args.only or item[1]==args.only]
    for index,(file,key) in enumerate(items,1):
        src=args.input/file;dst=output/(key+'-4k.png')
        before=digest(src);original_size=size(src)
        # Reuse only an existing verified output with matching source metadata.
        metadata=dst.with_suffix('.json')
        if dst.exists():
            old=json.loads(metadata.read_text()) if metadata.exists() else {}
            assert old.get('source_sha256')==before and old.get('output_sha256')==digest(dst),f'Unmanaged output exists: {dst}'
            assert old.get('tile',128)==args.tile and old.get('tta',False)==(not args.fast),f'Processing options changed; select a new output directory: {dst}'
            assert old.get('neural_blend',1)==FIDELITY_BLEND.get(key,1),f'Fidelity settings changed; select a new output directory: {dst}'
            assert size(dst)==[3840,2160]
            records.append(old);print(f'[{index}/{len(items)}] Reusing {dst.name}',flush=True)
            continue
        print(f'[{index}/{len(items)}] Upscaling {file} from {original_size}',flush=True)
        raw=rawdir/(key+'-x4.png')
        command=['nice','-n','10',str(binary),'-i',str(src),'-o',str(raw),'-s','4',
                 '-m',str(tool/'models'),'-n','realesrgan-x4plus','-g','0','-t',str(args.tile),'-j','1:1:1']
        if not args.fast:
            command.append('-x')
        with (state/(key+'.log')).open('w') as log:
            subprocess.run(command,cwd=tool,stdout=log,stderr=log,check=True)
        assert size(raw)==[original_size[0]*4,original_size[1]*4]
        temp=output/('.'+key+'-4k.tmp.png')
        subprocess.run(['magick',str(raw),'-filter','Lanczos','-resize','3840x2160^',
                        '-gravity','center','-extent','3840x2160','-strip',
                        '-define','png:compression-level=6',str(temp)],check=True)
        blend=FIDELITY_BLEND.get(key,1)
        if blend<1:
            original=rawdir/(key+'-original-4k.png')
            subprocess.run(['magick',str(src),'-filter','Lanczos','-resize','3840x2160^',
                            '-gravity','center','-extent','3840x2160',str(original)],check=True)
            mixed=output/('.'+key+'-blend.tmp.png')
            subprocess.run(['magick',str(original),str(temp),'-define',
                            f'compose:args={blend*100:g},{(1-blend)*100:g}',
                            '-compose','blend','-composite','-strip',str(mixed)],check=True)
            os.replace(mixed,temp)
        assert size(temp)==[3840,2160]
        stats=subprocess.run(['magick',str(temp),'-format','%[standard-deviation]','info:'],capture_output=True,text=True,check=True)
        assert float(stats.stdout)>1, 'Empty/uniform image produced'
        assert digest(src)==before, 'Source changed during processing'
        os.replace(temp,dst)
        record={'source':str(src),'source_sha256':before,'source_size':original_size,
                'output':str(dst),'output_sha256':digest(dst),'output_size':[3840,2160],
                'method':'Real-ESRGAN ncnn Vulkan, realesrgan-x4plus, x4; Lanczos downscale, centered 16:9 crop',
                'tile':args.tile,'tta':not args.fast,
                'neural_blend':blend,
                'binary_sha256':digest(binary),'model_sha256':digest(tool/'models/realesrgan-x4plus.bin'),
                'processing_state':str(state)}
        metadata.write_text(json.dumps(record,indent=2)+'\n')
        records.append(record)
        print(f'[{index}/{len(items)}] Ready: {dst.name}, 3840x2160',flush=True)
    (state/'outputs.json').write_text(json.dumps(records,indent=2)+'\n')
    print('Output directory:',output,flush=True)


if __name__=='__main__':
    main()
