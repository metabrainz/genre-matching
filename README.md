

Download data from https://zenodo.org/record/2553414

you only need the items that contain `-train.tsv.bz2` and `-validation.tsv.bz2` in the filename. 
You can skip the files that contain `-features-`.


Uncompress:

    bunzip2 acousticbrainz-mediaeval-discogs-train.tsv.bz2
    bunzip2 acousticbrainz-mediaeval-discogs-validation.tsv.bz2
    bunzip2 acousticbrainz-mediaeval-lastfm-train.tsv.bz2
    bunzip2 acousticbrainz-mediaeval-lastfm-validation.tsv.bz2
    bunzip2 acousticbrainz-mediaeval-tagtraum-train.tsv.bz2
    bunzip2 acousticbrainz-mediaeval-tagtraum-validation.tsv.bz2

Combine train and validation data into a single file listing the genres used in that source:

    python datafile-to-genrelist.py data/acousticbrainz-mediaeval-tagtraum-* > data/tagtraum-genre-and-counts.csv
    python datafile-to-genrelist.py data/acousticbrainz-mediaeval-lastfm-* > data/lastfm-genre-and-counts.csv
    python datafile-to-genrelist.py data/acousticbrainz-mediaeval-discogs-* > data/discogs-genre-and-counts.csv

Get a list of tags and genres from a musicbrainz 

\copy (select tag.name, tag.ref_count, genre.gid is not null as has_genre from tag left join genre on genre.name=tag.name order by has_genre desc, tag.name) to 'mb_tags.csv' with csv header;


Discogs tags come from releases, but we applied them to all recordings in that release group. We could
be a bit more careful about these when applying to MB - perhaps only add to RG or releases.

Observations:
 lots of tags with starting #, maybe remove them in MB
 autocomplete?
 

Todo tasks:
Short term
 - Abstract out 'Match' into class to make it easy to iterate and sort and store
 - Consider using just a string match, as most stuff is pretty good now?
 - hiphop/hip hop whitespace check
 - If no direct match, try and use the 'all tokens in a match' checker (hiphop/urban -> urban hip hop)

Long term - get more data
 - Re-run this tool with more MBIDs (especially on lastfm)
 - For discogs, try and use musicbrainz url links to discogs, 
      or parse the data dump (using typesense or our track matching algorithm?) to get more accurate matches
   

Hendrik Schreiber. Improving genre annotations for the million song dataset
https://archives.ismir.net/ismir2015/paper/000102.pdf

LEVERAGING KNOWLEDGE BASES AND PARALLEL ANNOTATIONS FOR MUSIC GENRE TRANSLATION
   https://archives.ismir.net/ismir2019/paper/000103.pdf


instead of matching mb -> dataset, find the best mb tag for each item in the dataset
If tag is 2 words and 1 word is 100%, then only return status of the other word
really treat a match as bad if the first letter is different