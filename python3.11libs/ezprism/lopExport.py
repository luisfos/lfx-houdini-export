import PrismInit
from PrismUtils.Decorators import err_catcher as err_catcher

from pathlib import Path
from pprint import pprint
import hou
from rockinvfx import lopGeneral

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *


def updateReadPath(kwargs):
    me = kwargs['node']
    core = PrismInit.pcore
    entity = lopGeneral.getEntity(me, context_only=True)    
    read_path = ""  
    exists = False 

    # modify entity with read parameters
    product_read = me.parm('product_read').evalAsString()
    version_read = None
    entity['product'] = product_read
    do_autoversion = me.parm('do_autoversion_read').evalAsInt()  
    
    if not do_autoversion:
        version_read = me.parm('version_read').evalAsInt()
        version_string = core.versionFormat % version_read               
        entity['version'] = version_string
        # core.products.generateProductPath(entity, product_read, ext, framePadding=fpadding, version=version)        
        
        # finds multiple versions of the product, they dont contain the full path
        find_products = core.products.getVersionsFromProduct(entity, product_read)
        find_products = [entry for entry in find_products if entry['version'] != 'master']
        find_products = [entry for entry in find_products if entry['version'] == version_string]
        
        if len(find_products)>0:
            # for the chosen version, find the full cache path
            read_path = core.products.getPreferredFileFromVersion(find_products[0])      
            exists = True                  
    else: # in auto version
        read_path = core.products.getLatestVersionpathFromProduct(product_read, entity, includeMaster=False)
        if read_path:
            exists = True            
            data = core.products.getProductDataFromFilepath(read_path)
            # if weird case where asset version mixed with identifier, fix manually
            if entity['type'] == 'asset' and not data.get('version','')[1:].isdigit():
                _tmp_split = data.get('identifier','').split(os.path.sep)            
                data['identifier'] = _tmp_split[0]
                data['version'] = _tmp_split[-1]
            version = int(data.get('version', '')[1:])
            me.parm('version_read').set(version)
    
    if not exists:
        # What to do if the read product isn't found
        guess = False
        if guess:
            ext = me.parm('format').evalAsString()
            version_read = me.parm('version_read').evalAsInt()
            version_string = core.versionFormat % version_read
            read_path = core.products.generateProductPath(entity, task=product_read, extension=ext, version=version_string)                
        else:
            read_path = ""
    
    read_path = lopGeneral.make_houdini_filepath_relative(read_path)    
    me.parm('path_read').set(read_path)
    if exists:
        me.parm('read_exists').set("Read product exists")
    else:
        me.parm('read_exists').set("Product doesn't exist, guessing future read path / or blank")
    

def makeExportPath(node):
    '''
    Creates the path we output to
    This cooks per frame I think. could switch to set method if problem
    '''
    # print("inside make export path lopExport")
    me = node
    core = PrismInit.pcore    
    currentEntity = lopGeneral.getEntity(node, context_only=True)
    
    if not currentEntity: # if empty e.g non prism scene        
        return "Not in Prism pipe"    

    save_mode = me.parm('saveMode').evalAsString()    
    do_autoversion = me.parm('do_autoversion').evalAsInt()

    if save_mode == "Custom": # simplest
        entity = currentEntity        
        product = me.parm('product').evalAsString()        
        ext = me.parm('format').evalAsString()
        fpadding = None
        export_per_frame = False
        version = None
        if not do_autoversion:
            manual_version = me.parm('version').evalAsInt()
            version = core.versionFormat % manual_version        
        else: # manually specify rather than use None
            _temp_version = core.products.getVersionsFromProduct(entity, product)
            latest = core.products.getLatestVersionFromVersions(_temp_version, includeMaster=False)
            version = core.versionFormat % 1
            # print(_temp_version,"\n latest:", latest, "\n version:", version)
            if latest:
                # string = latest['version']
                _temp_version = int(latest.get('version', '')[1:])
                _temp_version += 1
                version = core.versionFormat % _temp_version                                        

        if export_per_frame:
            fpadding = "$F%d" % core.framePadding
        # can return new entity from this if pass argument returnDetails
        # but not sure how to export this into the file details                                 
        # for some reason the version was defaulting to scenefile when none in production
        output = core.products.generateProductPath(entity, task=product, extension=ext, framePadding=fpadding, version=version)    
        
    # elif save_mode == "Full": # idk
    #     pass
    # elif save_mode == "Layer":
    #     # bun this mode its too complex same as Full
    #     dep_from_scene = me.parm('depFromSceneFile').evalAsInt()
    #     if dep_from_scene:
    #         department = "fx" #TODO: replace with current scenefile dep
    #     else:
    #         department = me.parm('department').evalAsString()
    #     use_sublayer = me.parm('useSubLayer').evalAsInt()
    #     if use_sublayer:
    #         sublayer = me.parm('sublayer').evalAsString() 
    #         # TODO: sanitise sublayer        
    #     entity = currentEntity
    #     task = '_layer_fx_master'
    #     output = core.products.generateProductPath(entity, task)                   
    
    replace_rvfx = True
    if replace_rvfx:
        path = lopGeneral.make_houdini_filepath_relative(output)        

    updateDescriptiveParm(me)
    return path

def onNodeCreated(kwargs):
    pass

def versionInfoDetails(kwargs, outputPath):
    '''
    For use to create the versioninfo.json that prism relies on
    '''
    me = kwargs['node']
    core = PrismInit.pcore
    entity = lopGeneral.getEntity(me, context_only=False)    

    details = entity.copy()    
    details.pop('filename', None)
    details.pop('extension', None)

    details['comment'] = ''
    if me.parm('do_comment').evalAsInt():
        details['comment'] = me.parm('comment').evalAsString()
    details['sourceScene'] = hou.hipFile.path()
    details['preferredFile'] = Path(outputPath).name
    details['username'] = core.username
    details['user'] = core.user
    from datetime import datetime
    details['date'] = datetime.now().strftime("%y.%m.%d %H:%M:%S")

    return details
    

def onExecute(kwargs):
    '''
    Replaces the "Save to disk" function on usd_rop
    Calls it from within this script due to order of execution
    First scene save, then export, then versioninfo
    '''
    me = kwargs['node']
    core = PrismInit.pcore

    # Query output path
    outputPath = hou.text.expandString(me.parm('outputPath').evalAsString())
    if outputPath == "":
        core.popup("output path incorrect")        
        return

    saveScene = bool(me.parm("saveScene").eval())
    incrementScene = saveScene and bool(
        me.parm("incrementScene").eval()
    )
    if saveScene:            
        if incrementScene:
            hou.hipFile.saveAndIncrementFileName()
        else:
            hou.hipFile.saveAndBackup()

    

    # Export usd (on autoversion, this will cause outputpath parameter to recook, hence query before)
    me.parm('usd_rop/execute').pressButton()

    # export versioninfo.json
    infoPath = core.products.getVersionInfoPathFromProductFilepath(outputPath)
    details = versionInfoDetails(kwargs, outputPath)   
    core.saveVersionInfo(filepath=infoPath, details=details)


def setContextSource(kwargs):
    pass

############################
# CONTEXT FUNCTIONS
############################

def updateDescriptiveParm(node):
    me = node
    core = PrismInit.pcore    

    product = me.parm('product').evalAsString()
    version = core.versionFormat % me.parm('version').evalAsInt()
    context_str = me.parm('context').evalAsString()
    output_text = "{}\n{} - {}".format(context_str, product, version)    
    me.parm('descriptiveparm').set(output_text)

def getContextMenu(kwargs):
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

    if parm.name().startswith("product"):
        entity = lopGeneral.getEntity(me, context_only=True)                
        names = core.products.getProductsFromEntity(entity)
        out = [entry['product'] for entry in names]

    if parm.name() == "version":
        do_autoversion = me.parm('do_autoversion').evalAsInt()
        if not do_autoversion:
            entity = lopGeneral.getEntity(me, context_only=True)
            product_name = me.parm('product').evalAsString()
            entity['product'] = product_name            
            find_versions = core.products.getVersionsFromProduct(entity, product_name)
            versions = [entry['version'] for entry in find_versions if entry['version']!="master"]   
            out = [int(version_string[1:]) for version_string in versions]

    # Context parms
    if parm.name() == "contextSource":        
        out = ['scenefile', 'custom']
        labels = ['From scenefile', 'Custom']        

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
        out = shot_names

    if parm.name() == "context_asset":
        context_type = me.parm("context_type").evalAsString()
        if context_type == "asset":
            find_assets = core.entities.getAssets()
            asset_names = [entry['asset_path'] for entry in find_assets]
            out = asset_names

    # format for houdini menu    
    if not labels:
        pairs = list(zip(out,out))
    else:
        pairs = list(zip(out,labels))
    return [item for sublist in pairs for item in sublist]
        
def onAutoVersionPressed(kwargs):
    ''' 
    TODO: set manual version to latest
    '''
    me = kwargs['node']
    core = PrismInit.pcore  

    do_autoversion = me.parm('do_autoversion').evalAsInt()
    if do_autoversion:
        outputPath = hou.text.expandString(me.parm('outputPath').evalAsString())        
        version = core.products.getVersionFromFilepath(outputPath, num=True)
        version = version or 1        
        me.parm('version').set(version)    
    
def onRefreshContext(kwargs):
    '''
    Updates the context label parm    
    TODO: Need someway to check result entity is correct // Done
    TODO: selecting shot should set sequence if it was not defined    
    '''
    me = kwargs['node']
    core = PrismInit.pcore
    fileName = core.getCurrentFileName()
    entity = core.getScenefileData(fileName)

    context_source = me.parm('contextSource').evalAsString()
    if context_source == "scenefile":
        fileName = core.getCurrentFileName()
        entity = core.getScenefileData(fileName)
    elif context_source == "custom":       
        context_type = me.parm('context_type').evalAsString()
        entity['type'] = context_type
        if context_type == "asset":
            context_asset = me.parm('context_asset').evalAsString()
            entity['asset_path'] = context_asset
        else:
            context_sequence = me.parm('context_sequence').evalAsString()
            context_shot = me.parm('context_shot').evalAsString()
            entity['sequence'] = context_sequence
            entity['shot'] = context_shot                          
    
    context_info = getContextStrFromEntity(entity, status=True)
    me.parm('context').set(context_info)

def getContextStrFromEntity(entity, status=False):
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
    context_source = me.parm('contextSource').evalAsString()
    fileName = core.getCurrentFileName()
    currentEntity = core.getScenefileData(fileName)
    entity = currentEntity

    if context_only:
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
        else:
            entity.pop('asset_path', None)
            context_sequence = me.parm('context_sequence').evalAsString()
            context_shot = me.parm('context_shot').evalAsString()
            entity['sequence'] = context_sequence
            entity['shot'] = context_shot    

        return entity

def getFormats():    
    '''
    for format menu script
    '''
    ext = ['.usdc', '.usda']
    pairs = list(zip(ext,ext))
    return [item for sublist in pairs for item in sublist]

