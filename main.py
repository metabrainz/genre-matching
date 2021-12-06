import argparse
import csv
import concurrent.futures
import sys
from enum import Enum, auto
import math
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set

from thefuzz import fuzz
from thefuzz import utils


DEBUG = False

class MatchType(Enum):
    FULLGENRE = auto()
    TOKENSORT = auto()
    PARENTGENRE = auto()
    SUBGENRE = auto()
    EXACT = auto()


@dataclass(unsafe_hash=True)
class ServiceGenre:
    parent_genre: str
    subgenre: Optional[str]
    number_taggings: int

    # just the parent genre, a-z, no spaces
    processed_parent_genre: str = field(init=False)
    # if parent + subgenre are set, the processed version of both. a-z, no spaces
    processed_full_genre: str = field(init=False)
    # same as above, but with spaces between words
    processed_full_genre_words: str = field(init=False)
    # subgenre, but just lowercase
    lowercase_subgenre: Optional[str] = field(init=False)
    processed_subgenre: Optional[str] = field(init=False)

    @property
    def full_genre(self):
        if self.subgenre:
            return self.parent_genre + "/" + self.subgenre
        else:
            return self.parent_genre

    def __post_init__(self):
        self.processed_parent_genre = utils.full_process(self.parent_genre).replace(" ", "")
        self.processed_full_genre_words = utils.full_process(self.full_genre)
        self.processed_full_genre = self.processed_full_genre_words.replace(" ", "")
        if self.subgenre:
            self.lowercase_subgenre = self.subgenre.lower()
            self.processed_subgenre = utils.full_process(self.subgenre).replace(" ", "")
        else:
            self.lowercase_subgenre = None
            self.processed_subgenre = None


@dataclass(unsafe_hash=True)
class MusicBrainzGenre:
    name: str
    # is it marked as a genre, or just a tag
    is_genre: bool
    # tag.ref_count
    tag_count: bool

    # processed version of name, a-z, no spaces
    processed_name: str = field(init=False)
    # same as above, but with spaces between words
    processed_name_words: str = field(init=False)

    def __post_init__(self):
        self.processed_name_words = utils.full_process(self.name)
        self.processed_name = self.processed_name_words.replace(" ", "")


@dataclass
class MatchResult:
    musicbrainz: MusicBrainzGenre

    match: int
    match_type: MatchType


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def threaded_match_genres(data_genres, musicbrainz_genres) -> Dict[ServiceGenre, List[MatchResult]]:
    num_workers = 8
    chunk_size = math.ceil(len(data_genres) / num_workers)
    genre_matches = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for genre_chunk in chunks(data_genres, chunk_size):
            futures.append(executor.submit(compare, genre_chunk, musicbrainz_genres))

        for future in concurrent.futures.as_completed(futures):
            genre_matches.update(future.result())
    return genre_matches


def compare(genre_chunk: List[ServiceGenre], musicbrainz_genres: List[MusicBrainzGenre]):
    """
    Try and find a matching musicbrainz
    :param genre_chunk:
    :param musicbrainz_genres:
    :return: dict of {service_genre: list of (match ratio, mb tag)}
    """

    ret = {}
    for genre in genre_chunk:
        matches = []
        for mbg in musicbrainz_genres:
            if DEBUG:
                if mbg.name == "abstract electronic" and genre.subgenre == "abstract":
                    print("abstract electronic")
                    print(f"{mbg.processed_name_words}, {genre.processed_full_genre_words}")
                    print(fuzz.token_sort_ratio(mbg.processed_name_words, genre.processed_full_genre_words))
            if genre.subgenre:
                ratio = fuzz.ratio(mbg.processed_name, genre.processed_subgenre)
                if ratio == 100:
                    matches.append(
                        MatchResult(musicbrainz=mbg, match=ratio, match_type=MatchType.SUBGENRE)
                    )
                if mbg.name.lower() == genre.lowercase_subgenre:
                    matches.append(
                        MatchResult(musicbrainz=mbg, match=100, match_type=MatchType.EXACT)
                    )
            ratio = fuzz.ratio(mbg.processed_name, genre.processed_parent_genre)
            if ratio == 100:
                matches.append(
                    MatchResult(musicbrainz=mbg, match=ratio, match_type=MatchType.PARENTGENRE)
                )

            ratio = fuzz.ratio(mbg.processed_name, genre.processed_full_genre)
            if ratio == 100:
                matches.append(
                    MatchResult(musicbrainz=mbg, match=ratio, match_type=MatchType.FULLGENRE)
                )
            ratio = fuzz.token_sort_ratio(mbg.processed_name_words, genre.processed_full_genre_words)
            if ratio == 100:
                matches.append(
                    MatchResult(musicbrainz=mbg, match=ratio, match_type=MatchType.TOKENSORT)
                )
        matches = sorted(matches, key=lambda m: m.match, reverse=True)
        ret[genre] = matches
    return ret


def main(genrefile, datafile, outfile=None):
    mb_genres: List[MusicBrainzGenre] = []
    with open(genrefile) as fp:
        reader = csv.DictReader(fp)
        for line in list(reader):
            mb_genres.append(
                MusicBrainzGenre(name=line["name"], is_genre=line["has_genre"] == 't', tag_count=line["ref_count"])
            )

    print(f"got {len(mb_genres)} genres")

    data_genres = []
    with open(datafile) as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            genre = line["genre"]
            # genres are either parent---subgenre, or just a main genre
            if '---' in genre:
                parent_genre, subgenre = genre.split('---')
            else:
                parent_genre, subgenre = genre, None
            data_genres.append(
                ServiceGenre(parent_genre=parent_genre, subgenre=subgenre, number_taggings=int(line["count"])))

    print(f"got {len(data_genres)} items from the datafile")

    t = time.monotonic()
    genre_matches = threaded_match_genres(data_genres, mb_genres)
    e = time.monotonic()
    print(e - t)

    print(f"{len(genre_matches)} matches")

    w = None
    fp = None
    if outfile == "-":
        fp = sys.stdout
    elif outfile:
        fp = open(outfile, "w")
    if fp:
        w = csv.writer(fp)
        w.writerow(["source parent genre", "source subgenre"] + ["mb tag", "type", "genre?"] * 4)

    sorted_matches = sorted(genre_matches.items(), key=lambda x: x[0].full_genre)
    for dataset_genre, matches in sorted_matches:
        print(f"* {dataset_genre.full_genre} (#{dataset_genre.number_taggings})")
        if DEBUG:
            for match in matches:
                print(f"    {match.musicbrainz.name} g={match.musicbrainz.is_genre} t={match.match_type}")
            print("----------")
        subgenrematch = get_match_for_matchtype(matches, MatchType.SUBGENRE)
        exactmatch = get_match_for_matchtype(matches, MatchType.EXACT)
        fullmatch = get_match_for_matchtype(matches, MatchType.FULLGENRE)
        parentmatch = get_match_for_matchtype(matches, MatchType.PARENTGENRE)

        for match in [subgenrematch, exactmatch, fullmatch, parentmatch]:
            if match:
                if match.match == 100:
                    print(f"    {match.musicbrainz.name} g={match.musicbrainz.is_genre} t={match.match_type}")

        # If this is the same match as the FULLGENRE match, don't show it
        tokenmatch = get_match_for_matchtype(matches, MatchType.TOKENSORT)
        if tokenmatch:
            if fullmatch is not None and tokenmatch.musicbrainz.name != fullmatch.musicbrainz.name and tokenmatch.match == 100:
                print(
                    f"    {tokenmatch.musicbrainz.name} g={tokenmatch.musicbrainz.is_genre} t={tokenmatch.match_type}")

        if w:
            sub = dataset_genre.subgenre
            row = [dataset_genre.parent_genre, sub if sub else ""]
            if not sub and parentmatch and parentmatch.musicbrainz.is_genre:
                # If there is no subgenre then only match the parent (if it's a genre)
                row += [parentmatch.musicbrainz.name, "parent", ""]
            else:
                row += get_ordered_list_of_matches(subgenrematch,
                                                   exactmatch,
                                                   parentmatch,
                                                   fullmatch, tokenmatch)
            w.writerow(row)

    if fp and outfile != "-":
        fp.close()


def get_ordered_list_of_matches(subgenrematch: MatchResult, exactmatch: MatchResult, parentmatch: MatchResult,
                                fullmatch: MatchResult, tokenmatch: MatchResult):
    ret = []
    if parentmatch and parentmatch.musicbrainz.is_genre:
        ret.extend([parentmatch.musicbrainz.name, "parent", ""])
    # If we get a match _and_ it's a genre in musicbrainz, this looks like a pretty good candidate
    for match, mt in [(subgenrematch, "subgenre"), (exactmatch, "exact"), (fullmatch, "full"), (tokenmatch, "unordered")]:
        if match and match.musicbrainz.is_genre:
            ret.extend([match.musicbrainz.name, mt, ""])
            return ret
    # we didn't return early, no genre match in sub/full/token, so iterate through them all
    # note that we prefer exact over subgenre match here
    # If we've seen the exact match before, or if we've seen something that looks similar after processing,
    # don't include it.
    seen_matches = set()
    for match, mt in [(exactmatch, "exact"), (subgenrematch, "subgenre"), (fullmatch, "full"), (tokenmatch, "unordered")]:
        if match and not fuzzy_match_seen(seen_matches, match.musicbrainz.name):
            ret.extend([match.musicbrainz.name, mt, "" if match.musicbrainz.is_genre else "n"])
            seen_matches.add(match.musicbrainz.name)
    return ret


def fuzzy_match_seen(seen_matches: Set[str], match: str):
    """See if a processed version of `match` appears as any element of seen_matches"""
    processed_match = utils.full_process(match).replace(" ", "")
    for sm in seen_matches:
        processed_sm = utils.full_process(sm).replace(" ", "")
        if processed_sm == processed_match:
            return True
    return False


def get_match_for_matchtype(matches: List[MatchResult], matchtype: MatchType) -> Optional[MatchResult]:
    matches = [match for match in matches if match.match_type == matchtype]
    sorted_matches = sorted(matches, key=lambda x: (x.match, x.musicbrainz.is_genre, x.musicbrainz.name), reverse=True)
    if sorted_matches:
        return sorted_matches[0]
    else:
        return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', required=False)
    parser.add_argument('genrefile')
    parser.add_argument('datafile')
    args = parser.parse_args()
    main(args.genrefile, args.datafile, args.o)
