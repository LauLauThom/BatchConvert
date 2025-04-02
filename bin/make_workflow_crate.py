"""
Module to create a WF (run) crate for a run of the BatchConvert tool i.e a conversion.
"""
import rocrate
#print(rocrate.__path__)

from rocrate.rocrate import ROCrate
from rocrate.model   import ComputerLanguage
from rocrate.model.entity import Entity
from rocrate.model.person import Person
from rocrate.model.contextentity import ContextEntity
from typing import Literal, Optional, cast


def createFormalParameter(crate : ROCrate,
                          id: str, 
                          additionalType : Literal["Text", "Boolean", "Integer", "Dataset", "File"], 
                          name:str, 
                          description : Optional[str] = None,
                          valueRequired = False) -> ContextEntity:
    """
    Create a FormalParameter to describe an input or output of a workflow.  
    The FormalParameter is created in the crate as a separate entity, and returned by the function.  
    The caller should then associate the returned FormalParameter entity to the workflow of interest. 
    """
    properties = {"@type": "FormalParameter",
                  "additionalType" : additionalType,
                  "valueRequired" : valueRequired,
                  "conformsTo": {
                            "@id": "https://bioschemas.org/profiles/FormalParameter/1.0-RELEASE"
                            },
                  "name" : name
                 }
    
    if description:
        properties["description"] = description
    
    return cast(ContextEntity, crate.add(ContextEntity(crate, 
                                                        identifier = id if id.startswith("#") else f"#{id}",
                                                        properties = properties)))


def create_workflow_crate(base_directory : str) -> ROCrate:
    """
    Create a Workflow RO crate representing the BatchConvert implementation.  
    It describes the entry point executable (batchconvert), the nextflow conversion workflow(s) and some parameters that can be passed to the batchconvert command.  
    
    The function DOES NOT return a Run Crate. A run crate can be created only once a conversion was performed with BatchConvert.  
    A run crate can be created by modifying/adding entries to the Workflow crate returned here, such as documenting values taken by parameters originally documented in the WF crate.  
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
    main_wf = cast(Entity, crate.add_workflow("batchconvert", main=True, lang = bash))  # type: ignore

    # Create an input parameter for the conversion format
    # this is the first argument passed to the batchconvert command
    param_format = createFormalParameter(crate,
                                         id = "#conversion_format",
                                         additionalType = "Text",
                                         name = "conversion_format",
                                         valueRequired = True,
                                         description = "Either 'ometiff' or 'omezarr'")
    main_wf["input"] = [param_format]

    
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
    author = crate.add(Person(crate, 
                              identifier="https://orcid.org/0000-0001-9823-0581", 
                              properties={"name" : "Bugra Özdemir"})) # the O with umlaut gets a unicode character code, which is OK in a UI it renders properly
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