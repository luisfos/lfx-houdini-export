from pxr import Usd, Sdf
import enum
import os
import hou
from pathlib import Path
import re
from pprint import pprint

###
#  Read Data
###

def make_data_dict(filepath, prim=None, attr="", layer=False) -> dict:
    data = {}
    data['filepath'] = filepath
    if prim:
        data['prim'] = str(prim.GetPath())
    if attr:
        data['attribute'] = attr
    if layer:
        data['layer'] = True
    return data    

def get_prim_attrib_paths(prim) -> list[dict]:
    attribs = prim.GetAuthoredAttributes()
    attribs = [ attr for attr in attribs if attr.GetTypeName() == 'asset' or attr.GetName().endswith('file') ]
    # filter any non sdf.AssetPaths
    attribs = [ attr for attr in attribs if type(attr.Get()).__name__ == "AssetPath" ]
    paths = [(attr.GetName(), attr.Get().resolvedPath) for attr in attribs]
    paths = [x for x in paths if x[-1]] # remove empty    
    return [make_data_dict(path[-1], prim=prim, attr=path[0]) for path in paths]
    
def get_stage_layer_paths(stage):
    layers = stage.GetLayerStack()
    layers = [l for l in layers if not l.identifier.startswith("anon:")]
    paths = [l.identifier for l in layers]
    data = [ make_data_dict(path, layer=True) for path in paths]    
    return data
    
def get_prim_references(prim):
    '''
    To test with references, payloads, other shit
    '''
    paths = []
    if prim.HasAuthoredReferences():
        query = Usd.PrimCompositionQuery(prim)
        for arc in query.GetCompositionArcs():
            find = arc.GetTargetLayer() # sdf find
            if find:
                identifier = find.identifier
                if not identifier.startswith("anon:"):
                    paths.append(identifier)
    return paths               
    
###
#  Convert Data to USD
###
class fs(enum.Enum):
    LOST = -1
    UNSYNCED = 0
    FOUND = 1

class Entry:
    def __init__(self, data: dict):
        for key, value in data.items():                   
            # if hasattr(self, key):
                # This will invoke the property setter if one exists
                # setattr(self, key, value)
            # else:
                # Otherwise, set the attribute directly

            if key == "filepath": # trigger property setter
                self.filepath = value
                #setattr(self, f"{key}", value)
            else:
                print('setting {} to {}'.format(key,value))
                setattr(self, f"_{key}", value)

        
        
    @property
    def filepath(self):
        return self._filepath
        
    @filepath.setter
    def filepath(self, new_filepath):
        self._filepath = Path(new_filepath).as_posix()
        self._label = self.label_from_filepath(self._filepath)
        self._targetPrim = self.make_prim_target(self._filepath)     
        self._status = self.check_file_status(self._filepath)   
        print(f"Start of filepath setting for:\n{self._filepath}\n{self._label}\n{self._targetPrim}\n{self._status}\n")     
        
    def add_to_stage(self, stage):        
        components = [ 
            str(self._status.name).capitalize(),
            self._targetPrim,
            self._label 
        ]     
        prim_to_create = '/' + '/'.join(components)    
        print("Creating prim at: ", prim_to_create)
        
        prim = stage.DefinePrim(prim_to_create)
        # print(prim)
        original_path = getattr(self, '_prim', '')
        # print(original_path)
        prim.CreateAttribute('original_path', Sdf.ValueTypeNames.String).Set(original_path)
        self._createdPrim = str(prim.GetPath())
        

    def check_file_status(self, filepath):
        path = Path(filepath)
        if path.exists():
            return fs.FOUND        
        rsls_path = path.with_suffix('.rsls')
        if rsls_path.exists():
            return fs.UNSYNCED
        else:
            return fs.LOST         

    def label_from_filepath(self, name):
        if isinstance(name, Path):
            name = name.name
        else:
            name = os.path.basename(name)
        bad_chars = [':', '.', '[', ']', '-', '~', ' ', '?']
        for char in bad_chars:
            name = name.replace(char, "_")
        return name
    
    def make_prim_target(self, filepath):
        prismjob = hou.text.expandString("$PRISMJOB")
        parts = simplifyFilepathToPrims(filepath)        
        # fix any folder names starting with a number
        parts = ["_"+p if p[0].isdigit() else p for p in parts]
        # print("parts are:", parts)

        if filepath.lower().startswith(prismjob.lower()):                        
            prefix = ""
        else:
            prefix = "Misc/"
        output = prefix + "/".join(parts)
        output.replace("//","/")        
        return output
        
            
def get_file_status(filepath):
    '''
    Determines whether the file exists, or is unsynced, or lost
    -1 Lost
    0 Unsynced
    1 Found   
    '''
    path = Path(filepath)
    if path.exists():
        return fs.FOUND
    
    rsls_path = path.with_suffix('.rsls')
    if rsls_path.exists():
        return fs.UNSYNCED
    else:
        return fs.LOST       
        
def parse_scene_for_filepath_data(stage) -> list[dict]:
    files = []
    # Layers
    layer_paths = get_stage_layer_paths(stage) # list of dict    
    files.extend(layer_paths)
    # Attributes
    prims = stage.TraverseAll()    
    attribute_paths = []
    for prim in prims:
        paths = get_prim_attrib_paths(prim)
        if paths:
            attribute_paths.append(paths)
        
    # flatten list 
    attribute_paths = sum(attribute_paths, [])
    
    files.extend(attribute_paths)
    return files

def lost_and_found_main(output_stage, data: list) -> None:
    pr_found = output_stage.DefinePrim("/Found")
    pr_unsynced = output_stage.DefinePrim("/Unsynced")
    pr_lost = output_stage.DefinePrim("/Lost")

    for datadict in data:
        print("___ New datadict ___")
        # datadict = data[0]
        if datadict['filepath'].startswith("opdef:"):
            continue
        entry = Entry(datadict)
        entry.add_to_stage(output_stage)

        print("=== End of entry ===")
        # break

    
def simplifyFilepathToPrims(filepath) -> list:
    output = []
    entity = {}
    path_parts = Path(filepath).parts
    # Check if the last part of the path is a file (by checking for an extension)
    if path_parts[-1].count('.') > 0:
        path_parts = path_parts[:-1]    
    
    anchor_folders = ["00_Pipeline", "01_Management", "02_Designs", "03_Production", "04_Resources"]
    anchor_indices = [i for i, part in enumerate(path_parts) if part in anchor_folders]    
    if anchor_indices:
        anchor_index = min(anchor_indices)
        path_parts_filtered = path_parts[anchor_index:]
        entity['project_path'] = "/".join(path_parts[:anchor_index])
        entity['project_name'] = path_parts[anchor_index-1]
        output.append(path_parts[anchor_index-1])
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
            context_type = assetshot_parts[1] # Shots or Assets
            if context_type == "Shots":
                entity['type'] = 'shot'
                entity['sequence'] = assetshot_parts[2]
                entity['shot'] = assetshot_parts[3]                
                output.append(context_type)
                output.extend(assetshot_parts[2:4])
            elif context_type == "Assets":
                entity['type'] = 'asset'
                entity['asset_path'] = "/".join(assetshot_parts[2:])
                entity['asset'] = assetshot_parts[-1]
                output.append(context_type)
                output.extend(assetshot_parts[2:])            
            # scenefiles        
            if path_parts_filtered[end_anchor_index] == "Scenefiles":
                after_parts = path_parts_filtered[end_anchor_index:]
                # output.append(after_parts)
                if len(after_parts)>1:
                    entity['department'] = after_parts[1]
                    output.append(after_parts[1])
                if len(after_parts)>2:
                    entity['task'] = after_parts[2]
                    output.append(after_parts[2])
    else: #if path_parts_filtered[0] == "04_Resources":
        if 'project_name' not in entity.keys(): # for non prism
            output.extend(path_parts[1:3])
        else: # for prism stuff but not in production
        # just add a few of them 
            output.extend(path_parts_filtered[:5])

    return output



if __name__ == "__main__":
    # test01 = r"E:\Projects\RockinVFX\25_FHTG2\03_Production\Assets\Environment\Arena"#\Scenefiles\Lookdev\Shading\geo"
    # test02 = "E:/Projects/RockinVFX/25_FHTG2/03_Production/Shots/SQ05/SH070/Scenefiles/lgt/Lighting/"
    test01 = r"E:\Projects\RockinVFX\25_FHTG2\04_Resources\Assets\Arena_collect\barrier\3d_modular_uhbicgudw"
    test02 = r"D:\Downloads\FanControl"
    print(simplifyFilepathToPrims(test01))
    print(simplifyFilepathToPrims(test02))

