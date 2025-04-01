"""
Module to create a WF (run) crate for a run of the BatchConvert tool i.e a conversion.
"""
import rocrate
#print(rocrate.__path__)

from rocrate.rocrate import ROCrate
from rocrate.model   import ComputerLanguage
from rocrate.model.person import Person

def create_workflow_crate(base_directory : str) -> ROCrate:
    """
    Create a workflow crate.
    """
    # Create a crate for the given directory
    # Files and folder will be added manually
    crate = ROCrate(source = base_directory)

    # crate.add_workflow("batchconvert", main=True, lang = "shell") # throws an error, currently lang has to be one of "cwl", "galaxy", "knime", "nextflow", "snakemake", "compss", "autosubmit"
    # However one can also pass a ComputerLanguage object to lang, see https://github.com/ResearchObject/ro-crate-py/issues/218#issuecomment-2753694857
    bash_url = "https://www.gnu.org/software/bash/"
    bash = ComputerLanguage(crate, identifier="#bash", properties = {"name" : "Bash",
                                                                    "identifier": {"@id": bash_url},
                                                                    "url": {"@id": bash_url}
                                                                    })
    crate.add(bash) # need to add the item first then reference it
    main_wf = crate.add_workflow("batchconvert", main=True, lang = bash) # type: ignore

    # Try adding the subworkflows has part of the WF crate
    # For a run, one could omit the one not used, or only mention the one used via a createAction
    # Same process, create the entities and add them to the crate (done in one go by add_workflow here), then link them to the main wf
    workflow_tiff = crate.add_workflow(source = "pff2ometiff.nf", 
                                       main = False,
                                       lang = "nextflow")

    workflow_zarr = crate.add_workflow(source = "pff2omezarr.nf", 
                                       main = False,
                                       lang = "nextflow")

    # Add description to the secondary workflow
    desc_template = "Nextflow workflow executed when passing the argument (i.e converting to) '{}' as first argument to the BatchConvert utility."
    workflow_tiff["description"] = desc_template.format("ometiff") # type: ignore
    workflow_zarr["description"] = desc_template.format("omezarr") # type: ignore

    main_wf["hasPart"] = [workflow_tiff, workflow_zarr]  # type: ignore

    # Add the authors and institution potentially
    # works but not added as author of the workflow
    # TODO add more authors
    author = crate.add(Person(crate, identifier="https://orcid.org/0000-0001-9823-0581", properties={"Name" : "Bugra Özdemir"})) # the O with umlaut gets a unicode character code, which is OK in a UI it renders properly
    #crate["Authors"] = author # nope

    # Add the authors at the root of the dataset entity as expected by workflow hub
    """
    for e in crate.get_entities():
        
        if e.id == "./" :
            root_dataset_entity = e
            break

    else: # for/else : hit if the for loop does not break
        raise Exception("Could not find root Dataset entity")
    """
    crate.root_dataset["author"] = [author]

    # Save the crate in a new subdirectory, all files and directories listed in the json will get copied to the subdirectory
    #crate.write(rocrate_name) # write and write_crate are the same
    #crate.write_crate("my_crate")

    return crate