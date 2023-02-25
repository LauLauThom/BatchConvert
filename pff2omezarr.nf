#!/usr/bin/env nfprojects
nextflow.enable.dsl=2
// nextflow.enable.moduleBinaries = true

include { bioformats2raw_fromPattern; bioformats2raw; mirror2s3; mirror2local; mirror2loc; mirror2bia; mirror_bia2local; stageLocal } from "./modules/modules.nf"

// TODO: add an optional remove-workdir parameter and a remove-workdir script to the end of the workflow (in Groovy)

workflow {
    // If the input dataset is in s3, bring it to the execution environment first:
    // Note that this scenario assumes that the input path corresponds to a directory at s3 (not a single file)
    if ( params.source_type == "s3" ) {
        ch0 = Channel.of(params.in_path)
        mirror2loc(ch0)
        ch1 = mirror2loc.out.map { file(it).listFiles() }.flatten()
        ch = ch1.filter { it.toString().contains(params.pattern) }
    }
    else if ( params.source_type == "bia" ) {
        ch0 = Channel.of(params.in_path)
        mirror_bia2local(ch0)
        ch1 = mirror_bia2local.out.map { file(it).listFiles() }.flatten()
        ch2 = ch1.map { file(it).listFiles() }.flatten()
        ch = ch2.filter { it.toString().contains(params.pattern) }
    }
    else if ( params.source_type == "local" ) {
        def fpath = file(params.in_path)
        // Note the above assignment yields either a list of files (with globbing), a single file (if the parameter in_path corresponds to a file path) a directory (if the parameter in_path corresponds to a directory path)
        // Make sure a proper channel is created in any of these cases:
        if  ( fpath instanceof List ){
            ch = Channel.fromPath(params.in_path).filter { it.toString().contains(params.pattern) }
        }
        else if ( fpath.isDirectory() ) {
            ch0 = Channel.of(fpath.listFiles()).flatten()
            ch = ch0.filter { it.toString().contains(params.pattern) }
        }
        else if ( fpath.isFile() ) {
            println fpath
            ch0 = Channel.of(fpath).flatten()
            ch = ch0.filter { it.toString().contains(params.pattern) }
        }
    }
    //Once the channel is created, run the conversion. Conversion is either kept local or transferred to s3 depending on the dest parameter.
    if ( params.source_type == "local" ) {
        if ( params.merge_files == "True" ) {
            output = bioformats2raw_fromPattern(params.in_path)
        }
        else {
            output = bioformats2raw(ch)
        }
    }
    else if ( params.source_type == "s3" ) {
        if ( params.merge_files == "True" ) {
            output = bioformats2raw_fromPattern(mirror2loc.out)
        }
        else {
            output = bioformats2raw(ch)
        }
    }
    if ( params.dest_type == "s3" ) {
        // Note that if the dest_type is s3, the output must be uploaded to the s3 bucket.
        // If dest_type is local, no need to do anything. module will do the publishDir.
        mirror2s3(output)
    }
}