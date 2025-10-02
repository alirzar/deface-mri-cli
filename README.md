# MRI Defacing Tool for ds004021

This repository contains a Python script for defacing MRI images in the ds004021 dataset. Defacing ensures subject privacy by automatically removing identifiable facial features from neuroimaging data prior to analysis, sharing, or publication.

## Script

- **deface_ds004021_separate_out.py**  
  Removes facial features from all MRI images in BIDS-formatted dataset `ds004021`. The script processes each subject/session and saves defaced images separately.

## Usage

1. Place the script in your dataset root or processing directory.
2. Run with Python 3 and the required dependencies (ensure nibabel and numpy are installed).
3. Adjust input/output dataset paths inside the script as needed.

## Notes

- Always verify output images and retain original unmodified data for audit/tracking.
- This tool is specific to the ds004021 dataset format but can be adapted for similar BIDS datasets.
