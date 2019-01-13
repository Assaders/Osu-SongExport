# Osu! song export
This project aims to provide convenient script that allows to export songs from Osu! beatmaps

**Options**
-
* `-i, -in` Osu! songs directory. On Windows script can find this through registry if Osu! was installed properly.
* `-o, -out` Output directory for exported songs.
* `-rr, -override` With this parameter script will rewrite existing songs in output directory with same name. Overwise new files with existing names will be ignored. 

**Features**
-
* Identifies unique songs through .osu files
* Places missing metadata for songs (artist and track name)