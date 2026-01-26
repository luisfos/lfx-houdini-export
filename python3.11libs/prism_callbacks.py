"""
Houdini Parameter Context Menu Callbacks for Prism

This module contains callback functions for custom parameter context menu items.

Put this in python source editor to reload module:
import importlib
import prism_callbacks
importlib.reload(prism_callbacks)


TODO:
- Handle deep files on each node
- automate testing
- match prism custom context parms
"""
try:
    import hou
except:
    pass

import tomllib
from pathlib import Path
from pprint import pprint
import json
import os

# Prefix for all spare parameters
PARM_PREFIX = "_lf_"

# Load configuration from TOML file
def load_config():
    """Load the parameter menu configuration from TOML file."""
    config_path = Path(__file__).parent / "prism_config.toml"
    with open(config_path, "rb") as f:
        return tomllib.load(f)

def get_optype_config(optype, config):
    """
    Get configuration for a specific optype.
    Supports inheriting settings from groups and fuzzy matching of node type names.
    
    Args:
        optype: The node type name from Houdini (e.g., 'otoy::Octane_ROP::1.3')
        config: The loaded TOML configuration
        
    Returns:
        dict: Configuration dictionary for the optype
    """
    # Start with the default settings
    optype_config = config.get("default", {}).copy()

    rop_settings = config.get("rop_settings", {})
    hou_optype_lower = optype.lower()
    
    # Find all keys from rop_settings that are substrings of the Houdini node type
    matching_keys = [key for key in rop_settings if key.lower() in hou_optype_lower]
            
    if not matching_keys:
        # No specific settings found, return the defaults
        return optype_config
        
    # Find the longest matching key to resolve ambiguity
    best_match_key = max(matching_keys, key=len)
    
    # Now get the configuration for the best matching key
    node_config_info = rop_settings[best_match_key]
    
    if isinstance(node_config_info, str):
        # It's a direct mapping to a group
        group_name = node_config_info.split('.')[-1]
        group_settings = config.get("groups", {}).get(group_name, {})
        optype_config.update(group_settings)
    elif isinstance(node_config_info, dict):
        # It has its own settings, possibly inheriting from a group
        if "group" in node_config_info:
            group_name = node_config_info["group"].split('.')[-1]
            group_settings = config.get("groups", {}).get(group_name, {})
            optype_config.update(group_settings)
        
        # Apply specific overrides
        optype_config.update(node_config_info)

    return optype_config


def get_prism_structure(project):
    """
    Get the Prism structure for a given project.
    Pulls the following:
    Asset productfiles
    Shot productfiles
    3D Renders
    2D Renders
    External Media?
    Playblasts

    Args:
        project: The project name or identifier

    Returns can look like e.g
    Shot productfiles:
    @productversion_path@/@sequence@-@shot@_@product@_@version@@.(frame)@@extension@
    """
    pass


def write_version_info(node_path: str, parm_name: str):
    """
    Create a `versioninfo.json` file next to the evaluated output file.

    Args:
        kwargs: Houdini callback kwargs containing at least the current `node`.
        parm_name: The name of the parameter which holds the final file path expression.
    """    
    node = hou.node(node_path)
    parm = node.parm(parm_name)
    if parm is None:
        print("write_version_info: Parameter not found:", parm_name)
        return

    filepath = parm.evalAsString()
    if not filepath:
        print("write_version_info: Parameter evaluated to empty string:", parm_name)
        return

    dest_folder = os.path.dirname(filepath)

    # hou.text.expandString instead of hou.expandString as its deprecated
    prism_user = hou.text.expandString("$PRISM_USER")
    source_scene = hou.text.expandString("$HIPFILE")
    # replace source scene absolute path with prism_job
    source_scene = source_scene.replace(hou.text.expandString("$PRISM_JOB"), "$PRISM_JOB")

    # Optional user comment from spare parameter
    comment_parm = node.parm(f"{PARM_PREFIX}comment")
    comment_val = comment_parm.evalAsString() if comment_parm is not None else ""

    data = {
        "comment": comment_val,
        "user": prism_user,
        "sourceScene": source_scene,
    }

    Path(dest_folder).mkdir(parents=True, exist_ok=True)
    out_path = Path(dest_folder) / "versioninfo.json"
    # print("Writing version info to:", out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    


def handle_prism_versioning(kwargs):
    """
    Handle the 'Prism Versionning' context menu action for a parameter.
    
    Creates a spare folder with versioned path parameters and sets up
    a Python expression on the clicked parameter to reference them.
    
    Args:
        kwargs: Dictionary containing context menu kwargs from Houdini
    """
    # Get the parameter that was right-clicked
    parms = kwargs.get('parms', [])
    if not parms:
        hou.ui.displayMessage("No parameter selected", severity=hou.severityType.Warning)
        return
    
    parm = parms[0]
    node = parm.node()
    # optype = node.type().name()
    optype = node.type().nameComponents()[-2]
    is_octane_rop = "octane_rop" in optype.lower() or "octanerendersetup" in optype.lower()
    # Create autoversion toggle parameter only if node has a prerender parm
    has_prerender = node.parm("prerender") is not None
    
    # Load configuration and get optype-specific settings
    config = load_config()
    optype_config = get_optype_config(optype, config)    
    
    # Get extension settings from config
    extensions = optype_config.get("extensions", [".bgeo.sc"])
    default_extension = extensions[0]
    time_dependent_default = optype_config.get("time_dependent", True)    
    default_type = optype_config.get("default_type", "Product")
    
    # Create a spare folder with versioned path parameters
    folder_name = f"{PARM_PREFIX}versioned_path_folder"
    folder_label = "Prism Export Settings"
    
    # Check if the folder already exists - if so, remove it and clear the expression
    existing_folder = node.parm(folder_name)
    if existing_folder is not None:
        # Clear the expression on the original parameter
        try:
            parm.deleteAllKeyframes()
        except:
            pass
        
        # Remove the existing folder
        ptg = node.parmTemplateGroup()
        try:
            ptg.remove(folder_name)
            node.setParmTemplateGroup(ptg)
        except:
            pass
    
    # Create the folder and parameters
    ptg = node.parmTemplateGroup()
    
    # Create folder (collapsible)
    folder = hou.FolderParmTemplate(
        folder_name,
        folder_label,
        folder_type=hou.folderType.Collapsible
    )
    
    # Create type parameter
    type_parm = hou.StringParmTemplate(
        f"{PARM_PREFIX}type",
        "Type",
        1,
        menu_items=["Product", "Playblast", "3dRender", "2dRender"],
        menu_labels=["Product", "Playblast", "3D Render", "2D Render"],
        default_value=[default_type],
        menu_type=hou.menuType.Normal,
        string_type=hou.stringParmType.Regular
    )

    # Create context parameter
    context_parm = hou.StringParmTemplate(
        f"{PARM_PREFIX}context",
        "Context",
        1,
        menu_items=["From Scenefile", "Custom"],
        menu_labels=["From Scenefile", "Custom"],
        default_value=["From Scenefile"],
        menu_type=hou.menuType.Normal,
        string_type=hou.stringParmType.Regular,
        script_callback="""
import prism_callbacks
prism_callbacks.on_context_changed(kwargs)
""",
        script_callback_language=hou.scriptLanguage.Python
    )
    context_parm.setHelp("If set to custom you can change the custom context hidden helper parameters.")
    context_parm.setJoinWithNext(True)

    context_label = hou.LabelParmTemplate(
        f"{PARM_PREFIX}context_label",
        "Context Label",
        (f'`chs("{PARM_PREFIX}shasset")`',),
        )
    context_label.hideLabel(True)
    
    
    # Create identifier parameterparm.setExpression(hscript_expr, language=hou.exprLanguage.Hscript)        
    identifier = hou.StringParmTemplate(
        f"{PARM_PREFIX}identifier",
        "Identifier",
        1,
        # default_value=["$OS"],
        default_value=[ node.name() ],
        string_type=hou.stringParmType.Regular,
        menu_items=[],
        menu_labels=[],
        menu_type=hou.menuType.StringReplace,
        item_generator_script="""
import prism_callbacks
return prism_callbacks.get_existing_identifiers(kwargs)
""",
        item_generator_script_language=hou.scriptLanguage.Python
    )
    # When identifier changes, press Latest to refresh version suggestion
    identifier.setScriptCallback(f"""
kwargs['node'].parm('{PARM_PREFIX}version_lookup').pressButton()
""")
    identifier.setScriptCallbackLanguage(hou.scriptLanguage.Python)
    
    # Create version parameter
    version = hou.IntParmTemplate(
        f"{PARM_PREFIX}version",
        "Version",
        1,
        default_value=[1],
        min=1,
        # min_is_strict=True
    )
    version.setJoinWithNext(True)

    version_lookup_button = hou.ButtonParmTemplate(
        f"{PARM_PREFIX}version_lookup",
        "Latest",
        script_callback="""
import prism_callbacks
prism_callbacks.version_lookup_callback(kwargs)
""",
        script_callback_language=hou.scriptLanguage.Python
    )

    folder.setTags({"sidefx::header_parm": f"{PARM_PREFIX}version"})

    # Disable version parm when autoversion is enabled (only if autoversion exists)
    if has_prerender:
        version.setConditional(
            hou.parmCondType.DisableWhen, f"{{ {PARM_PREFIX}autoversion == 1 }}"
        )
    
    
    # Create extension parameter (dropdown menu with replace type)
    # Uses optype-specific extensions from config    


    extension = hou.StringParmTemplate(
        f"{PARM_PREFIX}extension",
        "Extension",
        1,
        default_value=[default_extension],
        string_type=hou.stringParmType.Regular,
        menu_items=extensions,
        menu_labels=extensions,
        menu_type=hou.menuType.StringReplace
    )

    # for octane_rop, extension handled entirely by octane
    if is_octane_rop:
        extension.setConditional(
            hou.parmCondType.HideWhen, f"{{ {PARM_PREFIX}hide_helpers == 1 }}"
        )

    open_in_button = hou.ButtonParmTemplate(
        f"{PARM_PREFIX}open_in",
        "Open Folder",
        script_callback=f"""
import prism_callbacks
prism_callbacks.open_folder_callback(kwargs, parm_name='{parm.name()}')
""",
        script_callback_language=hou.scriptLanguage.Python
    )
    
    # Create frame parameter (disabled when time_dependent is false)
    frame = hou.StringParmTemplate(
        f"{PARM_PREFIX}frame",
        "Frame",
        1,
        default_value=["$F4"],
        string_type=hou.stringParmType.Regular
    )
    frame.setConditional(hou.parmCondType.DisableWhen, f'{{ {PARM_PREFIX}time_dependent == 0 }}')
    
    # Create time_dependent toggle parameter
    time_dependent = hou.ToggleParmTemplate(
        f"{PARM_PREFIX}time_dependent",
        "Time Dependent",
        default_value=time_dependent_default
    )

    
    if has_prerender:
        autoversion = hou.ToggleParmTemplate(
            f"{PARM_PREFIX}autoversion",
            "Auto Version",
            default_value=True
        )
        # When toggled on, press Latest to auto-pick next version
        autoversion.setScriptCallback(f"""
autoversion = kwargs['parm']
if autoversion and autoversion.evalAsInt() == 1:
    kwargs['node'].parm('{PARM_PREFIX}version_lookup').pressButton()
else:
    v = kwargs['node'].parm('{PARM_PREFIX}version')
    v.set(max(v.evalAsInt(),1))
""")
        autoversion.setScriptCallbackLanguage(hou.scriptLanguage.Python)

    # kwargs['script_value']=="on"
    
    # Create hide_helpers toggle parameter
    hide_helpers = hou.ToggleParmTemplate(
        f"{PARM_PREFIX}hide_helpers",
        "Hide Helper Parameters",
        default_value=True
    )

    # Set expressions on intermediate parameters
    # ctype expression
    ctype_expr = 'ifs(strcmp("$PRISM_SHOT", "") == 0, "asset", "shot")'

    # Custom context parameters
    ctype = hou.StringParmTemplate(
        f"{PARM_PREFIX}ctype",
        "Custom Context Type",
        1,
        default_value=["shot"],
        string_type=hou.stringParmType.Regular,
        menu_items=["shot", "asset"],
        menu_labels=["Shot", "Asset"],
        menu_type=hou.menuType.Normal
    )
    ctype.setConditional(hou.parmCondType.HideWhen, f'{{ {PARM_PREFIX}hide_helpers == 1 }}')
    ctype.setDefaultExpression((ctype_expr))
    # ctype.setDefaultExpressionLanguage(hou.scriptLanguage.Hscript)

    cshasset = hou.StringParmTemplate(
        f"{PARM_PREFIX}cshasset",
        "Custom Shot/Asset",
        1,
        default_value=["$PRISM_SHOT$PRISM_ASSETPATH"],
        string_type=hou.stringParmType.Regular
    )
    cshasset.setConditional(hou.parmCondType.HideWhen, f'{{ {PARM_PREFIX}hide_helpers == 1 }}')

    csequence = hou.StringParmTemplate(
        f"{PARM_PREFIX}csequence",
        "Custom Sequence",
        1,
        default_value=["$PRISM_SEQUENCE"],
        string_type=hou.stringParmType.Regular
    )
    csequence.setConditional(hou.parmCondType.HideWhen, f'{{ {PARM_PREFIX}hide_helpers == 1 }}')

    # Create hidden helper spare parameters
    base = hou.StringParmTemplate(
        f"{PARM_PREFIX}base",
        "Base",
        1,
        default_value=["$PRISMJOB/03_Production"],
        string_type=hou.stringParmType.Regular
    )
    base.setConditional(hou.parmCondType.HideWhen, f'{{ {PARM_PREFIX}hide_helpers == 1 }}')

    shasset = hou.StringParmTemplate(
        f"{PARM_PREFIX}shasset",
        "Shot/Asset",
        1,
        default_value=["Shots/$PRISM_SEQUENCE/$PRISM_SHOT"],
        string_type=hou.stringParmType.Regular
    )
    shasset.setConditional(hou.parmCondType.HideWhen, f'{{ {PARM_PREFIX}hide_helpers == 1 }}')

    etype = hou.StringParmTemplate(
        f"{PARM_PREFIX}etype",
        "Export Type",
        1,
        default_value=["Export"],
        string_type=hou.stringParmType.Regular
    )
    etype.setConditional(hou.parmCondType.HideWhen, f'{{ {PARM_PREFIX}hide_helpers == 1 }}')
    
    # Create hidden intermediate parameters to split up the expression
    # Version string (v001)
    version_str = hou.StringParmTemplate(
        f"{PARM_PREFIX}version_str",
        "Version String",
        1,
        default_value=[""],
        string_type=hou.stringParmType.Regular
    )
    version_str.setConditional(hou.parmCondType.HideWhen, f'{{ {PARM_PREFIX}hide_helpers == 1 }}')
    
    # Frame string (empty or .0001)
    frame_str = hou.StringParmTemplate(
        f"{PARM_PREFIX}frame_str",
        "Frame String",
        1,
        default_value=[""],
        string_type=hou.stringParmType.Regular
    )
    frame_str.setConditional(hou.parmCondType.HideWhen, f'{{ {PARM_PREFIX}hide_helpers == 1 }}')
    
    # Filename (identifier_v001 or identifier_v001.0001)
    filename = hou.StringParmTemplate(
        f"{PARM_PREFIX}filename",
        "Filename",
        1,
        default_value=[""],
        string_type=hou.stringParmType.Regular
    )
    filename.setConditional(hou.parmCondType.HideWhen, f'{{ {PARM_PREFIX}hide_helpers == 1 }}')
    
    # User comment to include in versioninfo.json
    comment_parm = hou.StringParmTemplate(
        f"{PARM_PREFIX}comment",
        "Comment",
        1,
        default_value=[""],
        string_type=hou.stringParmType.Regular,
        tags={
            "editor": "1",
            "editorlines": "5-8",
        },
    )
    
    # Add parameters to folder
    folder.addParmTemplate(type_parm)
    folder.addParmTemplate(context_parm)
    folder.addParmTemplate(context_label)
    folder.addParmTemplate(identifier)
    # Place autoversion before version when present
    if has_prerender:
        folder.addParmTemplate(autoversion)
    folder.addParmTemplate(version)
    folder.addParmTemplate(version_lookup_button)
    folder.addParmTemplate(time_dependent)
    folder.addParmTemplate(frame)
    folder.addParmTemplate(extension)
    folder.addParmTemplate(open_in_button)
    folder.addParmTemplate(comment_parm)
    folder.addParmTemplate(hide_helpers)
    folder.addParmTemplate(ctype)
    folder.addParmTemplate(cshasset)
    folder.addParmTemplate(csequence)
    folder.addParmTemplate(base)
    folder.addParmTemplate(shasset)
    folder.addParmTemplate(etype)
    folder.addParmTemplate(version_str)
    folder.addParmTemplate(frame_str)
    folder.addParmTemplate(filename)
    folder.addParmTemplate(hou.SeparatorParmTemplate(f"{PARM_PREFIX}separator"))
        
    # Insert folder at the top of the parameter list
    ptg.insertBefore((0,), folder)
    node.setParmTemplateGroup(ptg)
    
    # Set expressions on intermediate parameters
    # ctype expression
    ctype_expr = 'ifs(strcmp("$PRISM_SHOT", "") == 0, "asset", "shot")'
    node.parm(f"{PARM_PREFIX}ctype").setExpression(ctype_expr, language=hou.exprLanguage.Hscript)

    # shasset expression
    shasset_expr = f'''ifs(strcmp(chs("{PARM_PREFIX}ctype"), "shot") == 0, "Shots/" + chs("{PARM_PREFIX}csequence") + "/" + chs("{PARM_PREFIX}cshasset"), "Assets/" + chs("{PARM_PREFIX}cshasset"))'''
    node.parm(f"{PARM_PREFIX}shasset").setExpression(shasset_expr, language=hou.exprLanguage.Hscript)

    # etype: maps from type
    etype_expr = f'''ifs(strcmp(chs("{PARM_PREFIX}type"), "Product") == 0, "Export", ifs(strcmp(chs("{PARM_PREFIX}type"), "Playblast") == 0, "Playblasts", ifs(strcmp(chs("{PARM_PREFIX}type"), "3dRender") == 0, "Renders/3dRender", "Renders/2dRender")))'''
    node.parm(f"{PARM_PREFIX}etype").setExpression(
        etype_expr,
        language=hou.exprLanguage.Hscript
    )

    # version_str: "v001"
    node.parm(f"{PARM_PREFIX}version_str").setExpression(
        f'"v" + padzero(4, ch("{PARM_PREFIX}version"))',
        language=hou.exprLanguage.Hscript
    )

   
    
    # frame_str: ".0001" if time_dependent, else ""
    node.parm(f"{PARM_PREFIX}frame_str").setExpression(
        f'ifs(ch("{PARM_PREFIX}time_dependent"), "." + chs("{PARM_PREFIX}frame"), "")',
        language=hou.exprLanguage.Hscript
    )
    
    # filename: includes optional sequence prefix and sanitized cshasset ("/" -> "-")
    # Octane ROPs typically manage/expect the extension separately, so omit it.    

    filename_expr = f'''ifs(strcmp(chs("{PARM_PREFIX}type"), "3dRender") == 0, "beauty/", "")
        + ifs(strcmp(chs("{PARM_PREFIX}csequence"), "") == 0, "", chs("{PARM_PREFIX}csequence") + "-")
        + strreplace(chs("{PARM_PREFIX}cshasset"), "/", "-")
        + "_" + chs("{PARM_PREFIX}identifier")
        + "_" + chs("{PARM_PREFIX}version_str")
        + chs("{PARM_PREFIX}frame_str")'''

    if not is_octane_rop:
        filename_expr += f'''
        + chs("{PARM_PREFIX}extension")'''
    
    node.parm(f"{PARM_PREFIX}filename").setExpression(
        filename_expr,
        language=hou.exprLanguage.Hscript
    )

    # Final path: type / identifier / version / filename
    hscript_expr = f'chs("{PARM_PREFIX}base") + "/" + chs("{PARM_PREFIX}shasset") + "/" + chs("{PARM_PREFIX}etype") + "/" + chs("{PARM_PREFIX}identifier") + "/" + chs("{PARM_PREFIX}version_str") + "/" + chs("{PARM_PREFIX}filename")'
    
    if is_octane_rop:
        parm.set('`'+ hscript_expr + '`')
    else:
        parm.setExpression(hscript_expr, language=hou.exprLanguage.Hscript)        

    # If the node has a postrender script parm, set it to write versioninfo.json
    postrender_parm = node.parm("postrender")
    if postrender_parm is not None:
        node.parm("tpostrender").set(1)
        node.parm("lpostrender").set("python")
        # Use a Python block: create kwargs from current node and call writer with the file parm name
        python_block = f"""
import prism_callbacks
prism_callbacks.write_version_info('`opfullpath(".")`', '{parm.name()}')
"""        
        postrender_parm.set(python_block)

    # If the node has a prerender script parm, set it to press latest version
    prerender_parm = node.parm("prerender")
    if prerender_parm is not None:
        # node.parm("tprerender").set(1)
        node.parm("tprerender").setExpression(f'ch("{PARM_PREFIX}autoversion")') # set if autoversion enabled
        node.parm("lprerender").set("python")        
        pre_python = f"""
hou.parm('`opfullpath(".")`/'+'{PARM_PREFIX}version_lookup').pressButton()
v = hou.parm('`opfullpath(".")`/'+'{PARM_PREFIX}version')
v.set(v.evalAsInt() + 1)
"""
        prerender_parm.set(pre_python)

    # ensure version lookup is run once to set initial version
    node.parm(f'{PARM_PREFIX}version_lookup').pressButton()

    ### TIME DEPENDENT DEFAULTS
    # Link time_dependent based on node type specifics
    
    td_parm = node.parm(f"{PARM_PREFIX}time_dependent")
    
    optype_name = node.type().name().lower()
    # For filecache types, mirror the node's existing 'timedependent' parm
    if "filecache" in optype_name and node.parm("timedependent") is not None:
        td_parm.set(node.parm("timedependent"))
    # For rop_* nodes, link to trange == "off" (single frame -> not time dependent)
    # elif optype_name.startswith("rop_geo") and node.parm("trange") is not None:
    #     td_parm.setExpression('ifs(strcmp(chs("trange"), "off") == 0, 0, 1)', language=hou.exprLanguage.Hscript)
    
        
    
    
    
def context_to_formula(context, export_type):
    """
    Convert a Prism context dictionary to a file path formula.
    
    Args:
        context: Dictionary containing context data from Prism
        export_type: Type of export (e.g. "product", "playblast", "3dRender", "2dRender")
        
    Returns:
        str: File path formula with placeholders
    """
    # mapping for product type to formula
    exports_map = {
        "product": 'Export',
        "playblast": 'Playblasts',
        "3dRender": 'Renders/3dRender',
        "2dRender": 'Renders/2dRender',
        }
    
    # mapping for shot or asset. will have to handle if sequence folder
    shasset_map = {
        "asset": "Assets/@ASSET@",
        "shot": "Shots/@SEQUENCE@/@SHOT@",
        }
    
    BASE = "$PRISMJOB/03_Production"
    formula = f"{BASE}/" + shasset_map[context['type']] + "/" + exports_map[export_type] #+ "/@IDENTIFIER@/@VERSION@/@FILENAME@"
        
    return formula


def version_lookup_callback(kwargs):
    """
    Used as a callback for autoversion behaviour and "latest" button.
    Depends on handle_prism_versioning() having first created the helper parameters.
    Finds the latest version in the output directory and sets the version
    parameter to the latest existing version. Sets to 0 if no versions exist.

    """
    import os
    import re
    
    node = kwargs['node']

    # if autoversion is disabled, do nothing
    autoversion_parm = node.parm(f'{PARM_PREFIX}autoversion')
    if autoversion_parm and autoversion_parm.evalAsInt() == 0:
        return
    
    # Construct the path from helper parameters
    try:
        base_path = node.parm(f'{PARM_PREFIX}base').eval()
        shasset_path = node.parm(f'{PARM_PREFIX}shasset').eval()
        etype_path = node.parm(f'{PARM_PREFIX}etype').eval()
        identifier_path = node.parm(f'{PARM_PREFIX}identifier').eval()
    except AttributeError:
        hou.ui.displayMessage("Helper parameters not found. Cannot look up version.", severity=hou.severityType.Warning)
        return

    lookup_dir = f'{base_path}/{shasset_path}/{etype_path}/{identifier_path}'
    
    if not os.path.isdir(lookup_dir):
        # If the directory doesn't exist, the first version is 1.
        node.parm(f'{PARM_PREFIX}version').set(0)
        return
        
    versions = []
    version_pattern = re.compile(r'^v(\d+)$')
    
    for item in os.listdir(lookup_dir):
        match = version_pattern.match(item)
        if match and os.path.isdir(os.path.join(lookup_dir, item)):
            versions.append(int(match.group(1)))
            
    if versions:
        latest_version = max(versions)
        # latest_version = latest_version + 1
        # we set to the latest existing version for read purposes.
        # prerender script will increment it for write purposes.
        node.parm(f"{PARM_PREFIX}version").set(latest_version)
    else:
        # If no version folders are found, the first version is 1.
        node.parm(f'{PARM_PREFIX}version').set(0)

def open_folder_callback(kwargs, parm_name):
    """
    Callback function to open the folder containing the output file.
    If the folder does not exist, it tries parent directories up to 3 levels.
    """
    import os
    node = kwargs['node']
    parm = node.parm(parm_name)
    if not parm:
        return

    path = parm.eval()
    if not path:
        return

    folder_path = os.path.dirname(path)
    original_folder_path = folder_path

    # Try to find a valid parent directory up to 3 levels up
    for i in range(4):
        if os.path.exists(folder_path):
            os.startfile(folder_path)
            return  # Exit after opening

        # Move to parent directory
        parent_folder = os.path.dirname(folder_path)
        if parent_folder == folder_path:  # Reached root
            break
        folder_path = parent_folder

    # If loop finishes without finding a folder
    hou.ui.displayMessage(f"Folder does not exist: {original_folder_path}", severity=hou.severityType.Warning)

def on_context_changed(kwargs):
    """
    Callback function for when the context parameter is changed.
    """
    node = kwargs['node']
    parm = node.parm(f'{PARM_PREFIX}context')

    ctype_parm = node.parm(f'{PARM_PREFIX}ctype')
    cshasset_parm = node.parm(f'{PARM_PREFIX}cshasset')
    csequence_parm = node.parm(f'{PARM_PREFIX}csequence')

    if parm.evalAsString() == "From Scenefile":
        # Reset custom context parameters to their default values

        # ctype_parm.revertToDefaults()
        ctype_expr = 'ifs(strcmp("$PRISM_SHOT", "") == 0, "asset", "shot")'
        ctype_parm.setExpression(ctype_expr, language=hou.exprLanguage.Hscript)
        cshasset_parm.revertToDefaults()
        csequence_parm.revertToDefaults()
    else:
        # set ctype to no expression
        ctype_parm.deleteAllKeyframes()

def get_existing_identifiers(kwargs):
    """
    Finds existing identifiers in the output directory to populate a menu.
    """
    import os
    
    node = kwargs.get('node')
    if not node:
        return []

    try:
        base_path = node.parm(f'{PARM_PREFIX}base').eval()
        shasset_path = node.parm(f'{PARM_PREFIX}shasset').eval()
        etype_path = node.parm(f'{PARM_PREFIX}etype').eval()
    except AttributeError:
        # This can happen when the menu is being built before parms are evaluated.
        return []

    lookup_dir = f'{base_path}/{shasset_path}/{etype_path}'
    
    if not os.path.isdir(lookup_dir):
        return []
        
    try:
        subfolders = [d for d in os.listdir(lookup_dir) if os.path.isdir(os.path.join(lookup_dir, d))]
        # The menu requires a flat list of token and label pairs.
        menu_items = []
        for folder in subfolders:
            menu_items.extend([folder, folder])
        return menu_items
    except OSError:
        return []

# local testing
if __name__ == "__main__":
    import sys
    from pprint import pprint

    sys.path.append("C:/Program Files/Prism2/Scripts")    
    import os

    print("PYTHONPATH:", os.environ.get("PYTHONPATH"))

    import PrismCore

    core = PrismCore.create(prismArgs=["noUI"])    
    structure = core.projects.getProjectStructure()
    
    pprint(structure)
    asset_filepath = "S:/RockinVFX/01_Sandbox/03_Production/Assets/Rock/Scenefiles/mod/Modeling/Rock_Modeling_v0001.hip"
    shot_filepath = "S:/RockinVFX/01_Sandbox/03_Production/Shots/Users/Luis/Scenefiles/fx/exporter/Users-Luis_exporter_v0001.hiplc"
    asset_context = core.getScenefileData(asset_filepath)
    shot_context = core.getScenefileData(shot_filepath)
    pprint(asset_context)
    pprint(shot_context)

    formula = context_to_formula(asset_context, "product")
    print("Asset formula:", formula)