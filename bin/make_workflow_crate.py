"""
Module to create a WF (run) crate for a run of the BatchConvert tool i.e a conversion.
"""
import os
from pathlib import Path
import shutil, json
import rocrate
#print(rocrate.__path__)

from rocrate.rocrate import ROCrate
from rocrate.model   import ComputerLanguage
from rocrate.model.entity import Entity
from rocrate.model.person import Person
from rocrate.model.contextentity import ContextEntity
from typing import Any, Literal, Optional, cast

get_identifier = lambda id : id if id.startswith("#") else f"#{id}"
"""Get a ROCrate compliant identifier for a given string, i.e should start with #"""

class BatchConvertWorkflowRunCrate(ROCrate):
    """Custom class for the BatchConvertWorkflowRunCrate, adding convenience functions."""
    
    def __init__(self, repo_root_dir : str):
        """Create a workflow crate for BatchConvert, call add_input... to add additional infos about a run."""
        super().__init__()

        # crate.add_workflow("batchconvert", main=True, lang = "shell") # throws an error, currently lang has to be one of "cwl", "galaxy", "knime", "nextflow", "snakemake", "compss", "autosubmit"
        # However one can also pass a ComputerLanguage object to lang, see https://github.com/ResearchObject/ro-crate-py/issues/218#issuecomment-2753694857
        bash_url = "https://www.gnu.org/software/bash/"
        bash = ComputerLanguage(self, identifier="#bash", properties = {"name" : "Bash",
                                                                        "identifier": {"@id": bash_url},
                                                                        "url": {"@id": bash_url}
                                                                        })
        self.add(bash) # need to add the item first then reference it

        # the wf file will be copied from the source, to the directory where the crate will be saved (using crate.write)
        self.main_wf = cast(Entity, self.add_workflow(source = os.path.join(repo_root_dir, "batchconvert"), 
                                                      main=True, 
                                                      lang = bash))  # type: ignore
        """
        # Create input parameters
        param_format = self.addFormalParameter(id = "#conversion_format",
                                               additionalType = "Text",
                                               name = "conversion_format",
                                               valueRequired = True,
                                               description = "Either 'ometiff' or 'omezarr'")
        
        param_src_dir = self.addFormalParameter(id = "#src_dir",
                                                additionalType = "Text",
                                                name = "src_dir",
                                                valueRequired = True,
                                                description = "Input directory with images to convert.") 
        
        param_dst_dir = self.addFormalParameter(id = "#dest_dir",
                                                additionalType = "Text",
                                                name = "dest_dir",
                                                valueRequired = True,
                                                description = "Output directory with converted images.") 
        
        
        param_merge_files = self.addFormalParameter(id = "#merge_files",
                                                    additionalType = "Boolean",
                                                    name = "merge_files",
                                                    valueRequired = False,
                                                    defaultValue = False,
                                                    description = "Flag --merge_files, if multiple source files should be concatenated into a single ome-tiff/ome-zarr. Can be used together with the concatenation_order parameter to instruct the dimensions, otherwise batchconvert will automatically group datasets (see the doc).")
            
        param_concatenation_order = self.addFormalParameter(id = "#concatenation_order",
                                                            additionalType = "Text",
                                                            name = "concatenation_order",
                                                            valueRequired = False,
                                                            defaultValue = "auto",
                                                            description = "Can be used with the --merge_files flag to pass custom dimensions specifiers.")
                        
        self.main_wf["input"] = [param_format, 
                            param_src_dir,
                            param_dst_dir,
                            param_merge_files, 
                            param_concatenation_order]
        """

        # Adding the subworkflows has part of the WF crate
        # For a run, one could omit the one not used, or only mention the one used via a createAction
        # Same process, create the entities and add them to the crate (done in one go by add_workflow here), then link them to the main wf
        workflow_tiff = self.add_workflow(source = os.path.join(repo_root_dir, "pff2omezarr.nf"),
                                          main = False,
                                          lang = "nextflow")

        workflow_zarr = self.add_workflow(source = os.path.join(repo_root_dir, "pff2ometiff.nf"), 
                                          main = False,
                                          lang = "nextflow")

        # Add description to the secondary workflow
        desc_template = "Nextflow workflow executed when passing the argument (i.e converting to) '{}' as first argument to the BatchConvert utility."
        workflow_tiff["description"] = desc_template.format("ometiff") # type: ignore
        workflow_zarr["description"] = desc_template.format("omezarr") # type: ignore

        self.main_wf["hasPart"] = [workflow_tiff, workflow_zarr]  # type: ignore
        self.main_wf["url"]     = ["https://github.com/Euro-BioImaging/BatchConvert"]

        # Add the authors and institution potentially
        # works but not added as author of the workflow
        # TODO add more authors
        author = self.add(Person(self, 
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
        self.root_dataset["author"] = [author]

        # Create or get the creative work nodes, for the conformsTo at the dataset level (not the ones of the ro-crate-metdata.json entity)
        wf_crate_profile = self.get("https://w3id.org/workflowhub/workflow-ro-crate/1.0")

        if wf_crate_profile is None :
             wf_crate_profile = self.add_jsonld({"@id": "https://w3id.org/workflowhub/workflow-ro-crate/1.0",
                                                 "@type": "CreativeWork",
                                                 "name": "Workflow RO-Crate",
                                                 "version": "1.0"
                                                })

        process_profile = self.add_jsonld({ "@id": "https://w3id.org/ro/wfrun/process/0.1",
                                            "@type": "CreativeWork",
                                            "name": "Process Run Crate",
                                            "version": "0.1"})

        wfrun_profile = self.add_jsonld({"@id": "https://w3id.org/ro/wfrun/workflow/0.1",
                                         "@type": "CreativeWork",
                                         "name": "Workflow Run Crate",
                                         "version": "0.1"
                                         })
        
        self.root_dataset["conformsTo"] = [process_profile, wfrun_profile, wf_crate_profile]

        # Save the crate in a new subdirectory, all files and directories listed in the json will get copied to the subdirectory
        #crate.write(rocrate_name) # write and write_crate are the same
        #crate.write_crate("my_crate")

    def addFormalParameter(self,
                           id: str, 
                           additionalType : Literal["Text", "Boolean", "Integer", "Dataset", "File"], 
                           name:str, 
                           description : Optional[str] = None,
                           valueRequired = False,
                           defaultValue = None) -> ContextEntity:
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

        if defaultValue:
            properties["defaultValue"] = defaultValue

        return cast(ContextEntity, self.add(ContextEntity(self, 
                                                          identifier = get_identifier(id),
                                                          properties = properties)))
    
    def add_PropertyValue(self, value, param_entity : ContextEntity) -> ContextEntity:
        """
        Create a PropertyValue entity with the value taken by a paran_entity during a run.
        The PropertyValue will have the same id than the param entity with suffix "/value".  
        The field name is however the same than the FormalParameter.  
        """
        properties = {"@type" : "PropertyValue",
                      "name"  : param_entity["name"],
                      "value" : value
                      }
                    
        propertyValueEntity = cast(ContextEntity, self.add(ContextEntity(self,
                                                                        identifier = f"{param_entity.id}/value",
                                                                        properties = properties)))
        propertyValueEntity["exampleOfWork"] = param_entity

        return propertyValueEntity
    
    def add_input_and_value_entities(self, input_key : str, input_value) :
        """
        Create a FormalParameter and associated value entity for a pair of input:value.  
        """
        # mapping python type to the rocrate equivalent
        pytype_to_rotype = {int:"Integer", 
                            str:"Text",
                            bool:"Boolean",
                            }
        try:
            formal_parameter_type = pytype_to_rotype[type(input_value)]
        except KeyError:
            raise TypeError("input_value should be an int, str or bool.")

        param_entity = self.addFormalParameter(id = input_key,
                                               additionalType = formal_parameter_type, # type: ignore
                                               name = input_key,
                                               valueRequired = input_key in ("in_path", "out_path"),
                                               )
        self.main_wf.append_to("input", param_entity)
        
        _ = self.add_PropertyValue(input_value, param_entity=param_entity)

    def find_and_add_custom_param_values(self, param_dir_path:str):
        """
        After a run of BatchConvert, parse the file params.json and params.json.default normally in home/.batchConvert/params, to find out which parameters differ from the default, i.e were passed to the batchconvert command line utils.  
        It's true that some extra parameters can have been passed to the command line, with the same value than in the params.json.default, but in this case the result is the same than omitting them.  
        There is not much simpler way to recover these "custom" values, having always a consistent parameter naming.  
        """

        # first actual parameters used
        with open(os.path.join(param_dir_path, "params.json")) as param_file:
            params : dict[str, Any] = json.load(param_file)

        # then default parameters
        with open(os.path.join(param_dir_path, "params.json.default")) as default_param_file:
            default_params : dict[str, Any] = json.load(default_param_file)

        # Loop over the entries of the param dict, checking if differing from default
        for key, value in params.items():
            
            if key in default_params:
                
                default_value = default_params[key]
                
                if value != default_value:
                    self.add_input_and_value_entities(input_key = key,
                                                      input_value = value)
                #else value is default, nothing to do
            
            else : # if the key is not even in the default parameters then also add it
                self.add_input_and_value_entities(input_key = key,
                                                  input_value = value)
    
    def add_output_dataset(self, output_image_dir : str|Path):
        """
        Add a dataset entry to the RO crate with the converted images.
        Before calling this function, best is to move the images from the output directory of batchconvert to a new subdirectory e.g "images".  
        Then passing this subdirectory to this function, and writing the RO crate to this output directory.  
        """
        self.add_directory(output_image_dir, properties = {"name":"converted_images"})


def create_workflow_crate(repo_root_dir:str) -> BatchConvertWorkflowRunCrate:
    """
    Create a Workflow RO crate representing the BatchConvert implementation.  
    It describes the entry point executable (batchconvert), the nextflow conversion workflow(s) and some parameters that can be passed to the batchconvert command.  
    
    The function DOES NOT return a Run Crate. A run crate can be created only once a conversion was performed with BatchConvert.  
    A run crate can be created by modifying/adding entries to the Workflow crate returned here, such as documenting values taken by parameters originally documented in the WF crate.  

    repo_root_dir
    -------------
    Directory where the batchconvert, nextflow and other script files are.  

    converted_image_directory
    --------
    Directory for the root entity of the crate.  
    Elements added to the crate will have their identifier (path) relative to this root.  
    """
    return BatchConvertWorkflowRunCrate(repo_root_dir)

def extend_as_runcrate(crate:BatchConvertWorkflowRunCrate, image_output_dir:str|Path, input_directory:Optional[str|Path] = None) -> BatchConvertWorkflowRunCrate:
    """
    Add entries to a BatchConvert Workflow Crate, following a conversion with BatchConvert.  
    Returns a Workflow Run Crate documenting the conversion and the resutling dataset.  
    Before calling this function, best is to move the images from the output directory of batchconvert to a new subdirectory e.g "images". 
    Then passing this subdirectory to this function, and writing the RO crate to the parent output directory.   
    """
    crate.add_output_dataset(output_image_dir = image_output_dir)
    return crate

def move_content_to_subdir(base_directory:str, subdirectory_name = "converted_images") -> Path:
    """
    Move all the content of a directory to a subdirectory, create it if not existing.  
    Return the path to the subdirectory.
    """
    dest_dir_path = Path(base_directory)
    
    subdir = dest_dir_path.joinpath(subdirectory_name)

    # Create the directory otherwise create a weird image file and the files are lost
    if not subdir.exists():
        subdir.mkdir(parents = True) # recursive i.e create parents if needed
    
    for file in dest_dir_path.iterdir():
        shutil.move(file, subdir)
    
    return subdir

def write_workflow_run_crate(batch_convert_repo_dir:str, dest_dir:str, param_dir:str, src_dir:Optional[str] = None) :
    """
    After converting a dataset with batch_convert, call this function to turn the dest_dir into a Workflow Run ROCrate.  
    This function will actually move the converted images to a subdirectory "images" in the dest_dir.  
    It also copies the files batchconvert, batchconvert.sh, pff2ometiff.nf, pff2omezarr.nf to the RO crate too.    
    A ro-crate-metadata.json is written in dest_dir, which in effect makes the directory a RO_crate.  
    TODO add the rest of the files needed for execution
    
    batch_convert_repo_dir
    ---------------------
    path to the root directoy of batchconvert where the batchconvert utility and nextflow files are (e.g pff2ometiff.nf)  

    dest_dir
    --------
    original destination directory for the converted images, as passed to batch convert.  
    The images will be moved to a subdirectory "images" within this directory.  

    src_dir
    -------
    directory of the original images to convert
    """
    crate = create_workflow_crate(batch_convert_repo_dir)
    
    crate.find_and_add_custom_param_values(param_dir_path = param_dir)
    # Move the images to a subdirectory "images"
    #shutil.move(dest_dir, os.path.join(dest_dir, "images")) # error cannot move a directory in itself
    image_dir = move_content_to_subdir(dest_dir, subdirectory_name = "converted_images")
        
    extend_as_runcrate(crate,
                       image_output_dir = image_dir,  # type: ignore
                       )
    
    crate.write(dest_dir)