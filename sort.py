import argparse
from logging.config import fileConfig

fileConfig("logger.ini")

args_parser = argparse.ArgumentParser(description='Sort images and videos by oldest timestamp')
args_parser.add_argument('destination', type=str, help='Full path to destination directory')
args_parser.add_argument('source', type=str, nargs='+', help='Input directory(s) to process')

if __name__ == "__main__":
    args = args_parser.parse_args()

    from pathlib import Path
    from ImageSorter import ImageSorter

    try:
        image_sorter = ImageSorter(Path(args.destination))
        for source_path_str in args.source:
            image_sorter.sort_dir(Path(source_path_str))
    except Exception as e:
        ImageSorter.logger.exception(f"Sort failed: {str(e)}")
