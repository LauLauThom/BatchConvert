#!/usr/bin/env nflow
nextflow.enable.dsl=2

// Note that you can move the parameterise python scripts as a beforeScript directive

process createPatternFile {
    input:
        path inpath
    output:
        path "${inpath}/new.pattern", optional: true
        path "${inpath}/tempdir/new.pattern", optional: true
    script:
    """
    create_hyperstack --concatenation_order ${params.concatenation_order} ${inpath}
    """
}

process bfconvert {
    if ("${params.dest_type}"=="local") {
        publishDir(
            path: "${params.out_path}",
            mode: 'copy'
        )
    }
    input:
        path inpath
    output:
        path "${inpath.baseName}.ome.tiff", emit: conv

    script:
    template 'makedirs.sh "${params.out_path}"'
    """
    batchconvert_cli.sh $inpath "${inpath.baseName}.ome.tiff"
    """
}

process bfconvert_fromPattern {
    if ("${params.dest_type}"=="local") {
        publishDir(
            path: "${params.out_path}",
            mode: 'copy'
        )
    }
    input:
        path inpath
    output:
        path "${inpath.baseName}.ome.tiff", emit: conv
    script:
    template 'makedirs.sh "${params.out_path}"'
    """
    create_hyperstack --concatenation_order ${params.concatenation_order} ${inpath}
    if [[ "${params.concatenation_order}" == "infer_from_filenames" ]];
        then
            batchconvert_cli.sh $inpath/new.pattern "${inpath.baseName}.ome.tiff"
    elif ! [[ "${params.concatenation_order}" == "infer_from_filenames" ]];
        then
            batchconvert_cli.sh $inpath/tempdir/new.pattern "${inpath.baseName}.ome.tiff"
    fi
    rm -rf "${inpath}/tempdir" &> /dev/null
    rm -rf "${inpath}/new.pattern" &> /dev/null
    """
}

process bioformats2raw {
    if ("${params.dest_type}"=="local") {
        publishDir(
            path: "${params.out_path}",
            mode: 'copy'
        )
    }
    input:
        path inpath
    output:
        path "${inpath.baseName}.ome.zarr", emit: conv
    script:
    template 'makedirs.sh "${params.out_path}"'
    """
    batchconvert_cli.sh $inpath "${inpath.baseName}.ome.zarr"
    """
}

process bioformats2raw_fromPattern {
    if ("${params.dest_type}"=="local") {
        publishDir(
            path: "${params.out_path}",
            mode: 'copy'
        )
    }
    input:
        path inpath
    output:
        path "${inpath.baseName}.ome.zarr", emit: conv
    script:
    template 'makedirs.sh "${params.out_path}"'
    """
    create_hyperstack --concatenation_order ${params.concatenation_order} ${inpath}
    if [[ "${params.concatenation_order}" == "infer_from_filenames" ]];
        then
            batchconvert_cli.sh $inpath/new.pattern "${inpath.baseName}.ome.zarr"
    elif ! [[ "${params.concatenation_order}" == "infer_from_filenames" ]];
        then
            batchconvert_cli.sh $inpath/tempdir/new.pattern "${inpath.baseName}.ome.zarr"
    fi
    rm -rf "${inpath}/tempdir" &> /dev/null
    rm -rf "${inpath}/new.pattern" &> /dev/null
    """
}

process mirror2s3 {
    input:
        path local
    output:
        path "./transfer_report.txt", emit: tfr
    script:
    """
    localname="\$(basename $local)" && \
    mc alias set "${params.S3REMOTE}" "${params.S3ENDPOINT}" "${params.S3ACCESS}" "${params.S3SECRET}";
    if [ -f $local ];then
        mc cp $local "${params.S3REMOTE}"/"${params.S3BUCKET}"/"${params.out_path}"/"\$localname";
    elif [ -d $local ];then
        mc mirror $local "${params.S3REMOTE}"/"${params.S3BUCKET}"/"${params.out_path}"/"\$localname";
    fi
    echo "${params.S3REMOTE}"/"${params.S3BUCKET}"/"${params.out_path}"/$local > "./transfer_report.txt";
    """
}

process mirror2local {
    input:
        val source
    output:
        path "transferred"
    script:
    """
    mc alias set "${params.S3REMOTE}" "${params.S3ENDPOINT}" "${params.S3ACCESS}" "${params.S3SECRET}";
    mc mirror "${params.S3REMOTE}"/"${params.S3BUCKET}"/"${source}" "transferred";
    """
}

process mirror2loc {
    input:
        val source
    output:
        path "transferred/${source}"
    script:
    """
    mc alias set "${params.S3REMOTE}" "${params.S3ENDPOINT}" "${params.S3ACCESS}" "${params.S3SECRET}";
    mc mirror "${params.S3REMOTE}"/"${params.S3BUCKET}"/"${source}" "transferred/${source}";
    """
}

process stageLocal {
    input:
        path filepath
    output:
        path "${filepath.baseName}"
    """
    """
}

process stageLocalPublish {
    if ("${params.dest_type}"=="local") {
        publishDir(
            path: "${params.out_path}",
            mode: 'copy'
        )
    }
    input:
        path filepath
    output:
        path "${filepath.baseName}"
    """
    """
}

process mirror2bia {
    input:
        path local
    output:
        path "./transfer_report.txt", emit: tfr
    script:
    """
    ascp -P33001 -l 500M -k 2 -i $BIA_SSH_KEY -d $local bsaspera_w@hx-fasp-1.ebi.ac.uk:${params.BIA_REMOTE}/${params.out_path};
    echo "${params.BIA_REMOTE}"/"${params.out_path}" > "./transfer_report.txt";
    """
}

process mirror_bia2local {
    input:
        val source
    output:
        path transferred
    script:
    // source un basename ini ascp nin output kismina yerlestir
    """
    ascp -P33001 -l 500M -k 2 -i $BIA_SSH_KEY -d bsaspera_w@hx-fasp-1.ebi.ac.uk:${params.BIA_REMOTE}/$source transferred;
    """
}






// EXPERIMENTAL PROCESSES

process cleanup {
    input:
        path inpath
    script:
    """
    rm -rf "${inpath}/tempdir" &> /dev/null
    """
}

process bioformats2raw_experimental {
    if ("${params.dest_type}"=="local") {
        publishDir(
            path: "${params.out_path}",
            mode: 'copy'
        )
    }
    input:
        path inpath
    output:
        path "${inpath.baseName}.ome.zarr", emit: conv
    script:
    template 'makedirs.sh "${params.out_path}"'
    """
    if [[ "${params.merge_files}" == "True" ]];
        then
            create_hyperstack --concatenation_order ${params.concatenation_order} ${inpath};
            if [[ "${params.concatenation_order}" == "infer_from_filenames" ]];
                then
                    batchconvert_cli.sh $inpath/new.pattern "${inpath.baseName}.ome.zarr"
            elif ! [[ "${params.concatenation_order}" == "infer_from_filenames" ]];
                then
                    batchconvert_cli.sh $inpath/tempdir/new.pattern "${inpath.baseName}.ome.zarr"
            fi
    elif [[ "${params.merge_files}" == "False" ]];
        then
            batchconvert_cli.sh $inpath "${inpath.baseName}.ome.zarr"
    fi
    rm -rf "${inpath}/tempdir" &> /dev/null
    rm -rf "${inpath}/new.pattern" &> /dev/null
    """
}
