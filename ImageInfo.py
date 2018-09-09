from datetime import datetime
from pathlib import Path
from typing import Dict

import persistent
from imagehash import ImageHash


class ImageInfo(persistent.Persistent):

    def __init__(self, path: Path, size: int, hash: ImageHash, ts: datetime, width: int, height: int, exif: Dict = None):
        self.path = path
        self.size = size
        self.hash = hash
        self.ts = ts
        self.width = width
        self.height = height
        self.exif = exif

    def __repr__(self):
        return f"{self.hash} {self.path} {self.size} {self.width}x{self.height} {self.ts}"
