"""Compile the locally reviewed draft to exact message/site dictionaries.

Run from a local checkout. Does not fetch services or alter command routing.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src/allset'
REVIEW=ROOT/'docs/localization_review/full/完整审阅数据.json'
rows=json.loads(REVIEW.read_text(encoding='utf8'))['entries']
by_text=defaultdict(list)
by_file=defaultdict(set)
by_file_text=defaultdict(list)
for row in rows:
    by_text[row['english']].append(row)
    for file in {o['file'] for o in row['occurrences']}:
        by_file[file].add(row['english'])
        by_file_text[(file,row['english'])].append(row)

defaults={'Set':'设置','Key':'关键帧','Frame':'帧','Track':'平移','Scale':'缩放','Point':'点','Orient':'方向','Parent':'建立父子关系','Normal':'法线','Wire':'线','Action':'操作','Extend':'延伸','Mute':'禁用动画','Stiffness':'刚度','Joint':'关节','Bone':'骨骼','Clamped':'钳制','Stepped':'阶跃','Plateau':'高原','Additive':'相加','Holder':'限制曲线','UV Set':'UV 集'}
messages={}
for english,records in by_text.items():
    counts=Counter(r['suggested_chinese'] for r in records)
    # Human-readable captions should not inherit an internal enum's keep-English decision.
    translated=Counter({zh:n for zh,n in counts.items() if zh!=english})
    messages[english]=defaults.get(english,(translated or counts).most_common(1)[0][0])
contexts=defaultdict(dict)
for row in rows:
    context=row.get('context','')
    if context:
        contexts[context][row['english']]=row['suggested_chinese']
        contexts[context.rstrip('/')+'/'+row['english']][row['english']]=row['suggested_chinese']

site_path=ROOT/'integration_sites.json'
sites=json.loads(site_path.read_text(encoding='utf8')) if site_path.exists() else []
if isinstance(sites,dict): sites=sites.get('sites',[])
def relative_file(path):
    path=str(path).replace('\\','/')
    if path.startswith('src/allset/'): return path
    if '/src/allset/' in path: return 'src/allset/'+path.split('/src/allset/',1)[1]
    return 'src/allset/'+path.lstrip('/')
for site in sites:
    ctx=site['context']; file=relative_file(site['file']); line=int(site.get('line',0))
    source=site.get('source_text')
    # For a dynamic drawing boundary, register the phrases known to this module;
    # unrelated module vocabulary uses the generic exact message dictionary.
    candidates=[source] if isinstance(source,str) else by_file[file]
    for english in candidates:
        best=[]
        for r in by_file_text[(file,english)]:
            matching=[o for o in r['occurrences'] if o['file']==file]
            if matching:
                distance=min(abs(int(o['line'])-line) if int(o['line']) else 100000 for o in matching)
                best.append((distance, r))
        if best:
            best.sort(key=lambda pair:pair[0])
            contexts[ctx][english]=best[0][1]['suggested_chinese']
        elif english in messages:
            contexts[ctx][english]=messages[english]

# Exact global messages already cover identical site translations. Store only
# semantic differences rather than duplicating the catalog at each draw site.
compact_contexts={ctx:{en:zh for en,zh in values.items() if messages.get(en)!=zh} for ctx,values in contexts.items()}
compact_contexts={ctx:values for ctx,values in compact_contexts.items() if values}
catalog={'schema_version':1,'locale':'zh_HANS','messages':messages,'contexts':compact_contexts,'provenance':{'source_commit':'bd7ee0440250bf00d57c7aa304dd8cabc8b03143','review_records':len(rows),'implementation_authorized':True,'translation':'Local whole-sentence drafts and context-specific terminology; no external translation provider'}}
target=SRC/'translations_zh_HANS.json'
target.write_text(json.dumps(catalog,ensure_ascii=False,separators=(',',':')),encoding='utf8')
print(json.dumps({'messages':len(messages),'contexts':len(compact_contexts),'site_count':len(sites),'bytes':target.stat().st_size},ensure_ascii=True))
