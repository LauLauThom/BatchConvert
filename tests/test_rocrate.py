import sys
from pprint import pprint
from pathlib import Path
from rocrate.rocrate import ROCrate
from rocrate.model.contextentity import ContextEntity

# Add bin to the path to be able to import it
assert  Path.cwd().name == "BatchConvert", "Expected the working directory to be the root of the repo 'BatchConvert'"

sys.path.append("./bin")

# now the import should work
from make_workflow_crate import createFormalParameter # type: ignore

# Create an empty crate
crate = ROCrate()

# Add a FormalParameter entity to the crate
id = "#conversion_format"
additionalType = "Text"
name = "conversion_format"
description = "Either 'ometiff' or 'omezarr'"

formalParam = createFormalParameter(crate,
                                    id = id,
                                    additionalType = additionalType,
                                    name = name,
                                    valueRequired = True,
                                    description = description)

assert isinstance(formalParam, ContextEntity)
assert formalParam.id == id
assert formalParam["additionalType"] == additionalType
assert formalParam["name"] == name
assert formalParam["description"] == description
assert formalParam["valueRequired"] # directly True 

# Check that one can retrieve the formalParameter from the crate
assert crate.get(id) == formalParam

