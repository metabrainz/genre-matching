# Given a data file and a mapping file, generate a list of musicbrainz tags to upload

import argparse
import csv
from typing import List
import sys


def main(datafiles: List[str], mapping_file: str, do_recording: bool, do_releasegroup: bool):
    mapping_genre_to_tags = {}
    with open(mapping_file) as fp:
        reader = csv.reader(fp)
        next(reader)
        for line in reader:
            genre = line[0]
            subgenre = line[1]
            # fields are 'tag,matchtype,is_genre', just extract the tag
            tags = line[2::3]
            if subgenre:
                genre = f"{genre}---{subgenre}"
            mapping_genre_to_tags[genre] = tags
    
    for datafile in datafiles:
        writer = csv.writer(sys.stdout)
        with open(datafile) as fp:
            reader = csv.reader(fp, dialect=csv.excel_tab)
            next(reader)
            for line in reader:
                if do_recording:
                    mbid = line[0]
                elif do_releasegroup:
                    mbid = line[1]
                else:
                    raise Exception("Cannot get here")
                tags = [t for t in line[2:] if t]
                mb_tags = set()
                for t in tags:
                    mb_tags.update(mapping_genre_to_tags[t])
                writer.writerow([mbid] + sorted(list(mb_tags)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-rec', action='store_true', default=False, help='Output file for recording mbids')
    parser.add_argument('-rg', action='store_true', default=False, help='Output file for releasegroup mbids')
    parser.add_argument('mapping', help='Mapping file')
    parser.add_argument('data', nargs='+', help='Data file(s)')

    args = parser.parse_args()

    if (args.rec and args.rg) or (not args.rec and not args.rg):
        print("Require only one one of -rec or -rg")
    else:
        main(args.data, args.mapping, args.rec, args.rg)