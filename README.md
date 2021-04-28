

Download data from 

Uncompress:

    bunzip2 acousticbrainz-mediaeval-discogs-train.tsv.bz2
    bunzip2 acousticbrainz-mediaeval-discogs-validation.tsv.bz2
    bunzip2 acousticbrainz-mediaeval-lastfm-train.tsv.bz2
    bunzip2 acousticbrainz-mediaeval-lastfm-validation.tsv.bz2
    bunzip2 acousticbrainz-mediaeval-tagtraum-train.tsv.bz2
    bunzip2 acousticbrainz-mediaeval-tagtraum-validation.tsv.bz2

Combine train and validation data into a single 



Discogs tags come from releases, but we applied them to all recordings in that release group. We could
be a bit more careful about these when applying to MB - perhaps only add to RG or releases.



Todo tasks:
 - Re-run this tool with more MBIDs (especially on lastfm)
 - For discogs, try and use musicbrainz url links to discogs, 
      or parse the data dump (using typesense or our track matching algorithm?) to get more accurate matches
   

Hendrik Schreiber. Improving genre annotations for the million song dataset
LEVERAGING KNOWLEDGE BASES AND PARALLEL ANNOTATIONS FOR MUSIC GENRE TRANSLATION
   https://archives.ismir.net/ismir2019/paper/000103.pdf


instead of matching mb -> dataset, find the best mb tag for each item in the dataset
If tag is 2 words and 1 word is 100%, then only return status of the other word
really treat a match as bad if the first letter is different