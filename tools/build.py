"""Build a deterministic, root-layout Blender extension ZIP without network access."""
import hashlib
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'src/allset'
OUTPUT=ROOT/'dist/maya-workflow-kit-0.6.2-zh.2.zip'
OUTPUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUTPUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    for file in sorted(SOURCE.rglob('*')):
        if not file.is_file() or '__pycache__' in file.parts or file.suffix in {'.pyc','.blend1'}:
            continue
        info=zipfile.ZipInfo(file.relative_to(SOURCE).as_posix(),date_time=(2026,10,29,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o100644 << 16
        archive.writestr(info,file.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
digest=hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
OUTPUT.with_suffix('.zip.sha256').write_text(digest+'  '+OUTPUT.name+'\n',encoding='ascii')
print(OUTPUT.relative_to(ROOT))
print('SHA256',digest)
