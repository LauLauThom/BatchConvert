#!/usr/bin/env bash

# TODO make SCRIPTPATH an environment variable

SCRIPTPATH=$( dirname -- ${BASH_SOURCE[0]}; );

source $SCRIPTPATH/bin/utils.sh
mkdir -p $HOMEPATH

## STEP 1 : create the params.json from the command input
set -f && \
python $SCRIPTPATH/bin/parameterise_conversion.py "$@"; # the output of this script is a .process file with the name of the command to call, and the param.json with the actual parameters

if [[ -f $TEMPPATH/.stderr ]];
  then
    error=$(cat $TEMPPATH/.stderr);
    rm $TEMPPATH/.stderr;
fi;

if [[ ${#error} -gt 0 ]];
  then
    printf "${RED}$error${NORMAL}\n"
    printf "${RED}The batchconvert command is invalid. Please try again.${NORMAL}\n"
    exit
fi

if [[ -f $TEMPPATH/.stdout ]];
  then
    result=$(cat $TEMPPATH/.stdout);
    rm $TEMPPATH/.stdout;
fi;


## STEP 2 : read the .process file, which contains a "command name"
## The command name "converted" is the one triggering the conversion ("convert" would have probably been a better name, since it didnt happen yet)
if [[ -f $TEMPPATH/.process ]];
  then
    process=$(cat $TEMPPATH/.process)
  else
    printf "${RED}The batchconvert command is invalid. Please try again.${NORMAL}\n"
fi

if [[ $result == "inputpatherror" ]];
  then
    printf "${RED}Error: The input path does not exist.\n${NORMAL}"
    exit
elif [[ ${#result} -gt 0 ]];
  then
    if [[ $process == 'parameters_shown' ]];
      then
        printf "${NORMAL}$result${NORMAL}\n"
      else
        printf "${RED}$result${NORMAL}\n"
        exit
    fi
fi

if [[ -f $TEMPPATH/.afterrun ]];
  then
    afterrun=$(cat $TEMPPATH/.afterrun)
  else
    afterrun="nan"
fi


if [[ $process == 'configured_s3' ]];
  then
    printf "${GREEN}Configuration of the default s3 credentials is complete${NORMAL}\n";
elif [[ $process == 'configured_bia' ]];
  then
    printf "${GREEN}Configuration of the default bia credentials is complete${NORMAL}\n";
elif [[ $process == 'configured_slurm' ]];
  then
    printf "${GREEN}Configuration of the default slurm parameters is complete\n${NORMAL}";
elif [[ $process == 'configured_ometiff' ]];
  then
    printf "${GREEN}Configuration of the default parameters for 'bfconvert' is complete\n${NORMAL}";
elif [[ $process == 'configured_omezarr' ]];
  then
    printf "${GREEN}Configuration of the default parameters for 'bioformats2raw' is complete\n${NORMAL}";
elif [[ $process == 'configured_from_json' ]];
  then
    printf "${GREEN}Default parameters have been updated from a json file.\n${NORMAL}";
elif [[ $process == 'resetted' ]];
  then
    printf "${GREEN}Default parameters have been resetted.\n${NORMAL}";
elif [[ $process == 'parameters_shown' ]];
  then
    printf "${GREEN}Current default parameters displayed.\n${NORMAL}";
elif [[ $process == 'parameters_exported' ]];
  then
    printf "${GREEN}Current default parameters successfully exported.\n${NORMAL}";
elif [[ $process == "default_param_set" ]];
  then
    printf "${GREEN}Default parameter updated.\n${NORMAL}";
elif [[ $process == 'converted' ]];
  then
    printf "${GREEN}Nextflow script has been created. Workflow is beginning.\n${NORMAL}" && \
    chmod +x $BINPATH/run_conversion.py && \
    python $SCRIPTPATH/bin/run_nextflow_cli.py # where the nextflow workflows are actually started. The file run_conversion.py is made executable, and is called from within the nextflow wflows
fi

# delete the .process file
if [[ -f $TEMPPATH/.process ]];
  then
    rm $TEMPPATH/.process
fi

if [[ $1 == "ometiff" ]] || [[ $1 == "omezarr" ]];
  then
    if [[ $afterrun != "noclean" ]];
      then
        python $SCRIPTPATH/bin/clean_workdir.py;
    fi
fi

if [[ -f $TEMPPATH/.afterrun ]];
  then
  rm $TEMPPATH/.afterrun
fi

if [[ -d $TEMPPATH/.nextflow ]];
  then
  rm -rf $TEMPPATH/.nextflow
fi

python $SCRIPTPATH/bin/cleanup.py &> /dev/null







