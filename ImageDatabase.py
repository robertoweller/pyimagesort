import logging
import os
from os import path
from pathlib import Path
from typing import List, Iterator

import transaction
from BTrees import OOBTree
from ZODB import DB
from ZODB.FileStorage import FileStorage
from imagehash import ImageHash

from ImageInfo import ImageInfo


class ImageDatabase:
    logger = logging.getLogger(__name__)

    def __init__(self, root_dir: Path, save_threshold: int = 10):
        self.root_dir = root_dir
        self.save_threshold = save_threshold
        self.data_dir = self._get_data_dir(self.root_dir)
        self.storage_path = Path(os.path.join(self.data_dir, "images.db"))
        init_db = not self.storage_path.exists()
        self.storage = FileStorage(os.path.join(self.data_dir, "images.db"))
        self.db = DB(self.storage)
        self.connection = self.db.open()
        self.root = self.connection.root
        if init_db:
            self.root.by_path = OOBTree.BTree()
            self.root.by_hash = OOBTree.BTree()
        self.mod_count = 0

    @classmethod
    def _get_data_dir(cls, root_dir: Path) -> Path:
        data_dir = Path(path.join(root_dir.as_posix(), ".imagesort"))
        if not data_dir.exists():
            data_dir.mkdir(parents=True)
        return data_dir

    def _modified(self):
        self.mod_count = self.mod_count + 1
        if self.mod_count >= self.save_threshold:
            self.save()

    def save(self, force: bool = False):
        if self.mod_count or force:
            transaction.commit()
            self.mod_count = 0

    def get_by_path(self, path: Path) -> ImageInfo:
        return self.root.by_path.get(str(path))

    def get_by_hash(self, hash: ImageHash) -> ImageInfo:
        return self.root.by_hash.get(str(hash))

    def add(self, image: ImageInfo):
        self.root.by_path[str(image.path)] = image
        self.root.by_hash[str(image.hash)] = image
        self.logger.debug(f"Added {image}")
        self._modified()

    def remove(self, image: ImageInfo):
        try:
            del self.root.by_path[str(image.path)]
        except KeyError:
            pass
        try:
            del self.root.by_hash[str(image.hash)]
        except KeyError:
            pass
        self.logger.debug(f"Removed {image}")
        self._modified()

    def all_images(self) -> Iterator[ImageInfo]:
        return self.root.by_path.values()

    def all_paths(self) -> Iterator[Path]:
        return self.root.by_path.keys()

    def all_hashes(self) -> List[ImageHash]:
        return self.root.by_hash.keys()
