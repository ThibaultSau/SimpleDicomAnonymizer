# SimpleDicomAnonymizer

Python script made for anonymizing DICOM data. Works on an allow list fashion, meaning you must specifiy all DICOM tags that needs to be kept and the way they should be.

## How to install

If you have python setup on your machine this script can be run like any other python package, creating an environment, installing dependencies via the requirements.txt file and running Anonymisation.py.

If you do not have python setup you can download the file dist.zip in the releases section, unzip it and run the executable from the folder dist/Anonymisation/Anonymisation.exe.

## How to setup

At the root of the dist folder there are 4 configuration text files, allowing to change the scripts behavior.

* corr_names : This file allows to anonymizes patients and directories names. Any occurences of the names that are in the first column ill be replaced with the name on te second column. Original name and anonymized name must be separated by a comma : ```,``` 
* extra_rules : lists all tags that must be kept and the required action that must be done to anonymize it. By default every that that is not mentionned in this list will be deleted. List of possible action are :
  * keep : keep tag as-is
  * empty : keep tag but remove iit's value
  * replace : replace with a non-zero length value that may be a dummy value and consistent with the VR 
  * keep_year : change the date to january 1st of the year. 
  * change_year : change date to january 1st 2021
  * anonymize_name : replace patient name with name specified in the corr_names.txt file
* folder : list all the input folders that should be anonymized, if more than one folder must be anonymized, each separate folder must be written on a separate line.
* out_folder : lists all the output folders that the anonymized data should be written to.

These files must be setup before launching the programm.

## Script behavior

The script will respect the directory structure of the input folders until a patient is reached (a folder is a patient folder if its name is present on the corr_name.txt file), then all DICOM files will be written directly under the patient folder. Any non-DICOM files will be ignored.
