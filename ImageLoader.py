import atexit
import hashlib
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import exiftool
import imagehash
from PIL import Image

from ImageInfo import ImageInfo

exif_date_keys = ['EXIF:CreateDate', 'EXIF:DateTimeOriginal', 'EXIF:ModifyDate', 'RIFF:DateTimeOriginal', 'QuickTime:PreviewDate', 'QuickTime:CreateDate', 'QuickTime:ModifyDate', 'QuickTime:TrackCreateDate', 'QuickTime:TrackModifyDate', 'QuickTime:MediaCreateDate', 'QuickTime:MediaModifyDate', 'XMP:DateCreated', 'XMP:CreateDate', 'XMP:ModifyDate']
exif_width_keys = ['File:ImageWidth', 'RIFF:ImageWidth', 'QuickTime:ImageWidth']
exif_height_keys = ['File:ImageHeight', 'RIFF:ImageHeight', 'QuickTime:ImageHeight']


class ImageLoader:
    loadable_re = re.compile(".+\.(jpg|mov|avi|mp4|wmv|png|m4v|jpeg)$", re.IGNORECASE)
    image_re = re.compile(".+\.(jpg|png)$", re.IGNORECASE)

    logger = logging.getLogger(__name__)
    __instance = None

    def __init__(self):
        if ImageLoader.__instance:
            raise ValueError("This class is a singleton, use ImageLoader.instance()")
        self.exif_tool = exiftool.ExifTool()
        self.exif_tool.start()
        self.logger.info("ExifTool started")
        atexit.register(ImageLoader.terminate)
        ImageLoader.__instance = self

    @classmethod
    def instance(cls):
        if not ImageLoader.__instance:
            ImageLoader()
        return ImageLoader.__instance

    @classmethod
    def terminate(cls):
        image_loader = ImageLoader.instance()
        if image_loader:
            if image_loader.exif_tool:
                image_loader.exif_tool.terminate()
                cls.logger.info("ExifTool terminated")

    @classmethod
    def load(cls, path: Path) -> ImageInfo:
        if path.name.lower().endswith(".mov"):
            return ImageLoader.instance().load_mov(path)
        elif path.name.lower().endswith(".avi"):
            return ImageLoader.instance().load_avi(path)
        elif path.name.lower().endswith(".mp4"):
            return ImageLoader.instance().load_mp4(path)
        elif path.name.lower().endswith(".m4v"):
            return ImageLoader.instance().load_mp4(path)
        elif path.name.lower().endswith(".wmv"):
            return ImageLoader.instance().load_wmv(path)
        elif path.name.lower().endswith(".jpg"):
            return ImageLoader.instance().load_jpg(path)
        elif path.name.lower().endswith(".png"):
            return ImageLoader.instance().load_png(path)
        else:
            raise ValueError(f"I don't know how to load {path}")

    def load_jpg(self, path: Path) -> ImageInfo:
        image = Image.open(path.as_posix())
        image_hash = imagehash.dhash(image, 10)
        exif: Dict = self.load_exif(path)
        if not exif:
            self.logger.warning(f"No exif info found in {path}")
        stat = path.stat()
        oldest_dt = self.get_oldest_date(exif, stat, path)
        w, h = image.size
        return ImageInfo(path, stat.st_size, image_hash, oldest_dt, w, h, exif)

    def load_mov(self, path: Path) -> ImageInfo:
        # hash = imagehash.ImageHash(numpy.asarray(cls.sha(path.as_posix())))
        image_hash = self.hash_file(path.as_posix())
        exif: Dict = self.load_exif(path)
        if not exif:
            self.logger.warning(f"No exif info found in {path}")
        stat = path.stat()
        oldest_dt = self.get_oldest_date(exif, stat, path)
        w, h = self.get_wh(exif)
        return ImageInfo(path, stat.st_size, image_hash, oldest_dt, w, h, exif)

    def load_avi(self, path: Path) -> ImageInfo:
        return self.load_mov(path)

    def load_mp4(self, path: Path) -> ImageInfo:
        return self.load_mov(path)

    def load_wmv(self, path: Path) -> ImageInfo:
        return self.load_mov(path)

    def load_png(self, path: Path) -> ImageInfo:
        return self.load_jpg(path)

    def load_exif(self, path: Path):
        return self.exif_tool.get_metadata(path.as_posix())

    @classmethod
    def get_wh(cls, exif: Dict) -> Tuple[int, int]:
        w = h = None
        if exif:
            for key in exif_width_keys:
                w = exif.get(key)
                if w:
                    break
            for key in exif_height_keys:
                h = exif.get(key)
                if h:
                    break
        return w, h

    @classmethod
    def get_oldest_date(cls, exif: Dict, stat: Tuple, path: Path):
        dates = []
        if exif:
            for key in exif_date_keys:
                dt_str: str = exif.get(key)
                if dt_str:
                    try:
                        dates.append(datetime.strptime(dt_str.strip().rstrip('\x00'), '%Y:%m:%d %H:%M:%S'))
                    except ValueError:
                        cls.logger.warning(f"Failed to parse exif {key} value {dt_str} in {path}")
        modified_dt = datetime.fromtimestamp(stat.st_mtime)
        if modified_dt:
            dates.append(modified_dt)
        created_dt = datetime.fromtimestamp(stat.st_ctime)
        if created_dt:
            dates.append(created_dt)
        oldest_dt = sorted(dates)[0]
        return oldest_dt

    @classmethod
    def hash_file(cls, filename):
        if ImageLoader.image_re.match(filename):
            return cls.hash_image(filename)
        else:
            h = hashlib.sha1()
            with open(filename, 'rb', buffering=0) as f:
                for b in iter(lambda: f.read(128 * 1024), b''):
                    h.update(b)
            return h.hexdigest()

    @classmethod
    def hash_image(cls, filename, size=64):
        image = Image.open(filename)
        return imagehash.dhash(image, size)

    @classmethod
    def is_hdr(cls, exif: Dict) -> bool:
        hdr_image_type = exif.get('MakerNotes:HDRImageType')
        custom_rendered = exif.get('EXIF:CustomRendered')
        if hdr_image_type == 3 or custom_rendered == 3:
            return True
        return False
