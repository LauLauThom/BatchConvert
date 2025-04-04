import os, json, subprocess, sys
from subprocess import PIPE
import shutil
from make_workflow_crate import write_workflow_run_crate

if __name__ == "__main__":
    """First script called by batchconvert.sh"""
    scriptpath = os.path.dirname(os.path.realpath(__file__))
    # Recover the env variable defined by the first bash script
    homepath = os.environ.get('HOMEPATH')
    temppath = os.environ.get('TEMPPATH')
    parampath = os.environ.get('PARAMPATH')
    binpath = os.environ.get('BINPATH')
    configpath = os.environ.get('CONFIGPATH')
    paramsource = os.path.join(scriptpath, '..', 'params')
    paramfnames = os.listdir(paramsource)
    paramfpaths = [os.path.join(paramsource, item) for item in paramfnames]
    configsource = os.path.join(scriptpath, '..', 'configs')
    configfnames = os.listdir(configsource)
    configfpaths = [os.path.join(configsource, item) for item in configfnames]

    if not os.path.exists(parampath):
        os.makedirs(parampath)
    if not os.path.exists(temppath):
        os.makedirs(temppath)
    if not os.path.exists(homepath):
        os.makedirs(homepath)
    if not os.path.exists(binpath):
        os.makedirs(binpath)
    if not os.path.exists(configpath):
        os.makedirs(configpath)

    for fpath, fname in zip(paramfpaths, paramfnames):
        destpath = os.path.join(parampath, fname)
        if not os.path.exists(destpath):
            shutil.copy(fpath, destpath)

    for fpath, fname in zip(configfpaths, configfnames):
        destpath = os.path.join(configpath, fname)
        if not os.path.exists(destpath):
            shutil.copy(fpath, destpath)

    # Transfer the conversion script to the execution folder:
    shutil.copy(f"{scriptpath}/run_conversion.py", f"{binpath}/run_conversion.py")

    """
    # Recover the command line args (without the first one, which is the script name)
    args = sys.argv[1:]

    # Check if the ro-crate flag is passed in the command line
    PROV_FLAG = "--prov"

    make_workflowrun_crate = False
    
    if PROV_FLAG in args :
        args.remove(PROV_FLAG)
        make_workflowrun_crate = True
    """
    # Here call the batchconvert.py in the bin directory
    cmd = [os.path.join(scriptpath, "batchconvert"), *sys.argv[1:]] # Here sys.argv has the set of kwargs passed to the batchconvert util in the command line
    interactive_commands = ['configure_s3_remote', 'configure_ometiff', 'configure_omezarr', 'configure_slurm']
    
    if len(cmd) == 2 and cmd[1] in interactive_commands: # ex : batchconvert configure_omezarr, except here batchconvert refer to batchconvert.py
        proc = subprocess.Popen(cmd, universal_newlines=True)
        _ = proc.communicate()
    
    else:
        # actually a conversion task, still calls batchconvert.py
        proc = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        out, error = proc.communicate()
        if len(error) == 0:
            
            with open(os.path.join(temppath, '.stdout'), 'w') as writer: # type: ignore
                writer.write(out)
            
            """
            # Here write the Workflow Run RO crate
            # expect here the last 2 params to be the input and output directories
            # TODO wrong, change this, here is only the end of the batchconvert.py, not of the conversion !
            if make_workflowrun_crate :
                input_dir, output_dir = args[-2:]
                write_workflow_run_crate(batch_convert_repo_dir = os.path.dirname(scriptpath), # scriptpath is the bin directory, we want the root instead
                                         dest_dir = output_dir,
                                         src_dir = input_dir)
            """
            
        else:
            with open(os.path.join(temppath, '.stderr'), 'w') as writer:
                writer.write(error)


