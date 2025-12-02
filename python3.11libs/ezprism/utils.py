import hou
from pathlib import Path
import PrismInit
from imp import reload

import os

def updateIgnorelist(project=""):
    '''
    Attempts to run the updateIgnorelist bat found at the project root
    To make it easier for users to stay up to date. Must be careful as this can break a project syncing  
    project arg expected to look like "01_Sandbox"  
    '''    
    if project != "":
        temp = "$RVFX_ROOT/{}".format(project)
        temp = hou.text.expandString(temp)
        prismjob = temp
    else:
        # prismjob = Path(hou.getenv("PRISMJOB"))    
        prismjob = Path(hou.text.expandString("$PRISMJOB"))
    # check path exists
    if not Path(prismjob).exists():
        print("ERROR project path does not exist: ", prismjob)
        return
    # ensure posix path
    prismjob = Path(prismjob).as_posix()
    
    import sys
    sys.dont_write_bytecode = True # stop writing pycache
    sys.path.append(str(prismjob))
    print("found script to use inside directory: {}".format(prismjob))
    try:
        #from ignore_script import run            
        import ignore_script
        reload(ignore_script)
        ignore_script.run(str(prismjob))
    except Exception as error:
        print("ERROR trying to update ignoreList:\n", error)
    finally:
        sys.path.remove(str(prismjob))
        sys.dont_write_bytecode = False
                    
def remakePrismjob() -> bool:
    '''
    If remaps returns True, else False
    Methods to find the prismjob variable, and then path remap it for the current worker
    Priority order should be: os.environ, argument, scene

    Note: hou.getenv inconsistently works for $PRISMJOB as its not an environment variable but part of the scene
    must use hou.text.expandString() instead. 
    '''
    print('Entering remake PRISMJOB function')
    rvfx_root = hou.getenv("RVFX_ROOT")    

    # then check argument
    # then resort to hou.getenv

    prism_job = hou.text.expandString("$PRISMJOB") #hou.getenv("PRISMJOB")
    print("First checking values: \n$PRISMJOB = {0} \n$RVFX_ROOT = {1}".format(prism_job, rvfx_root))
    
    if not prism_job:
        print("$PRISMJOB not defined. Checking in os.environ...")
        if 'prism_project' in os.environ:
            print("Found prism_project in os.environ")
            prism_project = Path(os.environ['prism_project'])
            prism_job = prism_project.parent.parent
        else:
            print("Couldn't find prism_project in os.environ")
            # likely we are in a manually submitted deadline job
            # last resort to find prismjob from the arguments
            import sys
            print("args are:", sys.argv)
            # TODO?

    if prism_job:
        if rvfx_root:
            prism_job = Path(prism_job)
            rvfx_root = Path(rvfx_root)
            print("prism_job initially detected as {}".format(prism_job))    

            # remap paths
            project_name = prism_job.name # name guess from prismjob
            new_path = rvfx_root.joinpath( project_name ).as_posix() # combine rvfx_root with project_name
            print("Trying remap of $PRISMJOB from: {} to {}".format(str(prism_job), str(new_path)))

            if rvfx_root.as_posix() not in new_path and hou.isUIAvailable(): # dont think there's ever a case this will be true
                print("job is not part of rockinVFX, exiting 456...")
                return False            
            
            if not Path(new_path).exists(): # last check to see if this new prismjob exists
                print("Path {} does not exist, cannot set prismjob".format(new_path))
                print("Job is not part of rockinVFX, exiting 456...")
                return False

            # Force prism to change project. Needed for workers to correctly pick up right job that deadline pathmapping doesn't fix
            forcePrismUpdate = True
            if forcePrismUpdate:
                pipelinejson = rvfx_root.joinpath(rvfx_root, project_name, "00_Pipeline/pipeline.json")
                PrismInit.pcore.changeProject(pipelinejson.as_posix())

            # set both prism paths
            hou.hscript( "set -g {} = {}".format("PRISMJOB",new_path) )
            hou.hscript( "set -g {} = {}".format("PRISM_JOB",new_path) )
            print("Set $PRISMJOB to {}".format(new_path))                
            return True
        else:
            print("$RVFX_ROOT not defined, can't adjust for deadline. Speak to Luis")    
            return False
    else:
        print("$PRISMJOB currently not defined, no project selected")
        return False

def createSceneVariable(needs_remap=True):
    '''
    Creates $HIP alternative for use on farm
    When should this be set? on UI available sessions only at scene start?
    how should it be set? what if you're off pipe?    
    This does rely on prisms current structure and could break if the depth of scenefiles change
    '''            
    variable = "SCENE"
    variable_path = hou.text.expandString("$"+variable)
    # Check if variable path is set. If not see if we can make it. 
    if variable_path:
        # if variable already exists, check if it is valid
        prismjob = hou.text.expandString("$PRISMJOB") #hou.getenv("PRISMJOB") 
        if not prismjob:
            print("prismjob not defined, exiting scene variable creation")
            return
        
        hip = hou.text.expandString("$HIP")
        # check scene correctly points to HIP (in cases where the hip was copied)
        if hou.isUIAvailable() and hip.startswith(prismjob):
            # now compare hip to scene
            prismjob_name = prismjob.split("/")[-1]
            hip_end = hip.split(prismjob_name)[-1]
            variable_path_end = variable_path.split(prismjob_name)[-1]

            if hip_end != variable_path_end:
                # $SCENE doesnt match. probably was copied from another scene. Create from $HIP
                hip = hou.text.expandString("$HIP")
                # check hip variable is correctly in scenefiles
                if Path(hip).parent.parent.name == "Scenefiles":
                    # set variable with hscript cos putenv doesnt save to hip
                    hou.hscript( "set -g {} = {}".format(variable,hip) )
                    print("${0} did not match shot. Setting ${0} to {1}".format(variable, hip)) 
                    return            

        # Remap Scene to have correct local machine path 
        if not Path(variable_path).as_posix().startswith(prismjob) and needs_remap:
            # path doesnt start with remapped prism job var, so probably needs a remap            
            remapped_path = make_houdini_filepath_relative(variable_path) # path remap
            remapped_path = hou.text.expandString(remapped_path) # expand 
            # check new path exists
            if Path(remapped_path).exists():                
                hou.hscript( "set -g {} = {}".format(variable,remapped_path) )
                print("Set ${} to {}".format(variable, remapped_path))                       
            else:
                # likely the scene doesn't exists and is not synced?
                print("ERROR could not unfuck variable $SCENE")
    else:
        if not hou.isUIAvailable():
            # no interface means we might be in deadline. don't want to do anything here
            print("No interface detected, likely a deadline instance. Not setting $SCENE and exiting...")
            return
        # $SCENE doesn't exist yet. Create from $HIP
        hip = hou.text.expandString("$HIP")
        # check hip variable is correctly in scenefiles
        if Path(hip).parent.parent.name == "Scenefiles":
            # set variable with hscript cos putenv doesnt save to hip
            hou.hscript( "set -g {} = {}".format(variable,hip) )
            print("${0} not found in hip. Setting ${0} to {1}".format(variable, hip)) 

def make_houdini_filepath_relative(path, use_rvfx_root=False):
    if not path:
        return ""
    rvfx_root = Path(hou.getenv("RVFX_ROOT"))
    prismjob = Path(hou.text.expandString("$PRISMJOB"))    
    
    index = str(path).find(prismjob.name)    
    if index != -1:
        if use_rvfx_root: # make relative to rvfx root        
            var = "$RVFX_ROOT/"
            new_path = Path( var + path[index:]) # start at rvfx_root
            return new_path.as_posix()        
        else:  # make relative to prismjob                
            var = "$PRISMJOB/"
            index += len(prismjob.name)+1 # start at prism job
            new_path = Path( var + path[index:])
            return new_path.as_posix()         
    else:        
        return path

def debugVariables():
    '''
    TODO: Add max list limit when printing with UI. set by env var / ui available?
    '''
    from pprint import pprint
    print("%RVFX_ROOT% = {}".format(hou.text.expandString("$RVFX_ROOT")))
    print("%PRISMJOB% = {}".format(hou.text.expandString("$PRISMJOB")))
    print("Houdini Path:")
    pprint(hou.houdiniPath())
    print("PATH variable:")
    pprint(hou.text.expandString("$PATH"))
    print("PYTHONPATH variable:")
    pprint(hou.text.expandString("$PYTHONPATH"))
    print("OCIO variable:")
    pprint(hou.text.expandString("$OCIO"))

    print("Keys in os.environ: \n", dict(os.environ))
    import sys
    print("Script arguments: ", sys.argv)

    if "prism_project" in os.environ:
        print("prism_project found in os.environ as: {}".format(os.environ['prism_project']))
    print("$DEADLINE_SUBMITTER_DIR_REZ = {}".format(hou.text.expandString("$DEADLINE_SUBMITTER_DIR_REZ")))
    if hou.hipFile.basename() != "untitled.hip":
        print("Checking scene's absolute paths...")
        paths = findAllSceneAbsPaths()
        if len(paths)>0:
            print("OH NO! Absolute paths were found...")
            if not hou.isUIAvailable():
                pprint(paths)
        else:
            print("No absolute paths were found :)")

def isRefValid(houFileReference) -> bool:
    # check if parm is ok, then return true
    parm = houFileReference[0]
    path = houFileReference[1]    
    posix_path = Path(path).as_posix()
    # print("posix path: ", posix_path)

    if parm == None:        
        return False  

    if parm.path().startswith("/tasks/topnet1"):
        return False

    if parm.node().isInsideLockedHDA():
        if not parm.node().isEditableInsideLockedHDA():
            return False
    
    to_match = [":/", "$", ":\\"]    
    if any(item in posix_path[0:3] for item in to_match):
        # print("found match for:", path)       
        return True
    else:
        # print("path was: ", path)
        # print("couldn't match {} in {}:".format(posix_path[0:3], to_match))  
        return False

def isRefAbsolute(houFileReference) -> bool:
    # check if parm is ok, then return true
    parm = houFileReference[0]
    path = houFileReference[1]    
    posix_path = Path(path).as_posix()
    # print("posix path: ", posix_path)

    if parm == None:        
        return False  
    
    to_match = [":/"]    
    if any(item in posix_path[0:3] for item in to_match):
        # print("found absolute match for:", path)
        return True
    else:
        return False
    
def add_missing_fileRefs(file_refs):
    '''
    Temp fix for hou.fileReferences() not detecting Reference LOPs correctly.
    '''
    # print(file_refs)
    # quick fix for references
    lops = hou.node("/").recursiveGlob("*", hou.nodeTypeFilter.Lop)
    lops = [n for n in lops if n.type().name().startswith("reference")]
    parms = [n.globParms("filepath*") for n in lops]
    flattened_list = [item for tpl in parms for item in tpl]    
    
    def getParmVal(parm):
        if len(parm.keyframes())>0:
            return parm.evalAsString()
        else:
            return parm.unexpandedString()

    added = tuple((parm, getParmVal(parm)) for parm in flattened_list)    
    return file_refs + added

def findAllSceneAbsPaths() -> list[tuple]:
    file_refs = hou.fileReferences()
    file_refs = add_missing_fileRefs(file_refs)
    file_refs = [x for x in file_refs if isRefValid(x)]    
    abs_refs = [x for x in file_refs if isRefAbsolute(x)]
    # if len(abs_refs)>0:
    #     print("The following parameters contain absolute paths. \
    # Consider fixing them if rendering them crossfarm:\n",
    #         abs_refs)
    # else:
    #     print("No parameters found to contain absolute paths. Nice")
    return abs_refs

def fixParmReference(parm):
    '''
    Fixes any parameters that have absolute references, which cause issues when used on other machines
    TODO: Move to_find as input argument, preserve order of replacement, calc once before
    '''    
    text = parm.evalAsString()
    # find prism project in the path. use that as our reference.
    to_find = ["$PRISMJOB","$RVFX_ROOT"]
    to_find_dict = {}

    # populate paths to search for    
    for key in to_find:
        key_str = key.lstrip("$")
        value = hou.text.expandString('$' + key_str) #hou.getenv(key_str)
        if value:            
            to_find_dict[key] = Path(value).as_posix()
        else:
            print("cant find {} in env".format(key))
            return

    text_posix = Path(text).as_posix()
    prefix = ""
    # print("to_find_dict: ", to_find_dict)
    for key in to_find: # iterate through key list to ensure order
        val = to_find_dict[key]
        index = text_posix.find(val)
        if index != -1:
            index += len(val) # mark start point
            prefix = key
            break

    if index == -1:
        print("can't fix path, couldnt find var to replace absolute path\n ", text_posix, to_find_dict)
        return
    else:
        # must lstrip any slashes before doing joinpath, or it ignores the prefix                
        new_path = Path(prefix).joinpath(text_posix[index:].lstrip("/"))        
        out_text = new_path.as_posix()
        # print("out text is {}".format(out_text))

    parm.set(out_text)
    # print("end of fix parm func")

def fixAllAbsoluteParms():
    '''
    Attempts to fix all absolute parms in the scene
    '''
    file_refs = findAllSceneAbsPaths()   

     
    if len(file_refs)>0:
        parms = [parm for parm,text in file_refs]
        print(parms)
        for parm in parms:
            fixParmReference(parm)
        print("Parm replacement finished")

def sanityCheckPaths():
    refs = findAllSceneAbsPaths()

    if len(refs) > 0:
        paths = [str(pair) for pair in refs]
        paths = ",\n".join(paths)
        txt = "the follow absolute reference were found, do you still want to submit the render?\n {}".format(paths)
        if hou.isUIAvailable():
            confirm = hou.ui.displayConfirmation(txt, severity=hou.severityType.Warning)
        else: # if we are in 456
            from pprint import pprint
            print("### The following absolute paths were found in the scene: ###")
            pprint(paths)
        return False
    else:
        print("no absolute paths found, u good homie")
        return True
    
def getEntityFromPath(filepath) -> dict:
    ''' 
    Leaving this function for prism compatibility
    '''
    entity = {}
    path_parts = Path(filepath).parts
    # print(path_parts)
    anchor_folders = ["00_Pipeline", "01_Management", "02_Designs", "03_Production", "04_Resources"]
    anchor_indices = [i for i, part in enumerate(path_parts) if part in anchor_folders]    
    if anchor_indices:
        anchor_index = min(anchor_indices)
        path_parts_filtered = path_parts[anchor_index:]
        entity['project_path'] = "/".join(path_parts[:anchor_index])
        entity['project_name'] = path_parts[anchor_index-1]
    else:
        path_parts_filtered = path_parts    
    
    if path_parts_filtered[0] == "03_Production":
        # check where the path should end
        assetshot_parts = path_parts_filtered
        end_anchor_index = -1 # default value
        end_folders = ['Export', 'Playblasts', 'Renders', 'Scenefiles']
        end_folder_indices = [i for i, part in enumerate(path_parts_filtered) if part in end_folders]
        if end_folder_indices:
            end_anchor_index = min(end_folder_indices)
            assetshot_parts = assetshot_parts[:end_anchor_index]   

        if assetshot_parts:
        # easy filter case for 03_production
        # there is a case where if the path ends before END_FOLDERS, 
        # you wont know how long the asset is (subfolders)
            context_type = assetshot_parts[1] # Shots or Assets
            if context_type == "Shots":
                entity['type'] = 'shot'
                entity['sequence'] = assetshot_parts[2]
                entity['shot'] = assetshot_parts[3]
            elif context_type == "Assets":
                entity['type'] = 'asset'
                entity['asset_path'] = "/".join(assetshot_parts[2:])
                entity['asset'] = assetshot_parts[-1]
            
            # scenefiles        
            if path_parts_filtered[end_anchor_index] == "Scenefiles":
                after_parts = path_parts_filtered[end_anchor_index:]
                if len(after_parts)>1:
                    entity['department'] = after_parts[1]
                if len(after_parts)>2:
                    entity['task'] = after_parts[2]
                if len(after_parts)>3:
                    entity['_remaining'] = after_parts[3:]    
    return entity   