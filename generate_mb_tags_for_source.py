# Given a data file and a mapping file, generate a list of musicbrainz tags to upload

import argparse
import csv
from typing import List
import sys


def main(datafiles: List[str], mapping_file: str):
    mapping_genre_to_tags = {}
    with open(mapping_file) as fp:
        reader = csv.reader(fp)
        next(reader)
        for line in reader:
            genre = line[0]
            subgenre = line[1]
            # fields are 'tag,matchtype,is_genre', just extract the tag
            tags = line[2::3]
            tags = [t for t in tags if t]
            if subgenre:
                genre = f"{genre}---{subgenre}"
            mapping_genre_to_tags[genre] = tags
    
    for datafile in datafiles:
        writer = csv.writer(sys.stdout)
        with open(datafile) as fp:
            reader = csv.reader(fp, dialect=csv.excel_tab)
            next(reader)
            for line in reader:
                mbid = line[0]
                tags = [t for t in line[2:] if t]
                mb_tags = set()
                for t in tags:
                    mapped_tags = mapping_genre_to_tags[t]
                    if mapped_tags:
                        mb_tags.update(mapped_tags)
                if mb_tags:
                    writer.writerow([mbid] + sorted(list(mb_tags)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('mapping', help='Mapping file')
    parser.add_argument('data', nargs='+', help='Data file(s)')

    args = parser.parse_args()

    main(args.data, args.mapping)