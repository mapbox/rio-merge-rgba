# merge_rgba.py

A `rio merge` alternative optimized for large RGBA scenetifs

**Note**
This repository is in limbo and may move in one of several directions:
1. These optimizations may be pulled directly into `rasterio` (see [this issue](https://github.com/mapbox/rasterio/issues/507))
2. This may become an intergrated part of `pxm`
3. This may stay as an independent repo and become a legit pip-installable, tested module

## What it it?

`merge_rgba.py` is a CLI with nearly identical arguments to `rio merge`. They accomplish the same task, merging many rasters into one. The differences are in the implementation:

```
$ python merge_rgba.py --help
Usage: merge_rgba.py [OPTIONS] INPUTS... OUTPUT

Options:
  -o, --output PATH            Path to output file (optional alternative to a
                               positional arg for some commands).
  -f, --format, --driver TEXT  Output format driver
  --bounds FLOAT...            Output bounds: left bottom right top.
  -r, --res FLOAT              Output dataset resolution in units of
                               coordinate reference system. Pixels assumed to
                               be square if this option is used once,
                               otherwise use: --res pixel_width --res
                               pixel_height
  -f, --force-overwrite        Do not prompt for confirmation before
                               overwriting output file
  --precision INTEGER          Number of decimal places of precision in
                               alignment of pixels
  --co NAME=VALUE              Driver specific creation options.See the
                               documentation for the selected output driver
                               for more information.
  --help                       Show this message and exit.
```

`merge_rgba.py`
1. only accepts 4-band RGBA rasters
2. writes the destination data to disk rather than an in-memory array
3. reads/writes in windows corresponding to the destination block layout
4. once a window is filled with data values, the rest of the source files are skipped for that window

### Why windowed and why write to disk? 

Memory efficiency. You'll never load more than `(len(sources) + 1) * blockxsize * blockysize` pixels into numpy arrays at one time. 

While this does mean reading and writing to disk more frequently, having spatially aligned data with identical block layours (like scenetifs) can make that as efficient as possible. Also...

### Why only RGBA?

`rio merge` is more flexible with regard to nodata. It relies on masked reads to handle that logic across all cases. 

By reading with `masked=False` and using the alpha band as the sole source of nodata-ness, we get huge speedups over the rio merge approach. Roughly 40x faster for my test cases. The exact reasons behind the discrepency is TBD but since we're reading/writing more intensively with the windowed approach, we need to keep IO as efficient as possible.

### Why not improve rio merge

I tried but the speed advantage comes from avoiding masked reads. Once we improve the efficiency of masked reads or invent another mechanism for handling nodata masks that is more efficient, we can the windowed approach [back into rasterio](https://github.com/mapbox/rasterio/issues/507))
