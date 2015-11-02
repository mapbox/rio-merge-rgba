# rio merge-rgba

A `rio merge` alternative optimized for large RGBA scenetifs.

`rio merge-rgba` is a CLI with nearly identical arguments to `rio merge`. They accomplish the same task, merging many rasters into one. 

```
$ rio merge-rgba --help
Usage: rio merge-rgba [OPTIONS] INPUTS... OUTPUT

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

The differences are in the implementation, `rio merge-rgba`:

1. only accepts 4-band RGBA rasters
2. writes the destination data to disk rather than an in-memory array
3. reads/writes in windows corresponding to the destination block layout
4. once a window is filled with data values, the rest of the source files are skipped for that window

### Why windowed and why write to disk? 

Memory efficiency. You'll never load more than `2 * blockxsize * blockysize` pixels into numpy arrays at one time, assuming garbage collection is infallible and there are no memory leaks.

While this does mean reading and writing to disk more frequently, having spatially aligned data with identical block layouts (like scenetifs) can make that as efficient as possible. Also...

### Why only RGBA?

`rio merge` is more flexible with regard to nodata. It relies on reads with `masked=True` to handle that logic across all cases. 

By contrast, `rio merge-rgba` requires RGBA images because, by reading with `masked=False` and using the alpha band as the sole source of nodata-ness, we get huge speedups over the rio merge approach. Roughly 40x faster for my test cases. The exact reasons behind the discrepency is TBD but since we're reading/writing more intensively with the windowed approach, we need to keep IO as efficient as possible.

### Why not improve rio merge

I tried but the speed advantage comes from avoiding masked reads. Once we improve the efficiency of masked reads or invent another mechanism for handling nodata masks that is more efficient, we can pull the windowed approach [back into rasterio](https://github.com/mapbox/rasterio/issues/507)


### Benchmarks

Very promising. On the Landsat scenetif set from `s3://mapbox-pxm-live/scenes/7-21-49*` - 23 rasters in total. I created reduced resolution versions of each in order to test the performance charachteristics as sizes increase.

<table class="dataframe" border="1">
  <thead>
    <tr>
      <th>resolution</th>
      <th>raster size</th>
      <th>rio merge Memory (MB)</th>
      <th>merge_rgba Memory (MB)</th>
      <th>rio merge Time (s)</th>
      <th>merge_rgba Time (s)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>300</th>
      <th>1044x1044</th>
      <td>135</td>
      <td>83</td>
      <td>1.10</td>
      <td>0.70</td>
    </tr>
    <tr>
      <th>150</th>
      <th>2088x2088</th>
      <td>220</td>
      <td>107</td>
      <td>3.20</td>
      <td>1.90</td>
    </tr>
    <tr>
      <th>90</th>
      <th>3479x3479</th>
      <td>412</td>
      <td>115</td>
      <td>8.85</td>
      <td>3.10</td>
    </tr>
    <tr>
      <th>60</th>
      <th>5219x5219</th>
      <td>750</td>
      <td>121</td>
      <td>25.00</td>
      <td>7.00</td>
    </tr>
    <tr>
      <th>30</th>
      <th>10436x10436</th>
      <td><i>1GB+ crashed</i></td>
      <td>145</td>
      <td><i>crashed at 38 minutes</i></td>
      <td>19.80</td>
    </tr>
  </tbody>
</table>

Note that the "merge_aligned" refered to in the charts is the same command, just renamed:

![mem](https://gist.githubusercontent.com/perrygeo/063dddae6fa134908861/raw/ac2c2200e564e8b89ed1d78383e962f22ccfa21c/mem.png)

![speed](https://gist.githubusercontent.com/perrygeo/063dddae6fa134908861/raw/ac2c2200e564e8b89ed1d78383e962f22ccfa21c/time.png)

### Note about pixel alignment

Since the inclusion of the [full cover window](https://github.com/mapbox/rasterio/pull/466) in rasterio, there is a possibility of including an additional bottom row or right column if the bounds of the destination are not directly aligned with the source.

In rio merge, which reads the entire raster at once, this can manifest itself as one additional row and column on the bottom right edge of the image. The image within remains consistent.

With `merge_rgba.py`, if we used the default full cover window, errors may appear within the image at block window boundaries where e.g. a 257x257 window is read into a 256x256 destination. To avoid this, we effectively embed a reimplementation of rasterio's `get_window` using the `round` operator which improves our chances that the pixel boundaries are snapped to appropriate bounds.

You may see small differences between rio merge and merge_rgba as a result but they *should* be limited to the single bottom row and right-most column.
