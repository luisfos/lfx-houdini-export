'''
Only test the exporter parameters
Looks for no errors, no warnings, verify output is as expected
'''

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
    {"label": "usd_rop",    "context": "lopnet", "name": "usd_rop",   "parm": "lopoutput"},
    {"label": "usdrender_rop",  "context": "lopnet", "name": "usdrender_rop","parm": "outputimage"},
    {"label": "cop_image",  "context": "copnet", "name": "rop_image",   "parm": "copoutput"},    
]

def build_fresh_scene() -> None:
    print("Building test scene with latest ROP nodes...")
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
        rop_node = context_node.createNode(name, name)

    hou.node('/obj').createNode('cam', 'cam1')
    hou.node('/obj').layoutChildren()
    for node in hou.node('/obj').children():
        node.layoutChildren()

        

def test_versionning_single() -> None:
    """
    Checks exporter parms works on a single node so we can fail early
    """
    build_fresh_scene()

    # only test one node
    label = "mantra"    

    ele: dict = next(op for op in OPs if op['label'] == label)
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

def test_exporter_parameters_creation() -> None:
    """
    Checks the exporter parameters create correctly and without errors
    """
    build_fresh_scene()
    from lfx import exporter_callbacks

    # only test mantra
    for op in OPs:
        label = op['label']
        kwargs = {}

        ele: dict = next(op for op in OPs if op['label'] == label)
        n = hou.node(f'/obj/{ele["context"]}/{ele["name"]}')
        if n is None:
            # incase we test plugin nodes such as octane redshift arnold...
            print(f"Node not found for label: {label}, check its installed. Skipping...")
            continue
        kwargs = {
            'node': n,
            'parms': [n.parm(ele['parm'])],
        }        

        print(f"Creating exporter parameters for node: {n.path()} with parm: {ele['parm']}")
        
        exporter_callbacks.convert_parm(kwargs)

        output_path = n.parm(ele['parm']).evalAsString()
        print(f"Output path after conversion: {output_path}")

        version_parm = n.parm(f'{PREFIX}version')
        # default version should be 0 as no version folders exist yet
        assert version_parm is not None
        assert version_parm.evalAsInt() == 0


def tmp_test_prism_versionning_single() -> None:
    """
    Checks the prism versionning that requires to be part of prism pipeline
    """
    build_fresh_scene()

    label = "mantra"

    ele: dict = next(op for op in OPs if op['label'] == label)
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

    
    