#!/usr/bin/env bash

# TODO make SCRIPTPATH an environment variable

SCRIPTPATH=$( dirname -- ${BASH_SOURCE[0]}; );
source $SCRIPTPATH/bin/utils.sh

set -f && \
result=$(pythonexe $SCRIPTPATH/bin/parameterise_conversion.py "$@";)

if [[ $result == "inputpatherror" ]];
  then
    printf "${RED}Error: The input path does not exist.\n${BLACK}"
    exit
elif [[ ${#result} > 0 ]];
  then
    printf "$result\n"
    exit
fi

if [[ -f $SCRIPTPATH/bin/.process ]];
  then
    process=$(cat $SCRIPTPATH/bin/.process)
  else
    printf "${RED}The batchonvert command is invalid. Please try again.${BLACK}\n"
fi

if [[ -f $SCRIPTPATH/bin/.afterrun ]];
  then
    afterrun=$(cat $SCRIPTPATH/bin/.afterrun)
  else
    afterrun="nan"
fi

if [[ $process == 'configured_s3' ]];
  then
    printf "${GREEN}Configuration of the default s3 credentials is complete${BLACK}\n";
elif [[ $process == 'configured_bia' ]];
  then
    printf "${GREEN}Configuration of the default bia credentials is complete${BLACK}\n";
elif [[ $process == 'configured_slurm' ]];
  then
    printf "${GREEN}Configuration of the default slurm parameters is complete\n${BLACK}";
elif [[ $process == 'configured_ometiff' ]];
  then
    printf "${GREEN}Configuration of the default parameters for 'bfconvert' is complete\n${BLACK}";
elif [[ $process == 'configured_omezarr' ]];
  then
    printf "${GREEN}Configuration of the default parameters for 'bioformats2raw' is complete\n${BLACK}";
elif [[ $process == 'configured_from_json' ]];
  then
    printf "${GREEN}Default parameters have been updated from a json file.\n${BLACK}";
elif [[ $process == 'resetted' ]];
  then
    printf "${GREEN}Default parameters have been resetted.\n${BLACK}";
elif [[ $process == 'parameters_shown' ]];
  then
    printf "${GREEN}Current default parameters displayed.\n${BLACK}";
elif [[ $process == 'parameters_exported' ]];
  then
    printf "${GREEN}Current default parameters successfully exported.\n${BLACK}";
elif [[ $process == "default_param_set" ]];
  then
    printf "${GREEN}Default parameter updated.\n${BLACK}";
elif [[ $process == 'converted' ]];
  then
    cd $SCRIPTPATH/bin && \

    pythonexe construct_cli.py > batchconvert_cli.sh && \
    pythonexe construct_nextflow_cli.py > nextflow_cli.sh && \
    printf "${GREEN}Nextflow script has been created. Workflow is beginning.\n${BLACK}"
    cd - && \

    $SCRIPTPATH/bin/nextflow_cli.sh
fi

if [[ -f $SCRIPTPATH/bin/.process ]];
  then
    rm $SCRIPTPATH/bin/.process
fi

if [[ $1 == "ometiff" ]] || [[ $1 == "omezarr" ]];
  then
    if [[ $afterrun != "noclean" ]];
      then
        # echo $afterrun
        pythonexe $SCRIPTPATH/bin/clean_workdir.py;
    fi
fi

if [[ -f $SCRIPTPATH/bin/.afterrun ]];
  then
  rm $SCRIPTPATH/bin/.afterrun
fi

pythonexe $SCRIPTPATH/bin/cleanup.py &> /dev/null



# this runs the nextflow workflow which will consume the updated command line in the bin:





