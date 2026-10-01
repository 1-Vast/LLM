"""Bounded public HDF5 range reads with byte receipts; no signed URL storage."""
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import time
import urllib.request

from tools.datasets.state_prospective_input import digest, write_json


class RangeFile(io.RawIOBase):
    def __init__(self, url, out, max_blocks=256, block_size=262144, cache=None):
        self.url, self.out = url, Path(out)
        self.out.mkdir(parents=True, exist_ok=False)
        self.max_blocks, self.block_size, self.position = max_blocks, block_size, 0
        self.blocks, self.receipts, self.size = {}, [], None
        self.cache = Path(cache) if cache is not None else None
        if self.cache:
            old = json.loads((self.cache/"receipts.json").read_text())
            for record in old:
                if record.get("error") is None and record["url"] == url:
                    path = self.cache/record["path"]
                    if digest(path) != record["sha256"]:
                        raise ValueError("range cache hash mismatch")
                    self.blocks[record["byte_start"]//block_size] = path.read_bytes()
                    self.size = int(record["content_range"].split("/")[-1])
            write_json(self.out/"cache_reference.json",dict(path=str(self.cache),receipts_sha256=digest(self.cache/"receipts.json"),blocks=len(self.blocks)))
        self._block(0)

    def _block(self, block):
        if block in self.blocks:
            return self.blocks[block]
        if len(self.receipts) >= self.max_blocks:
            raise ValueError("bounded remote read budget exhausted")
        start = block*self.block_size
        end = start+self.block_size-1
        if self.size is not None:
            end = min(end, self.size-1)
        row = dict(url=self.url, byte_start=start, byte_end=end, cost="unknown",
                   started_at_utc=datetime.now(timezone.utc).isoformat(), retry=0)
        t = time.perf_counter()
        try:
            request = urllib.request.Request(self.url,headers={"Range":f"bytes={start}-{end}","User-Agent":"MAESTRO-public-range-audit/1"})
            with urllib.request.urlopen(request,timeout=45) as response:
                row["status"] = response.status
                row["content_range"] = response.headers.get("Content-Range")
                if response.status!=206 or not row["content_range"]:
                    raise ValueError("server did not honor bounded range")
                announced = row["content_range"].split()[1]
                span,total = announced.split("/")
                if span!=f"{start}-{end}":
                    raise ValueError("returned range mismatch")
                self.size = int(total)
                data=response.read(end-start+2)
                if len(data)!=end-start+1:
                    raise ValueError("partial range")
            path=self.out/f"block_{block}.raw"
            path.write_bytes(data)
            row.update(path=path.name,sha256=digest(path),bytes=len(data),error=None)
            self.blocks[block]=data
            return data
        except Exception as exc:
            # Network exception messages may include signed redirect URLs.
            row["error"]=type(exc).__name__
            raise RuntimeError("range retrieval failed; see sanitized receipt") from None
        finally:
            row.update(finished_at_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.perf_counter()-t)
            self.receipts.append(row)
            write_json(self.out/"receipts.json",self.receipts)

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        self.position=offset if whence==0 else self.position+offset if whence==1 else self.size+offset
        if self.position<0: raise ValueError("negative offset")
        return self.position
    def read(self, size=-1):
        size=min(self.size-self.position, self.size if size<0 else size)
        parts=[]
        while size>0:
            block,offset=divmod(self.position,self.block_size)
            data=self._block(block)
            n=min(size,len(data)-offset)
            parts.append(data[offset:offset+n]);self.position+=n;size-=n
        return b"".join(parts)
    def readinto(self, buffer):
        data=self.read(len(buffer));buffer[:len(data)]=data;return len(data)
