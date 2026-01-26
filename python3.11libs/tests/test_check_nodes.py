# create geo node in current session
import hou

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
        # parm = op['parm']
        
        context_node = hou.node(f'/obj/{context}')
        # create context node in /obj for clarity        
        if context_node is None or context not in context_node.type().name():
            context_node = hou.node('/obj').createNode(context, context)
        # create node
        rop_node = context_node.createNode(name)
        
    

    

def test_create_geo_node() -> None:
    """Create a Geometry (SOP) node in the current Houdini session."""
    build_scene()
    assert True
    