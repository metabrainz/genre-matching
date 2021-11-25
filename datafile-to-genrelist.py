# Take any number of datafiles (e.g. acousticbrainz-mediaeval-discogs-train.tsv) and extract out
# all genres, deduplicate, and write out in sorted order.
import argparse
import csv
import sys
from collections import Counter


def main(datafiles):
    data_genres = set()
    for f in datafiles:
        data_genres = Counter()
        with open(f) as fp:
            r = csv.reader(fp, dialect=csv.excel_tab)
            next(r)
            for line in r:
                for genre in line[2:]:
                    if genre:
                        data_genres[genre] += 1

    writer = csv.DictWriter(sys.stdout, fieldnames=["genre", "count"])
    writer.writeheader()
    for genre, count in data_genres.items():
        writer.writerow({"genre": genre, "count": count})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('datafile', nargs='+')
    args = parser.parse_args()
    main(args.datafile)

