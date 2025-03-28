#!/bin/bash

set -eu
tempdir=$PREFIX/share/${PKG_NAME}-${PKG_VERSION};
mkdir -p $tempdir;
cp -r $SRC_DIR/* $tempdir;
chmod -R 777 $tempdir

echo "#!/usr/bin/env bash" > $PREFIX/bin/batchconvert; 
echo 'SCRIPTPATH=$( dirname -- ${BASH_SOURCE[0]}; );' >> $PREFIX/bin/batchconvert; 
part1="\$SCRIPTPATH/../share/${PKG_NAME}-${PKG_VERSION}/batchconvert.sh"
part2=$'\x22$@\x22';
script=$part1' '$part2
echo $script >> $PREFIX/bin/batchconvert;
chmod +x $PREFIX/bin/batchconvert
chmod -R 777 $PREFIX/share/${PKG_NAME}-${PKG_VERSION}