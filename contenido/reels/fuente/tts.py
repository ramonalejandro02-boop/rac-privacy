import asyncio, ssl, os, sys, edge_tts, edge_tts.communicate as c
c._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
async def main(text, out, voice="es-MX-JorgeNeural"):
    comm = edge_tts.Communicate(text, voice, rate="+8%", proxy=os.environ.get("HTTPS_PROXY"), boundary="WordBoundary")
    sub = []
    with open(out, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary": sub.append((ch["offset"]/1e7, ch["duration"]/1e7, ch["text"]))
    import json; json.dump(sub, open(out+".json","w"), ensure_ascii=False)
asyncio.run(main(sys.argv[1], sys.argv[2]))
