import PrismInit
from PrismUtils.Decorators import err_catcher as err_catcher

from pathlib import Path
from pprint import pprint
import hou

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

###
# These functions are shared between the various LOPs to reduce duplicate code 
# Context switching, utility getEntity, Menus
# As long as the nodes share similar parameter menus its ok
###
############################
# CALLBACKS FUNCTIONS
############################

def onAutoVersionPressed(kwargs):
    ''' 
    TODO: set manual version to latest
    '''    
    core = PrismInit.pcore
    me = kwargs['node']
    path = hou.text.expandString(me.parm('outputPath').evalAsString())
    data = core.mediaProducts.getDataFromFilepath(path)
    version = int(data.get('version', '')[1:])
    me.parm('version').set(version)
    

############################
# CONTEXT FUNCTIONS
############################

def getContextMenu():
    '''
    for context menu drop down
    '''
    # contexts = ['stage', 'node', 'scenefile', 'custom']
    # labels = ['from stage metadata', 'from node metadata', 'From scenefile', 'custom']
    contexts = ['scenefile', 'custom']
    labels = ['From scenefile', 'Custom']
    pairs = list(zip(contexts,labels))
    return [item for sublist in pairs for item in sublist]

def getDropdownMenu(kwargs):
    '''
    returns prism project's shots / assets based on incoming parameter 
    '''
    # c = PrismInit.pcore
    me = kwargs['node']
    parm = kwargs['parm']
    
    core = PrismInit.pcore   
    out = []
    labels = []

    # Node specific parms

    # if parm.name().startswith("product"):
    #     entity = getEntity(me, context_only=True)                
    #     names = core.products.getProductsFromEntity(entity)
    #     out = [entry['product'] for entry in names]

    # if parm.name() == "version":
    #     do_autoversion = me.parm('do_autoversion').evalAsInt()
    #     if not do_autoversion:
    #         entity = getEntity(me, context_only=True)
    #         product_name = me.parm('product').evalAsString()
    #         entity['product'] = product_name            
    #         find_versions = core.products.getVersionsFromProduct(entity, product_name)
    #         versions = [entry['version'] for entry in find_versions if entry['version']!="master"]   
    #         out = [int(version_string[1:]) for version_string in versions]

    # Context parms
    if parm.name() == "contextSource":        
        out = ['scenefile', 'custom']
        labels = ['From Scenefile', 'Custom']        

    if parm.name() == "context_asset":
        context_type = me.parm("context_type").evalAsString()
        if context_type == "asset":
            find_assets = core.entities.getAssets()
            asset_names = [entry['asset_path'] for entry in find_assets]
            out = asset_names

    if parm.name() == "context_sequence":
        context_type = me.parm("context_type").evalAsString()
        if context_type == "shot":
            seqs = core.entities.getSequences()
            out = seqs
        else:
            pass
        
    if parm.name() == "context_shot":
        sequence = me.parm('context_sequence').evalAsString()      
              
        find_shots = core.entities.getShots(sequence, getSequences=False)        
        shot_names = [entry['shot'] for entry in find_shots]
        if not sequence: # if sequence not defined, list sequence and shot name
            shot_names = ["{}-{}".format(e['sequence'], e['shot']) for e in find_shots]
            shot_names.sort()
        out = shot_names    

    # format for houdini menu    
    if not labels:
        pairs = list(zip(out,out))
    else:
        pairs = list(zip(out,labels))
    return [item for sublist in pairs for item in sublist]

def onRefreshContext(kwargs):
    '''
    Updates the context label parm    
    update all, product, version, info parms etc
    bit weird this function cos entity stuff happening twice. nearly cyclic dependency      
    // nvm have removed, most handled by getEntity
    '''
    me = kwargs['node']
    core = PrismInit.pcore
    entity = getEntity(me, context_only=True)

    if kwargs['parm'].name() == "context_sequence":
        # maybe reset the shot here? 
        pass
    
    # slight edge case where shot is set before sequence
    if kwargs['parm'].name() == "context_shot":
        # our chosen shot
        shot = me.parm('context_shot').evalAsString()           
        sequence = me.parm('context_sequence').evalAsString()   
        
        if '-' in shot and not sequence:
            # special case when dropdown concats seq+shot for convenience
            # parse it and correct the fields
            split = shot.split('-')
            new_sequence = split[0]
            new_shot = split[1]
            me.parm('context_sequence').set(new_sequence)
            me.parm('context_shot').set(new_shot)                    
            entity['sequence']=new_sequence
            entity['shot']=new_shot
        else:
            # not sure if this code is ever reached now
            find_seq, find_shots = core.entities.getShots(shot) # tuple of ([sequences],[shots])        
            if not sequence and find_seq: # if there are sequences and sequence wasnt selected            
                find_shots = [l for l in find_shots if shot in l['shot']]
                if len(find_shots)==1:
                    new_sequence = find_shots[0]['sequence']
                    me.parm('context_sequence').set(new_sequence)                
                    entity['sequence']=new_sequence # modify entity for use in contextStr
                else:
                    print("shot matches multiple sequences or none at all")
                    pass
            

    context_info = getContextStrFromEntity(entity, status=True)
    me.parm('context').set(context_info)

def getContextStrFromEntity(entity, status=False):
    '''
    Helper function for onRefreshContext
    Formats the current context as a string for a label
    '''
    if not entity:
        return ""
    core = PrismInit.pcore
    entityType = entity.get("type", "")
    entityName = ""
    if entityType == "asset":
        entityName = entity.get("asset_path").replace("\\", "/")
    elif entityType == "shot":
        entityName = core.entities.getShotName(entity)

    context = "%s - %s" % (entityType.capitalize(), entityName)
    
    if status:
        defined = False
        if entityType == "asset":
            if core.entities.getAsset(entityName):
                defined = True
        elif entityType == "shot":
            # if core.entities.getSequences()
            seq = entity.get('sequence')
            proj_shots = core.entities.getShotsFromSequence(seq)
            proj_shots = [entry['shot'] for entry in proj_shots]
            if entity['shot'] in proj_shots:
                defined = True
        if not defined:
            context += " (undefined)"
    return context

def clearSearch(kwargs):    
    me = kwargs['node']
    core = PrismInit.pcore
    fileName = core.getCurrentFileName()
    entity = core.getScenefileData(fileName)
    entity_type = entity.get("type")

    node_type = me.type().name().split("::")[1]

    me.parm('context_type').set(entity_type)
    me.parm('context_sequence').set('')
    me.parm('context_shot').set('')
    me.parm('context_asset').set('')    

    if me.parm('product_read') and node_type=="LOP_import":
        me.parm('product_read').set('')
    if me.parm('do_autoversion_read'):
        me.parm('do_autoversion_read').set(True)
    me.parm('refreshContext').pressButton()

def getParentFolder(create=True):
    '''
    taken from prism_houdini_node_filecache.py
    creates the parent state folder
    '''
    txt = "RVFX LOP Renders"
    
    sm = PrismInit.pcore.getStateManager()
    if not sm:
        return

    for state in sm.states:
        if state.ui.listType != "Export" or state.ui.className != "Folder":
            continue

        if state.ui.e_name.text() != txt:
            continue

        return state

    if create:
        stateData = {
            "statename": txt,
            "listtype": "Export",
            "stateenabled": "PySide2.QtCore.Qt.CheckState.Checked",
            "stateexpanded": True,
        }
        state = sm.createState("Folder", stateData=stateData)
        return state

###
# Utility Functions
###
def getEntity(node, context_only=False):
    '''
    entity is a dictionary that tells prism the context of what we want to do
    it holds info about the shot / asset / task etc
    we initialize it from the current scenefile as the easiest way currently
    then remove what we don't need
    '''
    # get the entity from the current scenefile
    core = PrismInit.pcore
    me = node
    context_source_parm = me.parm('contextSource')
    if context_source_parm:
        context_source = context_source_parm.evalAsString()
    fileName = core.getCurrentFileName()
    currentEntity = core.getScenefileData(fileName) # this pulls from versioninfo data which can be wrong for other machine
    project_path = core.projectPath.rstrip('\\')
    if currentEntity['project_path'] != project_path:
        currentEntity['project_path'] = project_path # temp check for versioninfo overriding wrong path??

    entity = currentEntity
    if context_only:
        # keeps bare minimum. asset/shot/sequence
        entity.pop('department', None)
        entity.pop('task', None)
        entity.pop('user', None)
        entity.pop('username', None)
        entity.pop('filename', None)
        entity.pop('version', None)
        entity.pop('extension', None)
        entity.pop('comment', None)

    if context_source == "scenefile":        
        return entity
    elif context_source == "custom":               
        context_type = me.parm('context_type').evalAsString()
        entity['type'] = context_type
        if context_type == "asset":
            entity.pop('sequence', None)
            entity.pop('shot', None)
            context_asset = me.parm('context_asset').evalAsString()
            entity['asset_path'] = context_asset
        else: ## shot seq            
            entity.pop('asset', None)        
            entity.pop('asset_path', None)
            context_sequence = me.parm('context_sequence').evalAsString()
            context_shot = me.parm('context_shot').evalAsString()
            entity['sequence'] = context_sequence
            entity['shot'] = context_shot    

        return entity
    
def isContextDefined(inputEntity) -> bool:
    '''
    check context is usable
    Needs to be a copy so the pop doesn't affect the entity outside the function
    '''
    entity = inputEntity.copy()
    defined = True    
    # print(entity)

    context_type = entity.pop('type', None)
    if context_type is not None:
        if context_type == "asset":
            asset = entity.pop('asset_path', None)            
            if not asset:
                # print('asset not correct')
                defined = False
        elif context_type == "shot":
            sequence = entity.pop('sequence', None)
            shot = entity.pop('shot', None)
            if not sequence or not shot:                
                # print('sequence or shot not correct')
                defined = False
    else:
        # print('context type not defined')
        defined = False    
    return defined    

def getFormats():    
    '''
    for format menu script
    '''
    ext = ['.usdc', '.usda']
    pairs = list(zip(ext,ext))
    return [item for sublist in pairs for item in sublist]

def make_houdini_filepath_relative(path, use_rvfx_root=False):
    if not path:
        return ""
    rvfx_root = Path(hou.getenv("RVFX_ROOT"))
    prismjob = Path(hou.text.expandString("$PRISMJOB"))    
    
    index = path.find(prismjob.name)    
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

def buttonExplorer(kwargs) -> None:
    '''
    Loops through directory until it finds a path that exists, then opens it 
    '''
    me = kwargs['node']
    core = PrismInit.pcore
    node_type = me.type().name().split("::")[1]

    if node_type == "LOP_import":
        outputPath = me.parm('path_read').evalAsString()
        outputPath = hou.text.expandString(outputPath)
    elif node_type == "LOP_export":
        outputPath = me.parm('path_read_show').evalAsString()
        if not outputPath:
            outputPath = me.parm('outputPath').evalAsString()
        outputPath = hou.text.expandString(outputPath)
    elif node_type == "LOP_render":
        outputPath = me.parm('outputPath').evalAsString()
        outputPath = hou.text.expandString(outputPath)
    to_open = Path(outputPath)
    print("path to find is {}".format(to_open))
    count = 0
    for i in range(8):
        if to_open.exists():
            break
        to_open = to_open.parent
        count = i
    
    print("resolved path to {}".format(to_open))        
    if count > 3:
        print("Couldn't open explorer at path, went up {} directories".format(count))
    core.openFolder(to_open.as_posix())
    
###
# OTHER
###

def updateSceneImports() -> None:
    '''
    Finds all the nodes needing an update and updates them
    '''
    nodetypes = hou.lopNodeTypeCategory().nodeTypes()
    types = ['LOP_import', 'LOP_export', 'LOP_render']
    filtered = []    
    for k,v in nodetypes.items():
        t = [t for t in types if t in k]
        if t:
            filtered.append(v)
            
    nodes = [list(t.instances()) for t in filtered]
    nodes = sum( nodes, [] ) # flatten list

    text = "Updated the following nodes:"    
    for n in nodes:
        # print('checking {}'.format(n.name()))
        product = n.parm('product') # lop import
        if product == None: # lop export
            product = n.parm('product_read')
        
        if 'LOP_render' in n.type().name():            
            before = n.parm('context').evalAsString()
            n.parm('refreshContext').pressButton() # update context
            after = n.parm('context').evalAsString()
            if before != after:
                text += "\n{}, FROM: {} -> {}".format(n.name(), before, after)
            continue
        
        info_before = "{} {} {}".format(
            n.parm('context').evalAsString(), 
            product.evalAsString(),
            n.parm('version_read').evalAsInt()
        )
        # print(n.parm('context').evalAsString())
        n.parm('refreshContext').pressButton() # update context
        updateNodeImportVersion(n) # update version

        version_after = n.parm('version_read').evalAsInt()        
        info_after = "{} {} {}".format(
            n.parm('context').evalAsString(), 
            product.evalAsString(),
            n.parm('version_read').evalAsInt()
        )
        
        if info_after != info_before:
            text += "\n{}, FROM: {} -> {}".format(n.name(), info_before, info_after)
    
    if hou.isUIAvailable():
        if len(text.split('\n'))==1:
            text = "No nodes updated"
        hou.ui.displayMessage(text)


def updateNodeImportVersion(node) -> tuple or None:
    '''
    If the node has "latest" ticked, it will force the version to update to latest
    pressButton() does not change the state of the checkbox, it only triggers callbacks
    Lop export & import luckily share the same parm names but split logic for now
    '''
    me = node
    node_name = me.type().name().split('::')[1]    
    if node_name == 'LOP_export' or node_name == 'LOP_import':
        do_read_latest = me.parm('do_autoversion_read')
        if do_read_latest.evalAsInt():
            v0 = me.parm('version_read').evalAsInt()
            do_read_latest.pressButton()
            v1 = me.parm('version_read').evalAsInt()
            return (v0,v1)
    return None    