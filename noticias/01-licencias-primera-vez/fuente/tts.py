import asyncio, ssl, os, sys, json, edge_tts, edge_tts.communicate as c
c._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
async def one(text, out, voice):
    comm = edge_tts.Communicate(text, voice, rate="+6%", proxy=os.environ.get("HTTPS_PROXY"), boundary="WordBoundary")
    sub = []
    with open(out, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary": sub.append((ch["offset"]/1e7, ch["duration"]/1e7, ch["text"]))
    json.dump(sub, open(out+".json","w"), ensure_ascii=False)
async def main():
    lines=[l.strip() for l in open(sys.argv[1]) if l.strip()]
    for i,l in enumerate(lines,1): await one(l, f"s{i}.mp3", "es-HN-CarlosNeural")
asyncio.run(main())
