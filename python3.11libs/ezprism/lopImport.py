import PrismInit
from PrismUtils.Decorators import err_catcher as err_catcher

from pathlib import Path
import hou
from rockinvfx import lopGeneral

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *


#
# Parm Callbacks
#
def updateReadPath(kwargs):
    '''
    thiS IS NOT used when using browse button
    based on input parms form a static read parm that will be set on update, to prevent python cooking.
    '''    
    me = kwargs['node']
    core = PrismInit.pcore
    entity = lopGeneral.getEntity(me, context_only=True)    
    me.parm('refreshContext').pressButton()
    read_path = ""  
    exists = False 
    # print("my entity is", entity)

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
    else:
        read_path = core.products.getLatestVersionpathFromProduct(product_read, entity, includeMaster=False)
        if read_path:            
            exists = True
            data = core.products.getProductDataFromFilepath(read_path)
            # print(data)
            version = int(data.get('version', 'v001')[1:])
            me.parm('version_read').set(version)
    
    if not exists:
        # guess the path if it doesn't exist        
        read_path = core.products.generateProductPath(entity, task=product_read, version=version_read)
        read_path = ""
    
    read_path = lopGeneral.make_houdini_filepath_relative(read_path)        
    me.parm('path_read').set(read_path)
    updateDescriptiveParm(kwargs, entity)
    if exists:
        me.parm('read_exists').set("Read product exists")
    else:
        me.parm('read_exists').set("Product doesn't exist, guessing future read path / or blank")

    # if changing product, change node name
    if kwargs['parm'].name() == 'product_read':
        if me.evalParm('do_rename'):# and me.name().startswith('LOP_import'):
            to_name = product_read            
            if entity['type']=='asset':
                to_name = entity['asset_path'].replace('\\','_')
            me.setName('get_{}'.format(to_name), unique_name=True)

# def onRefreshContext(kwargs):
#     '''
#     Updates the context label parm    
#     update all, product, version, info parms etc
#     bit weird this function cos entity stuff happening twice. nearly cyclic dependency

#     TODO: Need someway to check result entity is correct // Done
#     TODO: selecting shot should set sequence if it was not defined    
#     '''
#     me = kwargs['node']
#     core = PrismInit.pcore
#     entity = lopGeneral.getEntity(me, context_only=True)
    
#     # slight edge case where shot is set before sequence
#     if kwargs['parm'].name() == "context_shot":
#         shot = me.parm('context_shot').evalAsString()
#         # returns a tuple of ([sequences],[shots])
#         find_shots = core.entities.getShots(shot)
#         if len(find_shots[0])>0:
#             sequence = find_shots[0][0]
#             me.parm('context_sequence').set(sequence)
       
#     # All below responsible for context info text
#     context_type = me.parm('context_type').evalAsString()
#     entity['type'] = context_type
#     if context_type == "asset":
#         context_asset = me.parm('context_asset').evalAsString()
#         entity['asset_path'] = context_asset
#     else:
#         context_sequence = me.parm('context_sequence').evalAsString()
#         context_shot = me.parm('context_shot').evalAsString()
#         entity['sequence'] = context_sequence
#         entity['shot'] = context_shot                          
    
#     context_info = getContextStrFromEntity(entity, status=True)
#     me.parm('context').set(context_info)

def updateDescriptiveParm(kwargs, entity):
    me = kwargs['node']
    core = PrismInit.pcore
    # entity = lopGeneral.getEntity(me, context_only=True)

    product = me.parm('product_read').evalAsString()
    version = core.versionFormat % me.parm('version_read').evalAsInt()
    context_str = me.parm('context').evalAsString()
    output_text = "{}\n{} - {}".format(context_str, product, version)
    
    me.parm('descriptiveparm').set(output_text)

def clearSearch(kwargs):
    me = kwargs['node']
    core = PrismInit.pcore
    fileName = core.getCurrentFileName()
    entity = core.getScenefileData(fileName)
    entity_type = entity.get("type")

    me.parm('context_type').set(entity_type)
    me.parm('context_sequence').set('')
    me.parm('context_shot').set('')
    me.parm('context_asset').set('')
    if me.parm('product_read'):
        me.parm('product_read').set('')
    if me.parm('do_autoversion_read'):
        me.parm('do_autoversion_read').set(True)

    me.parm('refreshContext').pressButton()

def updateSearchParms(kwargs, data: dict):
    me = kwargs['node']    
    # core = PrismInit.pcore
    # fileName = core.getCurrentFileName()
    # currentEntity = core.getScenefileData(fileName)
    # if compareEntity(currentEntity, data, depth='shot')
    # print(data)
    # easiest to just set to custom. ideally check if not scenefile
    me.parm('contextSource').set('custom')
    me.parm('context_type').set(data.get('type', ''))
    me.parm('context_sequence').set(data.get('sequence', ''))
    me.parm('context_shot').set(data.get('shot', ''))
    me.parm('context_asset').set(data.get('asset_path', ''))
    me.parm('product_read').set(data.get('product', ''))

    me.parm('refreshContext').pressButton()
    
    me.parm('do_autoversion_read').set(False)
    version_int = int(data.get('version','v0001')[1:])
    me.parm('version_read').set(version_int)

def openProductBrowser(kwargs):
    '''
    First need to create import state
    Then can use that state for browse versions
    Find what it will return?
    based on 
    C:\ProgramData\Prism2\plugins\Houdini\Scripts\Prism_Houdini_Node_ImportFile.py
    '''
    me = kwargs['node']
    new_kwargs = kwargs.copy()    
    core = PrismInit.pcore
    
    hijack_node = me.node("SOP/Dummy")
    new_kwargs['node'] = hijack_node    
    
    
    pclass = PrismInit.pcore.appPlugin #.importFile
    state = pclass.getStateFromNode(new_kwargs)
    if not state:
        return
        
    state.ui.browse() # search in browser    
    path = state.ui.getImportPath(expand=True) # returned by ui            
    if path: # if something selected
        data = core.products.getProductDataFromFilepath(path)    
        # relpath = pclass.getPathRelativeToProject( path.as_posix() )    
        
        # Set parms and we done    
        read_path = lopGeneral.make_houdini_filepath_relative(path)            
        me.parm('path_read').set(read_path)    
        updateInfo(kwargs, data)
        updateSearchParms(kwargs, data)
        updateDescriptiveParm((kwargs), data)
        me.parm('read_exists').set("Found product through browser")
        me.parm('product_read').pressButton() # inefficient but means dont need to copy code here
    else:
        # if browse products was cancelled
        pass
     
def updateInfo(kwargs, data):
    '''
    Updates the info parameters based on the entity data
    '''
    me = kwargs['node']
    
    context = getContextStrFromEntity(data, status=False)
    me.parm('info_asset_shot').set(context)
    
    parms = ['product', 'version', 'comment', 'user', 'date']
    for parm in parms:
        info_parm = 'info_{}'.format(parm)
        info_value = data.get(parm)
        if info_value is None:
            info_value = ''
        me.parm(info_parm).set(info_value)

    # set info if exists in data
    # me.parm('info_product').set(data.get('product'))
    # me.parm('info_version').set(data.get('version'))
    # me.parm('info_comment').set(data.get('comment'))

#
# Menu dropdowns
#

def getDropdownMenu(kwargs):
    '''
    returns prism project's shots / assets based on incoming parameter 
    in order of:
    type / sequence / shot / asset / product / version ? 
    '''
    # c = PrismInit.pcore
    me = kwargs['node']
    parm = kwargs['parm']
    
    core = PrismInit.pcore   
    out = []    

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

    if parm.name().startswith("product"):
        entity = lopGeneral.getEntity(me, context_only=True)                
        names = core.products.getProductsFromEntity(entity)
        out = [entry['product'] for entry in names]

    if parm.name().startswith("version"):
        do_autoversion = me.parm('do_autoversion_read').evalAsInt()
        if not do_autoversion:
            entity = lopGeneral.getEntity(me, context_only=True)
            product_name = me.parm('product_read').evalAsString()
            entity['product'] = product_name            
            find_versions = core.products.getVersionsFromProduct(entity, product_name)
            versions = [entry['version'] for entry in find_versions if entry['version']!="master"]   
            out_strings = [version_string for version_string in versions]
            out = [int(version_string[1:]) for version_string in versions]
            pairs = list(zip(out,out_strings))            
            return [item for sublist in pairs for item in sublist]
        
    pairs = list(zip(out,out))
    return [item for sublist in pairs for item in sublist]

def getContextStrFromEntity(entity, status=False):

    if not entity:
        return ""
    core = PrismInit.pcore
    entityType = entity.get("type", "")
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


#
# Utils
#


def make_houdini_filepath_relative(path, use_rvfx_root=False):
    if not path:
        return ""
    rvfx_root = Path(hou.getenv("RVFX_ROOT"))
    prismjob = Path(hou.getenv("PRISMJOB"))    
    
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

#
# Experimental prism state stuff
#
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