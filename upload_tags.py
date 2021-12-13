# Upload a list of tags to MusicBrainz

import argparse
import csv
import json
import os
import time
from datetime import timedelta

import musicbrainzngs

musicbrainzngs.set_useragent("MB-Tagsubmit", "0.1", "Alastair")
# We have a temporary limit exemption, so do up to 5 queries per second
musicbrainzngs.set_rate_limit(1, 5)

musicbrainzngs.set_hostname("test.musicbrainz.org", True)

musicbrainzngs.auth('alastairp', 'mb')


ITEMS_PER_CHUNK = 25


def load_submit_cache(tagfile):
    cachefile = f"{tagfile}.submitcache"

    if not os.path.exists(cachefile):
        return []
    with open(cachefile) as fp:
        return json.load(fp)


def save_submit_cache(tagfile, submitted_mbids):
    cachefile = f"{tagfile}.submitcache"

    with open(cachefile, 'w') as fp:
        json.dump(submitted_mbids, fp)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def main(tagtype, tagfile):
    submitted_items = load_submit_cache(tagfile)
    with open(tagfile) as fp:
        reader = csv.reader(fp)
        tags = {}
        for line in reader:
            tags[line[0]] = line[1:]

        print(f"Loaded {len(tags)} tags")
        tags = {k: v for k, v in tags.items() if k not in submitted_items}
        print(f"After filtering submitted items, {len(tags)} tags remaining")

    start = time.monotonic()
    numtags = len(tags)
    chunk_count = 0
    tgs = list(sorted(tags.keys()))
    for mbids in chunks(tgs[:10], ITEMS_PER_CHUNK):
        to_submit = {}
        for m in mbids:
            to_submit[m] = tags[m]
        
        #print(to_submit)
        musicbrainzngs.submit_tags(recording_tags=to_submit)

        submitted_items += mbids
        save_submit_cache(tagfile, submitted_items)
        chunk_count += 1
        print_status_update(chunk_count, numtags, start)


def print_status_update(chunk_count, number_chunks, start_time):
    """Print a basic status update based on how many chunks have been computed"""
    chunk_time = time.monotonic()
    chunk_percentage = chunk_count / number_chunks
    duration = round(chunk_time - start_time)
    durdelta = timedelta(seconds=duration)
    remaining = round((duration / (chunk_percentage or 0.01)) - duration)
    remdelta = timedelta(seconds=remaining)
    if number_chunks > 0:
        print(f" - Done {chunk_count}/{number_chunks} in {str(durdelta)}; {str(remdelta)} remaining")
    else:
        print(f" No chunks processed in {str(durdelta)}; {str(remdelta)} remaining") 



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('type', help='"rec" or "rg"')
    parser.add_argument('tagfile')

    args = parser.parse_args()

    main(args.type, args.tagfile)