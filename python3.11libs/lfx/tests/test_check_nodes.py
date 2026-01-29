# create geo node in current session
import hou

PREFIX = "_lfx_"
# list of OP dicts to test for (inline)
OPs: list[dict] = [
    {"label": "file_sop", "context": "geo", "name": "file","parm": "file"},
    {"label": "filecache", "context": "geo", "name": "filecache","parm": "file"},
    {"label": "alembic",    "context": "ropnet", "name": "alembic",  "parm": "filename"},
    {"label": "geometry",   "context": "ropnet", "name": "geometry", "parm": "sopoutput"},
    {"label": "mantra",     "context": "ropnet", "name": "ifd",      "parm": "vm_picture"},
    {"label": "opengl",     "context": "ropnet", "name": "opengl",   "parm": "picture"},
    {"label": "octane",     "context": "ropnet", "name": "Octane_ROP",   "parm": "HO_img_fileName"},
    {"label": "usd_rop",    "context": "lopnet", "name": "usd_rop",   "parm": "output"},
    {"label": "usdrender_rop",  "context": "lopnet", "name": "usdrender_rop","parm": "outputimage"},
    {"label": "cop_image",  "context": "copnet", "name": "cimage",   "parm": "copoutput"},    
]

def build_scene() -> None:
    print("Building test scene with various ROP nodes...")
    # open new hip file
    hou.hipFile.clear(suppress_save_prompt=True)
    context_node = None
    for op in OPs:
        context = op['context']
        name = op['name']        
        
        context_node = hou.node(f'/obj/{context}')
        # create context node in /obj for clarity        
        if context_node is None or context not in context_node.type().name():
            context_node = hou.node('/obj').createNode(context, context)
        # create node
        rop_node = context_node.createNode(name)
        

def test_versionning_single() -> None:
    """
    Checks the simple versionning that works on any file
    """
    build_scene()

    ele = [op for op in OPs if op['label'] == 'mantra'][0]
    n = hou.node(f'/obj/{ele["context"]}/{ele["name"]}')
    kwargs = {
        'node': n,
        'parms': [n.parm(ele['parm'])],
    }
    
    from lfx import exporter_callbacks
    exporter_callbacks.convert_parm(kwargs)

    version_parm = n.parm(f'{PREFIX}version')

    # default version should be 0 as no version folders exist yet
    assert version_parm is not None
    assert version_parm.evalAsInt() == 0

def test_prism_versionning_single() -> None:
    """
    Checks the prism versionning that requires to be part of prism pipeline
    """
    build_scene()

    ele = [op for op in OPs if op['label'] == 'mantra'][0]
    n = hou.node(f'/obj/{ele["context"]}/{ele["name"]}')
    kwargs = {
        'node': n,
        'parms': [n.parm(ele['parm'])],
    }
    
    from lfx import exporter_prism_callbacks
    exporter_prism_callbacks.convert_parm_prism(kwargs)

    type_parm = n.parm(f'{PREFIX}type')
    assert type_parm is not None
    assert type_parm.evalAsString() == '3dRender'

    version_parm = n.parm(f'{PREFIX}version')
    # default version should be 0 as no version folders exist yet
    assert version_parm is not None
    assert version_parm.evalAsInt() == 0

    
    