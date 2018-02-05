import glob
import tempfile

import pytest

from merge_rgba import merge_rgba_tool
import rasterio


@pytest.fixture()
def sources():
    paths = glob.glob("tests/data/sources/*.tif")
    return [rasterio.open(p, 'r') for p in paths]


def test_merge_rgba_tool(sources):
    outtif = tempfile.NamedTemporaryFile(suffix='.tif').name
    merge_rgba_tool(sources, outtif)
    with rasterio.open(outtif) as merged:
        assert merged.shape == (600, 600)
