import argparse
import collections
import csv

from fuzzywuzzy import fuzz


def main(genrefile, datafile, outfile=None):
    mb_genres = open(genrefile).read().splitlines()

    data_genres = []
    with open(datafile) as fp:
        for line in fp:
            genre = line.strip()
            if '---' in genre:
                data_genres.append(tuple(genre.split('---')))
            else:
                data_genres.append((genre, genre))

    genre_matches = collections.defaultdict(list)

    for g in mb_genres:
        for dg in data_genres:
            ratio = fuzz.ratio(g, dg[1])
            genre_matches[g].append((ratio, dg))

    for k, v in genre_matches.items():
        genre_matches[k] = sorted(v, reverse=True)

    for k, v in genre_matches.items():
        ratio, match = v[0]
        if ratio >= 70:
            important = '***' if ratio == 100 else ''
            if match[0] == match[1]:
                genre = match[0]
            else:
                genre = f"{match[0]}/{match[1]}"
            print(f"{important} mb genre: {k}  other genre {genre} ({ratio})")

    if outfile:
        with open(outfile, "w") as fp:
            w = csv.writer(fp)
            w.writerow(["musicbrainz genre", "other genre", "match score"])
            for k, v in genre_matches.items():
                ratio, match = v[0]
                if match[0] == match[1]:
                    genre = match[0]
                else:
                    genre = f"{match[0]}/{match[1]}"
                w.writerow([k, genre, ratio])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', required=False)
    parser.add_argument('genrefile')
    parser.add_argument('datafile')
    args = parser.parse_args()
    main(args.genrefile, args.datafile, args.o)
