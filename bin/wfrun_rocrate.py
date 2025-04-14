"""
Module to create a WF (run) crate for a run of the BatchConvert tool i.e a conversion.
"""
import os
from pathlib import Path
import shutil, json
import time
import warnings
import rocrate
#print(rocrate.__path__)

from rocrate.rocrate import ROCrate
from rocrate.model   import ComputerLanguage
from rocrate.model.entity import Entity
from rocrate.model.person import Person
from rocrate.model.contextentity import ContextEntity
from typing import Any, Dict, List, Literal, Optional, cast

get_identifier = lambda id : id if id.startswith("#") else f"#{id}"
"""Get a ROCrate compliant identifier for a given string, i.e should start with #"""

def load_params_json(path:str|Path) -> Dict[str, Any]:
    """Load the param json, casting the bool which were not properly encoded."""

    with open(path) as file:
        content_dict : dict[str, Any] = json.load(file)
    
    for key, value in content_dict.items():

        if value in ("True", "False"): 
            content_dict[key] = eval(value) # replace with an actual boolean
        
    return content_dict


class BatchConvert_RunCrateMaker(object):
    """
    Custom class for the BatchConvertWorkflowRunCrate, adding convenience functions.  
    Dont directly extend a ROCrate, we dont want to give the option to save the crate anywhere, since we also need to move files around.  
    """
    
    def __init__(self, repo_root_dir : str, param_dir:Optional[str] = None, name="", description = "", license = ""):
        """
        Create a workflow run crate after conversion of an image dataset with BatchConvert.  
        This constructor only populates the default infos that do not change, but does not parse the json files with the actual parameter values.   
        
        repo_root_dir
        -------------
        Where the BatchConvert script files are.

        param_dir
        --------
        Directory of the params.json file.  
        If not provided, default to home/.batchconvert/params  

        name
        ----
        Name of the crate  
        Use for the attribute "name" of the root dataset of the crate  
        A default name is created if not provided.

        description
        -----------
        Optional description for the crate.
        By default will be "Conversion of dataset {name} to format {format}" where name is the name of the source directory passed to BatchConvert, and format is the conversion format (ometiff or omezarr).
        """
        
        super().__init__()
        self.crate = ROCrate()

        self.param_dir = Path(param_dir) if param_dir else Path.home().joinpath(".batchconvert") \
                                                                      .joinpath("params")
        
        if not self.param_dir.exists():
            raise FileNotFoundError(self.param_dir)

        # Declare varaibles that should be populated by _parseParams if the params.json file exists in param_dir
        self._conversion_format : Optional[str] # conversion format
        self._src_dir : Optional[str]

        # crate.add_workflow("batchconvert", main=True, lang = "shell") # throws an error, currently lang has to be one of "cwl", "galaxy", "knime", "nextflow", "snakemake", "compss", "autosubmit"
        # However one can also pass a ComputerLanguage object to lang, see https://github.com/ResearchObject/ro-crate-py/issues/218#issuecomment-2753694857
        bash_url = "https://www.gnu.org/software/bash/"
        bash = ComputerLanguage(self.crate, identifier="#bash", properties = {"name" : "Bash",
                                                                              "identifier": {"@id": bash_url},
                                                                              "url": {"@id": bash_url}
                                                                             })
        self.crate.add(bash) # need to add the item first then reference it

        # the wf file will be copied from the source, to the directory where the crate will be saved (using crate.write)
        self.main_wf = cast(Entity, self.crate.add_workflow(source = os.path.join(repo_root_dir, "batchconvert"), 
                                                            main=True, 
                                                            lang = bash))  # type: ignore
        """
        # Create input parameters
        param_format = self.crate.addFormalParameter(id = "#conversion_format",
                                               additionalType = "Text",
                                               name = "conversion_format",
                                               valueRequired = True,
                                               description = "Either 'ometiff' or 'omezarr'")
        
        param_src_dir = self.crate.addFormalParameter(id = "#src_dir",
                                                additionalType = "Text",
                                                name = "src_dir",
                                                valueRequired = True,
                                                description = "Input directory with images to convert.") 
        
        param_dst_dir = self.crate.addFormalParameter(id = "#dest_dir",
                                                additionalType = "Text",
                                                name = "dest_dir",
                                                valueRequired = True,
                                                description = "Output directory with converted images.") 
        
        
        param_merge_files = self.crate.addFormalParameter(id = "#merge_files",
                                                    additionalType = "Boolean",
                                                    name = "merge_files",
                                                    valueRequired = False,
                                                    defaultValue = False,
                                                    description = "Flag --merge_files, if multiple source files should be concatenated into a single ome-tiff/ome-zarr. Can be used together with the concatenation_order parameter to instruct the dimensions, otherwise batchconvert will automatically group datasets (see the doc).")
            
        param_concatenation_order = self.crate.addFormalParameter(id = "#concatenation_order",
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
        workflow_tiff = self.crate.add_workflow(source = os.path.join(repo_root_dir, "pff2omezarr.nf"),
                                                main = False,
                                                lang = "nextflow")

        workflow_zarr = self.crate.add_workflow(source = os.path.join(repo_root_dir, "pff2ometiff.nf"), 
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
        author = self.crate.add(Person(self.crate, 
                                       identifier="https://orcid.org/0000-0001-9823-0581", 
                                       properties={"name" : "Bugra Özdemir"})) # the O with umlaut gets a unicode character code, which is OK in a UI it renders properly
        self.crate.root_dataset["author"] = [author]

        #crate["Authors"] = author # nope

        # Create or get the creative work nodes, for the conformsTo at the dataset level (not the ones of the ro-crate-metdata.json entity)
        wf_crate_profile = self.crate.get("https://w3id.org/workflowhub/workflow-ro-crate/1.0")

        if wf_crate_profile is None :
             wf_crate_profile = self.crate.add_jsonld({"@id": "https://w3id.org/workflowhub/workflow-ro-crate/1.0",
                                                        "@type": "CreativeWork",
                                                        "name": "Workflow RO-Crate",
                                                        "version": "1.0"
                                                        })

        process_profile = self.crate.add_jsonld({ "@id": "https://w3id.org/ro/wfrun/process/0.1",
                                                "@type": "CreativeWork",
                                                "name": "Process Run Crate",
                                                "version": "0.1"})

        wfrun_profile = self.crate.add_jsonld({"@id": "https://w3id.org/ro/wfrun/workflow/0.1",
                                               "@type": "CreativeWork",
                                               "name": "Workflow Run Crate",
                                               "version": "0.1"
                                                })
        
        self.crate.root_dataset["conformsTo"] = [process_profile, wfrun_profile, wf_crate_profile]

        # Add default name and description
        self.name = name
        self.description = description
        self.license = license
        
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

        return cast(ContextEntity, self.crate.add(ContextEntity(self.crate, 
                                                                identifier = get_identifier(id),
                                                                properties = properties)))
    
    def add_PropertyValue(self, value, param_entity : ContextEntity) -> ContextEntity:
        """
        Create a PropertyValue entity with the value taken by a param_entity during a run.
        The PropertyValue will have the same id than the param entity with suffix "/value".  
        The field name is however the same than the FormalParameter.  
        """
        properties = {"@type" : "PropertyValue",
                      "name"  : param_entity["name"],
                      "value" : value
                      }
                    
        propertyValueEntity = cast(ContextEntity, self.crate.add(ContextEntity(self.crate,
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


    def _parse_params_and_reorganize_files(self):
        """
        IMPORTANT : This function can also move the input and/or output directory of images to subdirectories to avoid data-duplication !  

        After a run of BatchConvert, add both the params.json and params.json.default to the crate normally in (home/.batchConvert/params).  
        Also parse those files to try find out which parameters differ from the default, i.e were potentially passed to the batchconvert command line utils.  
        Typically, includes the input and output directory.  
        Some parameters will be listed in the rocrate json although they were not passed to the cmd line i.e they were taking the default value, the result is however the same than omitting them.   
        There is not much simpler way to recover these "custom" values, having always a consistent parameter naming.  
        
        And adds the input and output directory as Dataset in the crate.  
        """
        
        # Params.json
        param_path = self.param_dir.joinpath("params.json")

        if not os.path.exists(param_path):
            raise FileNotFoundError(param_path)
        
        self.crate.add_file(param_path, 
                      dest_path="params/params.json",
                      properties = {"name":"parameters",
                                    "encodingFormat":"text/json"    
                      })
        
        # first actual parameters used
        params = load_params_json(param_path)

        # Create a variable for the input/output directory 
        # used later on when saving the crate
        in_dir  = Path(params["in_path"]) 
        out_dir = Path(params["out_path"])

        # populate the dataset name, just for the crate description
        self._src_dir = in_dir.name

        # Handle the different cases of input/output directory structure
        # because the rpyrocrate package copy the directory referenced in the json, unless they are already in the right place
        # so to avoid duplication we move the data already in the right place

        # Case 1 : input and output are in the same directory
        # then move them to a subdirectory and use the newly created parent as the crate
        # "least astonishment principle" 
        if in_dir.parent == out_dir.parent:
            
            parent = in_dir.parent

            self.crate_dir = parent.joinpath(f"batchconvert_wfrun_rocrate_{time.strftime('%Y_%m_%d_%H%M')}")
            self.crate_dir.mkdir()

            # Move the input and output dir to the crate dir
            image_dir = self.crate_dir.joinpath(in_dir.name)
            shutil.move(in_dir, image_dir) # in dir is the original input directory, its content is then moved to crate/in_dir

            converted_image_dir = self.crate_dir.joinpath(out_dir.name)
            shutil.move(out_dir, converted_image_dir)

        # if the output dir is a subdirectory of the input directory
        # then move the images to a subdirectory of the original input dir 
        # and use the original input dir as the crate
        elif out_dir.is_relative_to(in_dir):
            
            self.crate_dir = in_dir 
            
            # Move the original images to a subdirectory of the input directory
            # Dont move the subdirectyory of the converted images though
            image_dir = move_content_to_subdir(base_directory = in_dir,
                                               subdirectory_name = "images",
                                               exclude = [out_dir])
            
            converted_image_dir = out_dir
        
        # any other case : the input directory is somewhere and the input dir somewhere unrelated, then move the content of the output directory to a subdirectory
        # and use the original output directory as the crate directory
        # TODO if the output directory contains stuff already this content also get moved to the newly created subdirectory, could bew avoided?
        else :
            self.crate_dir = out_dir
            image_dir = in_dir
            
            converted_image_dir = move_content_to_subdir(base_directory = out_dir,
                                                         subdirectory_name = "converted_images")
        
        # Add input directory as datasets
        self.crate.add_directory(source = image_dir,
                           properties = {"name": "original_image_directory",
                                        "description" : "Directory of images to convert"} ) 
        
        # Add output directory
        self.crate.add_directory(source = converted_image_dir,
                           properties = {"name": "converted_image_directory",
                                         "description" : "Directory with converted images"} ) 

        # Default params        
        default_param_path = self.param_dir.joinpath("params.json.default")

        if not os.path.exists(default_param_path):
            warnings.warn(f"Could not find file {default_param_path}")
            return
        
        # Add default param file to crate
        self.crate.add_file(default_param_path, 
                      dest_path="params/params.json.default",
                      properties = {"name":"default_parameters",
                                    "encodingFormat":"text/json"    
                      })
        
        default_params = load_params_json(default_param_path)

        # Loop over the entries of the param dict, checking if differing from default
        for key, value in params.items():
            
            if key == "output_type":
                self._conversion_format = cast(str, value) 
            
            if key in default_params:
                
                default_value = default_params[key]
                
                if value != default_value:
                    self.add_input_and_value_entities(input_key = key,
                                                      input_value = value)
                #else value is default, nothing to do
            
            else : # if the key is not even in the default parameters then also add it
                self.add_input_and_value_entities(input_key = key,
                                                  input_value = value)
    
    def save_crate(self):
        """
        Save the crate to the original output directory passed to the BatchConvert tool.  
        This function will also parse the params file with the parameter values used during the run and move the files around accordingly (to avoid data-duplication).   
        """
        self._parse_params_and_reorganize_files()
        
        # Add name, description and license to root dataset, needed for a valid crate
        if not self.name and self._src_dir:
            self.name = f"BatchConvert wf runcrate - converted directory '{self._src_dir}'"

        if not self.description and self._conversion_format and self._src_dir:
            self.description = f"Worfklow run crate describing conversion of images in directory '{self._src_dir}' to format {self._conversion_format} using BatchConvert"
                
        self.crate.write(self.crate_dir)
    

def move_content_to_subdir(base_directory:str|Path, subdirectory_name = "converted_images", exclude:List[str]|List[Path] = []) -> Path:
    """
    Move all the content of a directory to a subdirectory, create it if not existing.  
    Return the path to the subdirectory.
    """
    if isinstance(base_directory, str):
        base_directory = Path(base_directory)
    
    subdir = base_directory.joinpath(subdirectory_name)

    # Create the directory otherwise create a weird executable file and the files are lost
    if not subdir.exists():
        subdir.mkdir(parents = True) # recursive i.e create parents if needed

    exclude = [Path(path) for path in exclude]

    for file in base_directory.iterdir():
        
        if file in exclude :
            continue

        shutil.move(file, subdir)
    
    return subdir

def write_workflow_run_crate(batch_convert_repo_dir:str, param_dir:str) :
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
    crate_maker = BatchConvert_RunCrateMaker(batch_convert_repo_dir, 
                                        param_dir = param_dir)
    
    crate_maker.save_crate()

if __name__ ==  "__main__" :
    crate_maker = BatchConvert_RunCrateMaker(repo_root_dir="..")