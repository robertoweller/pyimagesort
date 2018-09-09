from datetime import datetime

import logging
import os
import time
from pathlib import Path

import imagehash
import piexif
from PIL import Image
from imagehash import ImageHash

from ImageDatabase import ImageDatabase
from ImageInfo import ImageInfo
from ImageLoader import ImageLoader

SIMILAR_IMAGE_HASH_DIST = 3
OLD_TS = datetime.strptime('1980:02:01 00:00:00', '%Y:%m:%d %H:%M:%S')


class ImageSorter:
    logger = logging.getLogger(__name__)

    def __init__(self, sorted_dir: Path):
        if not sorted_dir.exists() or not sorted_dir.is_dir():
            raise ValueError(f"{sorted_dir} does not exist or is not a directory")
        self.sorted_dir = sorted_dir
        self.db = ImageDatabase(self.sorted_dir)
        self.recycle_dir = Path(os.path.join(self.db.data_dir, "trash"))
        if not self.recycle_dir.exists():
            self.recycle_dir.mkdir(parents=True)
        self.root_dir = None
        self.check_db()

    def check_db(self):
        self.logger.info(f"Verifying database consistency")
        for image_hash in self.db.all_hashes():
            image = self.db.get_by_hash(image_hash)
            if not self.db.get_by_path(image.path):
                self.logger.warning(f"Missing in images_by_path {image}")
                self.db.add(image)

        for path in self.db.all_paths():
            image = self.db.get_by_path(path)
            if not self.db.get_by_hash(image.hash):
                self.logger.warning(f"Missing in images_by_hash {image}")
                self.db.add(image)

        for image in self.db.all_images():
            if not image.path.exists():
                self.logger.warning(f"Deleting missing {image}")
                self.db.remove(image)

        self.check_dir(self.sorted_dir)
        self.db.save()

    def check_dir(self, path: Path):
        for path in path.glob(f"*"):
            if path.is_dir() and not path.name.startswith("."):
                self.check_dir(path)
            elif path.is_file() and ImageLoader.loadable_re.match(path.name):
                existing_image = self.db.get_by_path(path)
                if not existing_image:
                    self.reload(path)

    def reload(self, path: Path):
        self.logger.info(f"Reloading {path}")
        reloaded = ImageLoader.load(path)
        existing = self.db.get_by_hash(reloaded.hash)
        if existing and existing.path != path:
            self.logger.warning(f"Reloaded image: {reloaded}")
            self.logger.warning(f"  Matches existing: {existing}")
            better = self.find_better(reloaded, existing)
            if better == reloaded:
                self.db.remove(existing)
                self.recycle(existing)
            else:
                self.db.remove(reloaded)
                self.recycle(reloaded)
        self.db.add(reloaded)

    def sort_dir(self, incoming_dir: Path):
        if not incoming_dir.exists():
            self.logger.fatal(f"{incoming_dir} does not exist!")
            exit(1)
        if not self.root_dir:
            self.root_dir = incoming_dir

        self.logger.info(f"Processing DIR {incoming_dir}")
        for path in incoming_dir.glob(f"*"):
            if path.is_dir() and not path.name.startswith("."):
                self.sort_dir(path)
            elif path.is_file() and ImageLoader.loadable_re.match(path.name):
                self.sort_file(path)
            elif path.is_file() and path.name.lower() in ['.picasa.ini', 'desktop.ini']:
                os.remove(path)
                time.sleep(0.1)

        if incoming_dir != self.root_dir and not os.listdir(incoming_dir.as_posix()):
            self.logger.info(f"Deleting empty directory {incoming_dir}")
            os.rmdir(incoming_dir)
            time.sleep(0.1)

        self.db.save()

    def sort_file(self, path: Path):
        self.logger.info(f"Processing FILE {path}")
        path = self.cleanup_filename(path)
        incoming_image = ImageLoader.load(path)
        existing_image = self.find_existing(incoming_image.hash)
        if not existing_image:
            self.move_to_sorted(incoming_image)
        else:
            self.logger.info(f"Found match for incoming image {incoming_image}")
            self.logger.info(f"  With existing image {existing_image}")
            self.keep_better(existing_image, incoming_image)

    @classmethod
    def cleanup_filename(cls, path: Path):
        if path.name.lower().endswith("jpeg"):
            new_path = Path(os.path.join(path.parent, path.name[:-5] + ".jpg"))
            os.rename(path, new_path)
            return new_path
        return path

    def find_existing(self, incoming_hash: ImageHash) -> ImageInfo:
        hash_match = self.db.get_by_hash(incoming_hash)
        if hash_match:
            return hash_match
        if isinstance(incoming_hash, ImageHash):
            similar_match = self.find_similar(incoming_hash)
            if similar_match:
                return similar_match

    def find_similar(self, incoming_hash: ImageHash) -> ImageInfo:
        for image in self.db.all_images():
            existing_hash = image.hash
            if isinstance(existing_hash, ImageHash):
                dist = existing_hash - incoming_hash
                if dist <= SIMILAR_IMAGE_HASH_DIST:
                    return image

    def move_to_sorted(self, incoming_image: ImageInfo):
        self.sort_to(self.sorted_dir, incoming_image, True)

    def recycle(self, image: ImageInfo):
        existing_image = self.db.get_by_hash(image.hash)
        if existing_image:
            prune_hash = ImageLoader.hash_file(image.path.as_posix())
            existing_hash = ImageLoader.hash_file(existing_image.path.as_posix())
            if prune_hash == existing_hash:
                self.logger.info(f"Deleting {image}")
                self.logger.info(f"  Matches {existing_image}")
                os.remove(image.path)
                time.sleep(0.1)
                return
        self.logger.debug(f"Recycling {image}")
        self.sort_to(self.recycle_dir, image, False)

    def sort_to(self, root_dir: Path, incoming_image: ImageInfo, check_rotated: bool):
        ext = incoming_image.path.name[-4:].lower()
        year = incoming_image.ts.strftime("%Y")
        month = incoming_image.ts.strftime("%m")
        new_name = incoming_image.ts.strftime(f"%Y%m%d-%H%M%S-0{ext}")
        new_path = Path(os.path.join(root_dir, year, month, new_name))
        new_path.parent.mkdir(parents=True, exist_ok=True)
        if new_path.exists():
            if check_rotated and ImageLoader.image_re.match(incoming_image.path.name):
                self.logger.info(f"{new_path} already exists! Checking for rotated images...")
                existing_image = self.find_rotated(incoming_image)
                if existing_image:
                    self.logger.info(f"Rotated version of {incoming_image}")
                    self.logger.info(f"  Matches existing: {existing_image}")
                    self.keep_better(existing_image, incoming_image)
                    return
            for i in range(1, 100):
                new_name = incoming_image.ts.strftime(f"%Y%m%d-%H%M%S-{i}{ext}")
                new_path = Path(os.path.join(root_dir, year, month, new_name))
                if not new_path.exists():
                    break
        self.logger.info(f"Moving {incoming_image.path} to {new_path}")
        os.rename(incoming_image.path, new_path)
        incoming_image.path = new_path
        if root_dir == self.sorted_dir:
            self.db.add(incoming_image)

    def find_rotated(self, incoming_image: ImageInfo) -> ImageInfo:
        image: Image = Image.open(incoming_image.path.as_posix())
        for i in range(0, 3):
            image = image.rotate(90, expand=True)
            image_hash = imagehash.dhash(image, 10)
            existing_image = self.find_existing(image_hash)
            if existing_image:
                return existing_image

    def keep_better(self, existing_image: ImageInfo, incoming_image: ImageInfo):
        better = self.find_better(existing_image, incoming_image)
        if existing_image == better:
            self.keep_existing(existing_image, incoming_image)
        else:
            self.keep_incoming(existing_image, incoming_image)

    @classmethod
    def find_better(cls, image1: ImageInfo, image2: ImageInfo):
        pixels1 = image1.width * image1.height
        pixels2 = image2.width * image2.height
        is_hdr1 = ImageLoader.is_hdr(image1.exif)
        is_hdr2 = ImageLoader.is_hdr(image2.exif)
        if pixels1 == pixels2 and (is_hdr1 or is_hdr2):
            if is_hdr1:
                return image1
            else:
                return image2
        elif pixels1 >= pixels2:
            return image1
        else:
            return image2

    def keep_existing(self, existing_image: ImageInfo, incoming_image: ImageInfo):
        self.logger.info(f"Keeping existing: {existing_image}")
        self.logger.info(f"  Deleting incoming: {incoming_image}")
        if existing_image.path.name.lower().endswith(".jpg") and incoming_image.ts > OLD_TS and incoming_image.ts < existing_image.ts:
            self.logger.info(f"  But preserving incoming's exif: {incoming_image}")
            try:
                piexif.transplant(incoming_image.path.as_posix(), existing_image.path.as_posix())
            except ValueError as e:
                self.logger.warning(f"Failed to transplant exif: {e}")
            self.reload(existing_image.path)
        self.recycle(incoming_image)

    def keep_incoming(self, existing_image: ImageInfo, incoming_image: ImageInfo):
        self.logger.info(f"Deleting existing: {existing_image}")
        self.logger.info(f"  Keeping incoming: {incoming_image}")
        if existing_image.path.name.lower().endswith(".jpg") and existing_image.ts > OLD_TS and existing_image.ts < incoming_image.ts:
            self.logger.info(f"  But preserving existing's exif: {existing_image}")
            try:
                piexif.transplant(existing_image.path.as_posix(), incoming_image.path.as_posix())
            except ValueError as e:
                self.logger.warning(f"Failed to transplant exif: {e}")
            incoming_image = ImageLoader.load(incoming_image.path)
        self.db.remove(existing_image)
        self.recycle(existing_image)
        self.move_to_sorted(incoming_image)
