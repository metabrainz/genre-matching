import argparse
import collections
import csv
import os


def load_genres(datafile):
    genres = collections.defaultdict(set)
    with open(datafile) as fp:
        r = csv.reader(fp, dialect=csv.excel_tab)
        next(r)
        for line in r:
            for genre in line[2:]:
                if genre:
                    if '---' in genre:
                        parent, sub = genre.split('---')
                        genres[parent].add(sub)
                    else:
                        if genre not in genres:
                            genres[genre] = set()
    return genres


def main(files, debug):
    filegenres = {}
    for fname in files:
        print(fname)
        genres = load_genres(fname)
        if debug:
            for g in sorted(genres.keys()):
                print(g)
                for sg in sorted(genres[g]):
                    print(f"  - {sg}")
        filegenres[fname] = genres

    # Check if there are any subgenres that are shared between different genres/sources
    sg_map = collections.defaultdict(set)
    for f, genres in filegenres.items():
        source, ext = os.path.splitext(os.path.basename(f))
        for g, sgs in genres.items():
            for sg in sgs:
                sg_map[sg].add((source, g))
    for sg in sorted(sg_map.keys()):
        sources = sg_map[sg]
        if len(sources) > 1:
            print(sg, "-", ", ".join([f"{source}:{genre}" for source, genre in sources]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('files', nargs='+')

    args = parser.parse_args()
    main(args.files, args.debug)
