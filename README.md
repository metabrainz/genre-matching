# Genre tags for recordings in MusicBrainz

Over a few months in 2021 we added almost 6 million new genre tags to over 1.3 million recordings in the MusicBrainz database

The source for these genres came from three locations: genre anotations in discogs, tags from last.fm, and tags from beatunes.

The data was collected as part of a research project: [The AcousticBrainz Genre Dataset](https://github.com/MTG/acousticbrainz-genre-dataset).

This repository contains the code used to generate and submit the data. This document describes the steps that we took to
process the original datasets, convert the annotations to the tag/genre structure used in MusicBrainz, and submit them.

### Data collection

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

Get a list of tags and genres from a musicbrainz database mirror

    \copy (select tag.name, tag.ref_count, genre.gid is not null as has_genre from tag left join genre on genre.name=tag.name order by has_genre desc, tag.name) to 'mb_tags.csv' with csv header;

### Dependencies

Python dependencies are included in `requirements.txt`

    pip install -r requirements.txt


### Mapping data sources to MusicBrainz

Genre annotations from the dataset come in a two level hierarchy, for example "rock---blues rock". We took each of these parts
and independently tried to map each of them to genre tags in MusicBrainz. We applied some fuzzy matching techniques to try to
identify cases where a tag was slightly different, e.g., where it used characters such as & or - or an extra/missing space.
In almost all cases we were able to map annotations to an actual genre in the MusicBrainz database.

Given a data file and a list of tags from musicbrainz, generate a list of proposed mappings from the service to MusicBrainz

    python main.py -o lastfm-to-mb-tags.csv mb_tags.csv data/lastfm-genre-and-counts.csv

The resulting output file (specified with the -o flag) includes two columns for a main/secondary genre, then groups of three 
columns, mbtag - the MusicBrainz tag that was matched, type - some metadata about the way that the match was made, and genre? - 
an indicator if the matched tag is marked as a genre in the MusicBrainz database. Ideally, each genre should map to just one
tag in MusicBrainz, though sometimes when we couldn't make a strong match we listed a few possible candidates.

Once this is done, some mappings might still be wrong, or we might want to remove some tags which we don't think fit well.

We loaded these output files (`lastfm-to-mb-tags.csv` etc) into a collaborative spreadsheet and manually checked them, making 
a correction file with columns `genre,subgenre,replacement,tags`

For example, we changed the tag `jazz---modernjazz` to `modern jazz` by including a row

    jazz,modernjazz,jazz,modern jazz

To remove a tag, put it in the file but don't include any replacement tags. For example we removed the `oldie` tag with a row:

    oldie,,


Re-run the mapper, including the manual mapping file

    python main.py -o lastfm-to-mb-tags.csv -m lastfm-mapping.csv mb_tags.csv data/lastfm-genre-and-counts.csv

now given the mapping and the data file, generate a list of Recording MBIDs to MusicBrainz tags

    python generate_mb_tags_for_source.py lastfm-to-mb-tags.csv data/lastfm.tsv > lastfm-tags-to-submit.csv
 

upload:

    python upload_tags.py rec lastfm-tags-to-submit.csv


## Recreating data files

We don't include the final list of tags that were submitted in this repository due to their size, however you
can recreate them yourself using the list of MusicBrainz tags and the manual mapping files, which are included.

We include the four key data and mapping files that we created:

 * mapping/mb_tags.csv - the state of the MusicBrainz tags/genre list at the moment we did this project
 * mapping/discogs-mapping.csv
 * mapping/lastfm-mapping.csv
 * mapping/tagtraum-mapping.csv - individual mapping files for each service

For example, for the last.fm dataset, run the following:

    bunzip2 acousticbrainz-mediaeval-lastfm-train.tsv.bz2
    bunzip2 acousticbrainz-mediaeval-lastfm-validation.tsv.bz2
    python datafile-to-genrelist.py data/acousticbrainz-mediaeval-lastfm-* > data/lastfm-genre-and-counts.csv
    python main.py -o lastfm-to-mb-tags.csv -m mapping/lastfm-mapping.csv mapping/mb_tags.csv data/lastfm-genre-and-counts.csv
    python generate_mb_tags_for_source.py lastfm-to-mb-tags.csv data/acousticbrainz-mediaeval-lastfm-train.tsv > lastfm-tags-to-submit.csv