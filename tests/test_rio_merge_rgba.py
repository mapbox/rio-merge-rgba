import sys
import os
import logging

from affine import Affine
import numpy
from click.testing import CliRunner
from pytest import fixture
import rasterio
from rasterio.rio.main import main_group
from rasterio.enums import Compression

from merge_rgba.scripts.cli import merge_rgba


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# Fixture to create test datasets within temporary directory
@fixture(scope='function')
def test_data_dir_1(tmpdir):
    kwargs = {
        "crs": {'init': 'epsg:4326'},
        "transform": Affine.from_gdal(-114, 0.2, 0, 46, 0, -0.2),
        "count": 4,
        "dtype": rasterio.uint8,
        "driver": "GTiff",
        "width": 10,
        "height": 10
    }

    with rasterio.Env():

        with rasterio.open(str(tmpdir.join('b.tif')), 'w', **kwargs) as dst:
            data = numpy.zeros((4, 10, 10), dtype=rasterio.uint8)
            data[0:3, 0:6, 0:6] = 255
            data[3, 0:6, 0:6] = 255
            dst.write(data)

        with rasterio.open(str(tmpdir.join('a.tif')), 'w', **kwargs) as dst:
            data = numpy.zeros((4, 10, 10), dtype=rasterio.uint8)
            data[0:3, 4:8, 4:8] = 254
            data[3, 4:8, 4:8] = 255
            dst.write(data)

    return tmpdir


def test_merge_rgba(test_data_dir_1):
    outputname = str(test_data_dir_1.join('merged.tif'))
    inputs = [str(x) for x in test_data_dir_1.listdir()]
    inputs.sort()
    runner = CliRunner()
    result = runner.invoke(merge_rgba, inputs + [outputname])
    assert result.exit_code == 0
    assert os.path.exists(outputname)
    with rasterio.open(outputname) as out:
        assert out.count == 4
        data = out.read(1, masked=False)
        expected = numpy.zeros((10, 10), dtype=rasterio.uint8)
        expected[0:6, 0:6] = 255
        expected[4:8, 4:8] = 254
        assert numpy.all(data == expected)

        alpha = out.read(4, masked=False)
        expected = numpy.zeros((10, 10), dtype=rasterio.uint8)
        expected[0:6, 0:6] = 255
        expected[4:8, 4:8] = 255
        assert numpy.all(alpha == expected)


def test_merge_rgba_vs_merge(test_data_dir_1):

    output1 = str(test_data_dir_1.join('merged1.tif'))
    output2 = str(test_data_dir_1.join('merged2.tif'))
    inputs = [str(x) for x in test_data_dir_1.listdir()]
    inputs.sort()
    runner = CliRunner()
    result = runner.invoke(merge_rgba, inputs + [output1])
    assert result.exit_code == 0
    assert os.path.exists(output1)
    result = runner.invoke(main_group, ['merge'] + inputs + [output2])
    assert result.exit_code == 0
    assert os.path.exists(output1)

    with rasterio.open(output1) as out1:
        with rasterio.open(output2) as out2:
            assert numpy.array_equal(out1.read(), out2.read())

def test_merge_rgba_bounds(test_data_dir_1):
    outputname = str(test_data_dir_1.join('merged.tif'))
    inputs = [str(x) for x in test_data_dir_1.listdir()]
    inputs.sort()
    runner = CliRunner()
    bounds = ["--bounds"] + "-113.4 44.8 -112.8 45.4".split()
    result = runner.invoke(merge_rgba, inputs + [outputname] + bounds)
    assert result.exit_code == 0
    with rasterio.open(outputname) as out:
        assert out.count == 4
        data = out.read(1, masked=False)
        expected = numpy.array(
            [[255, 255, 255,   0],
             [255, 254, 254, 254],
             [255, 254, 254, 254],
             [0,   254, 254, 254]]).astype('uint8')
        assert numpy.all(data == expected)


def test_merge_rgba_res(test_data_dir_1):
    outputname = str(test_data_dir_1.join('merged.tif'))
    inputs = [str(x) for x in test_data_dir_1.listdir()]
    inputs.sort()
    runner = CliRunner()
    bounds = ["--res", "0.4"]
    result = runner.invoke(merge_rgba, inputs + [outputname] + bounds)
    assert result.exit_code == 0
    with rasterio.open(outputname) as out:
        assert out.count == 4
        data = out.read(1, masked=False)
        expected = numpy.array(
            [[255, 255, 255,   0,   0],
             [255, 255, 255,   0,   0],
             [255, 255, 254, 254,   0],
             [0,     0, 254, 254,   0],
             [0,     0,   0,   0,   0]]).astype('uint8')
        assert numpy.all(data == expected)


def test_merge_output_exists(tmpdir, test_data_dir_1):
    outputname = str(tmpdir.join('merged.tif'))
    runner = CliRunner()
    rast = str(test_data_dir_1.listdir()[0])
    result = runner.invoke(
        merge_rgba,
        [rast, outputname])
    assert result.exit_code == 0
    result = runner.invoke(
        merge_rgba,
        [rast, outputname])
    assert os.path.exists(outputname)
    with rasterio.open(outputname) as out:
        assert out.count == 4


def test_rgba_only(tmpdir):
    outputname = str(tmpdir.join('merged.tif'))
    inputs = ['tests/data/rgb1.tif']
    runner = CliRunner()
    result = runner.invoke(merge_rgba, inputs + [outputname])
    assert result.exit_code == -1
    assert 'Inputs must be 4-band RGBA rasters' in str(result.exception) 


@fixture(scope='function')
def test_data_dir_2(tmpdir):
    kwargs = {
        "crs": {'init': 'epsg:4326'},
        "transform": Affine.from_gdal(-114, 0.2, 0, 46, 0, -0.2),
        "count": 4,
        "dtype": rasterio.uint8,
        "driver": "GTiff",
        "width": 10,
        "height": 10
    }

    with rasterio.Env():

        with rasterio.open(str(tmpdir.join('b.tif')), 'w', **kwargs) as dst:
            data = numpy.zeros((4, 10, 10), dtype=rasterio.uint8)
            data[0:3, 0:6, 0:6] = 255
            data[3, 0:6, 0:6] = 255
            dst.write(data)

        with rasterio.open(str(tmpdir.join('a.tif')), 'w', **kwargs) as dst:
            data = numpy.ones((4, 10, 10), dtype=rasterio.uint8)
            data[3, :, :] = 255  # no nodata
            dst.write(data)

    return tmpdir


def test_merge_rgba_allfull(test_data_dir_2):
    outputname = str(test_data_dir_2.join('merged.tif'))
    inputs = [str(x) for x in test_data_dir_2.listdir()]
    inputs.sort()
    runner = CliRunner()
    result = runner.invoke(merge_rgba, inputs + [outputname])
    assert result.exit_code == 0
    assert os.path.exists(outputname)
    with rasterio.open(outputname) as out:
        assert out.count == 4
        data = out.read(1, masked=False)
        expected = numpy.ones((10, 10), dtype=rasterio.uint8)
        assert numpy.all(data == expected)


@fixture(scope='function')
def test_data_dir_3(tmpdir):
    kwargs = {
        "crs": {'init': 'epsg:4326'},
        "transform": Affine.from_gdal(-114, 0.1, 0, 46, 0, -0.1),
        "count": 4,
        "dtype": rasterio.uint8,
        "driver": "GTiff",
        "width": 32,
        "height": 32,
        "compress": "JPEG"
    }

    with rasterio.Env():

        with rasterio.open(str(tmpdir.join('a.tif')), 'w', **kwargs) as dst:
            data = numpy.ones((4, 32, 32), dtype=rasterio.uint8)
            data[3, :, :] = 255
            dst.write(data)
    return tmpdir


def test_opts(test_data_dir_3):
    outputname = str(test_data_dir_3.join('merged.tif'))
    inputs = [str(x) for x in test_data_dir_3.listdir()]
    inputs.sort()
    runner = CliRunner()

    co = ["--co", "tiled=true",
          "--co", "blockxsize=16",
          "--co", "blockysize=16"]
    result = runner.invoke(merge_rgba, inputs + [outputname] + co)
    assert result.exit_code == 0
    assert os.path.exists(outputname)
    with rasterio.open(outputname) as out:
        assert out.count == 4
        assert out.profile['tiled'] == True
        assert out.profile['blockxsize'] == 16
        assert out.profile['blockysize'] == 16
        assert out.profile['compress'] == "jpeg"  # from src data
        assert out.compression == Compression.jpeg

    outputname = str(test_data_dir_3.join('merged2.tif'))
    co = ["--co", "tiled=true",
          "--co", "blockxsize=16",
          "--co", "blockysize=16",
          "--co", "compress=none"]
    result = runner.invoke(merge_rgba, inputs + [outputname] + co)
    assert result.exit_code == 0
    assert os.path.exists(outputname)
    with rasterio.open(outputname) as out:
        assert out.count == 4
        assert out.profile['tiled'] == True
        assert out.profile['blockxsize'] == 16
        assert out.profile['blockysize'] == 16
        assert out.profile['compress'] == "none"
        assert out.compression is None
