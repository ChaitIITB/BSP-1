import lzma, tarfile, io, json, sys
f=open(r"raw/unarXive_open.tar.xz","rb")
x=lzma.LZMAFile(f)
t=tarfile.open(fileobj=x,mode="r|")
for m in t:
    print(m.name,m.size)
    if m.isfile() and m.name.endswith(".jsonl"):
        fh=t.extractfile(m)
        line=fh.readline()
        d=json.loads(line)
        print(list(d.keys()))
        print(json.dumps(d["metadata"])[:1500])
        be=d["bib_entries"]; k=list(be)[:3]
        for kk in k: print(kk, json.dumps(be[kk])[:600])
        print(len(be), d["discipline"])
        break
