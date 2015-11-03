import logging
import os
import rasterio
import click

from cligj import files_inout_arg, format_opt
from rasterio.rio.helpers import resolve_inout
from rasterio.rio import options
from merge_rgba import merge_rgba_tool

logger = logging.getLogger('merge_rgba')

@click.group()
def cli():
    pass

@click.command(name="merge-rgba", short_help="Merge a stack of RGBA raster datasets.")
@files_inout_arg
@options.output_opt
@options.bounds_opt
@options.resolution_opt
@click.option('--force-overwrite', '-f', 'force_overwrite', is_flag=True,
              type=bool, default=False,
              help="Do not prompt for confirmation before overwriting output "
                   "file")
@click.option('--precision', type=int, default=7,
              help="Number of decimal places of precision in alignment of "
                   "pixels")
@options.creation_options
def merge_rgba(files, output, bounds, res, force_overwrite,
               precision, creation_options):

    output, files = resolve_inout(files=files, output=output)

    if os.path.exists(output) and not force_overwrite:
        raise click.ClickException(
            "Output exists and won't be overwritten without the "
            "`-f` option")

    sources = [rasterio.open(f) for f in files]
    merge_rgba_tool(sources, output, bounds=bounds, res=res,
                    precision=precision,
                    creation_options=creation_options)

cli.add_command(merge_rgba)
