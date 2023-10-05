#!/usr/bin/env python
# coding: utf-8
 
import logging
from logging.handlers import RotatingFileHandler
import traceback

import os
import re


os .chdir("..")
regexp = re.compile('.([0-9]*/?){3}.-.([0-9]*/?){3}.')

# création de l'objet logger qui va nous servir à écrire dans les logs
logger = logging.getLogger()
# on met le niveau du logger à DEBUG, comme ça il écrit tout
logger.setLevel(logging.DEBUG)
 
# création d'un formateur qui va ajouter le temps, le niveau
# de chaque message quand on écrira un message dans le log
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
# création d'un handler qui va rediriger une écriture du log vers
# un fichier en mode 'append', avec 1 backup et une taille max de 1Mo

log_file = 'activity.log'


if os.path.isfile(log_file):
    os.remove(log_file)
file_handler = RotatingFileHandler(log_file, 'a', 5000000000, 15)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)

logger.info("Anonymization script started !\n")

try :
    import dicomanonymizer
    import json
    import csv
    import sys

    import pydicom
    from pydicom import dcmread
    from glob import glob
    from collections import defaultdict

    from threading import Thread

    pydicom.config.replace_un_with_known_vr = False

    input_dicom_path = [os.path.normpath(path.rstrip('\n')) for path in open("folder.txt","r").readlines()]
    try :
        output_dicom_path = [os.path.normpath(path.rstrip('\n')) for path in open("out_folder.txt","r").readlines()]
    except :
        output_dicom_path = [input_dicom_path+"_anonymized"]

    logger.info(f'Reading from {input_dicom_path} and outputing to {output_dicom_path}.\n')
    
    for path in output_dicom_path :
        if not os.path.isdir(path):
            logger.warning(f"output path {path} does not exist, creating")
            os.mkdir(path)

    def anonymize_dcm_file(inFile, out_files, anonymization_rules, anonymized_patient_name=None):
        """Anonymize a DICOM file by modyfying personal tags
        Conforms to DICOM standard except for customer specificities.
        :param inFile: File path or file-like object to read from
        :param out_files: File path or file-like object to write to
        :param extraAnonymizationRules: add more tag's actions
        """
        try :
            try :
                dataset = pydicom.dcmread(inFile,stop_before_pixels=False,force = True)
            except Exception as e:
                e.args+=("Reading error",)
                raise

            try :
                series_desc = dataset[0x8,0x103e].repval.lower()
                if 'orientation' in series_desc:
                    logger.warning(f"File {inFile} ignored, is orientation file")
                    return
                if ("new" in series_desc and 't2' not in series_desc )or 'creen' in series_desc or 'electronic' in series_desc or 'images trait' in series_desc or "time to peak" in series_desc:
                    logger.warning(f"File {inFile} ignored, unanonimyzed images")
                    return
                if 'phoenix' in series_desc :
                    logger.warning(f"File {inFile} ignored, PhoenixZipFile")
                    return
                if 'anonymized' in series_desc:
                    logger.warning(f"File {inFile} ignored, series desc is 'ANONYMIZED' ")
                    return
                # if (regexp.match(series_desc.strip('\'')) is not None) or 'perf' in series_desc or 'dyn' in series_desc:
                #     logger.warning(f"File {inFile} ignored, sequence is a perfusion")
                #     return
                # if "diff" in series_desc:
                #     logger.warning(f"File {inFile} ignored, is diffusion")
                #     return
                if 'loc' in series_desc or 'reperage' in series_desc or 'survey' in series_desc or 'cal' in series_desc:
                    logger.warning(f"File {inFile} ignored, is localization")
                    return
                if 'cal' in series_desc:
                    logger.warning(f"File {inFile} ignored, is calibration")
                    return
                if 'olea' in series_desc:
                    logger.warning(f"File {inFile} ignored, is olea related")
                    return
                if 'refor' in series_desc:
                    logger.warning(f"File {inFile} ignored, is reformatted")
                    return                    
            except :
                logger.warning(f"No series description (field [0x8,0x103e]) for file {inFile}, ignoring file")
                return

            inFile = inFile.rstrip('\uf029')
            start_length = len(dataset)
            for i in dataset:
                try :
                    if (i.keyword == 'PatientName' or i.keyword == 'PatientID'):
                        anonymization_rules[(i.tag.group,i.tag.elem)](dataset,(i.tag.group,i.tag.elem),anonymized_patient_name)
                    else:
                        anonymization_rules[(i.tag.group,i.tag.elem)](dataset,(i.tag.group,i.tag.elem))
                except Exception as e:
                    e.args += (str(i),)
                    e.args += (anonymization_rules[(i.tag.group,i.tag.elem)],)
                    raise
            logger.info(f"Dicom file {inFile}, length : {start_length} reduced to : {len(dataset)}, saving to {out_files}")
            for out_file in out_files:
                dataset.save_as(out_file)
        except Exception as e :
            logger.error(f"file {inFile} anonymization failed, Stacktrace :")
            for arg in e.args:
                logger.error(arg)

    def anonymize_recursively(input_dicom_path, output_dicom_path, extra_anonymization_rules = None, name_anonymization_dict={}, anonymized_patient_name=None, folder_min_size=15,file_record_name=None):
        anonymization_rules = defaultdict(lambda : dicomanonymizer.delete )
        if (extra_anonymization_rules is not None):
            anonymization_rules.update(extra_anonymization_rules)

        for path in output_dicom_path:
            if not (os.path.isdir(path)):
                logger.info(f'Output folder does not exist, creating {path}')
                os.mkdir(path)

        sub_folders = glob(f"{input_dicom_path}/*/")
        if sub_folders:
            for sub_folder in sub_folders:
                output_subfolder_name = os.path.basename(sub_folder[:-1])
                new_output_folder_name = output_dicom_path
                if (output_subfolder_name in name_anonymization_dict.keys()):
                    file_record_name=0
                    output_subfolder_name = name_anonymization_dict [os.path.basename(sub_folder[:-1]) ]
                    anonymized_patient_name = output_subfolder_name
                    # logger.debug(f'found match in sanonymzation table : new name = {anonymized_patient_name}, old name was : {os.path.basename(sub_folder[:-1])} ')
                    new_output_folder_name = [os.path.join(path,output_subfolder_name) for path in output_dicom_path]
                if anonymized_patient_name is None :
                    new_output_folder_name = [os.path.join(path,output_subfolder_name) for path in output_dicom_path]
                file_record_name = anonymize_recursively(sub_folder, new_output_folder_name, extra_anonymization_rules, name_anonymization_dict, anonymized_patient_name,folder_min_size,file_record_name)

        dcms_in_folder = list(filter(lambda x : os.path.isfile(os.path.join(input_dicom_path,x)) and pydicom.misc.is_dicom(os.path.join(input_dicom_path,x)) and ('DICOMDIR' not in x), os.listdir(input_dicom_path)))
        if len(dcms_in_folder)>folder_min_size:
            if file_record_name is None:
                file_record_name = 1
            for sub_doc in dcms_in_folder:
                Thread(target = anonymize_dcm_file, args =(os.path.join(input_dicom_path,sub_doc),[os.path.join(path,"MR"+str(file_record_name).zfill(6)) for path in output_dicom_path],anonymization_rules,anonymized_patient_name)).start()            
                file_record_name += 1
        else :
            logger.info(f'Folder {input_dicom_path} contains too few files (<{folder_min_size}), ignoring it as it is likely screenshots or contains no meaningful acquisition')
        return file_record_name
    
    def anonymize_name(dataset,tag,new_name):
        element = dataset.get(tag)
        if element is not None:
            element.value = new_name

    def keep_only_year(dataset, tag):
        element = dataset.get(tag)
        if element is not None:
            element.value = element.value[:4]+'0101'

    def change_year(dataset, tag):
        element = dataset.get(tag)
        if element is not None:
            element.value = '20210101'    

    corr_dict = {
        'delete' : dicomanonymizer.delete,
        'keep' : dicomanonymizer.keep,
        'keep_year' : keep_only_year,
        'change_year' : change_year,
        'empty': dicomanonymizer.empty,
        'replace':dicomanonymizer.replace,
        'anonymize_name':anonymize_name,
                }

    # Par défault on supprime tout
    anonymization_rules = {}
            
    logger.info("Reading extra rules.\n")
    #TODO : changer pour ne pas lire le header ici aussi
    try :
        extra_rules = {}
        with open('extra_rules.txt', 'r') as file:
            for i in file.readlines():
                j = i.split(";")
                k = j[0].split(',')
                extra_rules[int(k[0][1:]),int(k[1][:-1])] = j[1].rstrip('\n')
        logger.info(str(extra_rules))

        for key, val in extra_rules.items():
            anonymization_rules[key] = corr_dict[val]
    except FileNotFoundError:
        logger.warning("No extra_rules.txt file found")
        pass
    except Exception as e:
        logger.error(f"Exception occured : {e}")
        sys.exit()


    logger.info('Reading name correspondences.\n')
    name_anonymization_dict = {}
    try :
        with open('corr_names.txt', 'r') as file:
            file.readline()
            for i in file.readlines():
                j = i.split(",")
                name_anonymization_dict[j[0].rstrip(' ').lstrip(' ')] = j[1].rstrip('\n').rstrip(' ').lstrip(' ')
        logger.info(str(name_anonymization_dict))
    except FileNotFoundError:
        pass

    logger.info("Starting anonymization")
    for input_path in input_dicom_path:
        base_dir = os.path.basename(input_path)
        if base_dir in name_anonymization_dict.keys():
            base_dir = name_anonymization_dict[base_dir]
        output_path = [os.path.join(path, base_dir) for path in output_dicom_path]
        anonymize_recursively(input_path, output_path, anonymization_rules, name_anonymization_dict)
    logger.info("Anonymisation done")
    input("Press any key to exit.")
except Exception as e:
    logger.error(e)
    print(e)
    print(traceback.format_exc())
    logger.error(traceback.format_exc())
finally :
    input("Process done, press any key to exit.")
    sys.exit()
