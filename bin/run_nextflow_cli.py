#!/usr/bin/env python
import subprocess
import argparse
import os, sys, argparse, glob, shutil, json
from pathlib import Path
from wfrun_rocrate import write_workflow_run_crate

# def makelinks(inpath,
#               outpath,
#               contains = None,
#               ignores = None
#               ):
#     if isinstance(inpath, Path):
#         inpath = inpath.as_posix()
#     if isinstance(outpath, Path):
#         outpath = outpath.as_posix()
#     if '**' in inpath:
#         paths = glob.glob(inpath, recursive = True)
#     elif '*' in inpath:
#         paths = glob.glob(inpath)
#     else:
#         paths = glob.glob(os.path.join(inpath, '*'))
#
#     if os.path.exists(outpath):
#         shutil.rmtree(outpath)
#     os.makedirs(outpath)
#
#     for path in paths:
#         if os.path.isfile(path):
#             if contains is None and ignores is None:
#                 os.symlink(path, os.path.join(outpath, os.path.basename(path)))
#             elif ignores is not None:
#                 if ignores not in path:
#                     os.symlink(path, os.path.join(outpath, os.path.basename(path)))
#             elif contains is not None:
#                 if contains in path:
#                     os.symlink(path, os.path.join(outpath, os.path.basename(path)))
#
#     return outpath

if __name__ == '__main__':
    scriptpath = os.path.dirname(os.path.realpath(__file__))
    homepath = os.environ.get('HOMEPATH')
    temppath = os.environ.get('TEMPPATH')
    parampath = os.environ.get('PARAMPATH')
    configpath = os.environ.get('CONFIGPATH')
    defparamfile = os.path.join(parampath, 'params.json.default')
    backupparamfile = os.path.join(parampath, 'params.json.backup')
    paramfile = os.path.join(parampath, 'params.json') # load the file with the args passed to the cmd line
    configfile = os.path.join(configpath, 'bftools.config')

    if not os.path.exists(parampath):
        os.makedirs(parampath)
    if not os.path.exists(configpath):
        os.makedirs(configpath)
    if not os.path.exists(temppath):
        os.makedirs(temppath)
    if not os.path.exists(homepath):
        os.makedirs(homepath)

    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    with open(paramfile, 'rt') as f:
        t_args = argparse.Namespace()
        t_args.__dict__.update(json.load(f))
        args = parser.parse_args(namespace = t_args)

    logdir = os.path.join(args.workdir, 'logs/.nextflow.log')

    # Command to call the nextflow conversion workflow
    conversion_command = ["nextflow", "-C", configfile, "-log", logdir, "run"]

    batchconvert_root_dir = os.path.dirname(scriptpath)

    if args.output_type == 'ometiff':
        conversion_command.append(os.path.join(batchconvert_root_dir, "pff2ometiff.nf"))
    
    elif args.output_type == 'omezarr':
        conversion_command.append(os.path.join(batchconvert_root_dir, "pff2omezarr.nf"))
    
    # add file with parameter values and the execution profile
    conversion_command += [f"-params-file", paramfile, "-profile", args.profile]
    
    # Change running directory
    curpath = os.getcwd()
    os.chdir(temppath)

    # Start the conversion workflow
    subprocess.run(conversion_command, check = True, shell = False)
    
    # Call the nextflow clean after running the wf
    subprocess.run(["nextflow", "clean", "but", "none", "-n", "-f"], 
                   check = True, 
                   shell = False)
    
    # Reset current directory to the one before running the nextflow
    os.chdir(curpath)

    # Create a run crate if the flag is set
    if args.prov == "True": # The boolean value are not properly encoded in the params.json so they are returned as string
        crate = write_workflow_run_crate(batch_convert_repo_dir = batchconvert_root_dir,
                                         param_dir = parampath) # type: ignore

        # get the conversion wf entity to be able to reference it
        #conversion_wf_entity = crate.get(conversion_wf_name)
        




