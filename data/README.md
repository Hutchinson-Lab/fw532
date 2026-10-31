# Course data

## `envStack.tif`

A 20-layer GeoTIFF of environmental variables covering roughly North America,
used by every lab (R and Python read the same file).

* **Source:** [WorldClim](https://www.worldclim.org/data/bioclim.html) bioclimatic
  variables (averages for 1970–2000) plus elevation.
* **Resolution:** 10 arc-minutes (1/6 degree; about 13 km at 45° latitude).
* **Extent:** longitude −167.67 to −52.5, latitude 7.17 to 71.33.
* **Coordinate system:** WGS 84 longitude/latitude (EPSG:4326).
* **Grid:** 385 rows × 691 columns; ocean cells are missing (NA / NaN).

| Layer | Name | WorldClim code | Units |
|---:|---|---|---|
| 1 | Annual.Mean.Temperature | BIO1 | °C |
| 2 | Mean.Diurnal.Range | BIO2 | °C |
| 3 | Isothermality | BIO3 | % (BIO2/BIO7 × 100) |
| 4 | Temperature.Seasonality | BIO4 | sd × 100 |
| 5 | Max.Temperature.of.Warmest.Month | BIO5 | °C |
| 6 | Min.Temperature.of.Coldest.Month | BIO6 | °C |
| 7 | Temperature.Annual.Range | BIO7 | °C |
| 8 | Mean.Temperature.of.Wettest.Quarter | BIO8 | °C |
| 9 | Mean.Temperature.of.Driest.Quarter | BIO9 | °C |
| 10 | Mean.Temperature.of.Warmest.Quarter | BIO10 | °C |
| 11 | Mean.Temperature.of.Coldest.Quarter | BIO11 | °C |
| 12 | Annual.Precipitation | BIO12 | mm |
| 13 | Precipitation.of.Wettest.Month | BIO13 | mm |
| 14 | Precipitation.of.Driest.Month | BIO14 | mm |
| 15 | Precipitation.Seasonality | BIO15 | coefficient of variation |
| 16 | Precipitation.of.Wettest.Quarter | BIO16 | mm |
| 17 | Precipitation.of.Driest.Quarter | BIO17 | mm |
| 18 | Precipitation.of.Warmest.Quarter | BIO18 | mm |
| 19 | Precipitation.of.Coldest.Quarter | BIO19 | mm |
| 20 | elevation | — | m |

A few cells have values for some layers but not others (e.g., 99 coastal cells
have climate data but no elevation). Most labs only use cells with data in all
20 layers.

In earlier years this stack was distributed as `envStack.RData` (a `raster`
package object). It was converted to GeoTIFF so that it no longer depends on the
retired `raster`/`sp` workflow and can be read from Python.
