# =============================================================================
# FW 532 -- install the R packages used in the labs
#
# Run this once at the start of the term:
#   1. Open fw532.Rproj in RStudio or Positron.
#   2. In the Console, type:   source("install_packages.R")
#
# It only installs packages you don't already have, so it's safe to re-run.
# =============================================================================

if (getRversion() < "4.3.0") {
  warning("These labs were tested with R 4.5. You have R ", getRversion(),
          ". Please update R (https://cloud.r-project.org) if you run into problems.")
}

packages <- c(
  # everywhere
  "terra",        # rasters (replaces the retired raster + sp packages)
  "sf",           # vector spatial data
  "here",         # find files relative to the project folder
  "ggplot2", "ggcorrplot",
  "knitr", "rmarkdown",
  # Lab 2: evaluation
  "caret", "pROC", "PRROC", "blockCV",
  # Lab 3: trees
  "rpart", "rpart.plot",
  # Lab 4: random forests
  "randomForest", "ranger", "tictoc", "pdp",
  # Lab 5: boosted regression trees
  "gbm", "dismo",
  # Lab 6: Maxent
  "maxnet",
  # Lab 7 (bonus) and demos
  "neuralnet", "plotly", "lattice", "spatstat", "ape"
)

missing <- setdiff(packages, rownames(installed.packages()))
if (length(missing) > 0) {
  message("Installing: ", paste(missing, collapse = ", "))
  install.packages(missing, repos = "https://cloud.r-project.org")
} else {
  message("All lab packages are already installed.")
}

# Quick check that the key packages load and the course data can be read
library(terra)
env <- rast(here::here("data", "envStack.tif"))
message("Success! Read ", nlyr(env), " environmental layers. You're ready for Lab 1.")
