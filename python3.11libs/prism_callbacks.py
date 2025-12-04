"""
Houdini Parameter Context Menu Callbacks for Prism

This module contains callback functions for custom parameter context menu items.
"""
try:
    import hou
except:
    pass

import tomllib
from pathlib import Path
from pprint import pprint

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
    optype = node.type().name()
    
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
    
    
    # Create identifier parameter
    identifier = hou.StringParmTemplate(
        f"{PARM_PREFIX}identifier",
        "Identifier",
        1,
        default_value=["$OS"],
        string_type=hou.stringParmType.Regular
    )
    
    # Create version parameter
    version = hou.IntParmTemplate(
        f"{PARM_PREFIX}version",
        "Version",
        1,
        default_value=[1],
        min=1,
        min_is_strict=True
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
        default_value=[ctype_expr],
        string_type=hou.stringParmType.Regular,
        menu_items=["shot", "asset"],
        menu_labels=["Shot", "Asset"],
        menu_type=hou.menuType.Normal
    )
    ctype.setConditional(hou.parmCondType.HideWhen, f'{{ {PARM_PREFIX}hide_helpers == 1 }}')

    cshasset = hou.StringParmTemplate(
        f"{PARM_PREFIX}cshasset",
        "Custom Shot/Asset",
        1,
        default_value=["$PRISM_SHOT$PRISM_ASSET"],
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
    
    # Add parameters to folder
    folder.addParmTemplate(type_parm)
    folder.addParmTemplate(context_parm)
    folder.addParmTemplate(context_label)
    folder.addParmTemplate(identifier)
    folder.addParmTemplate(version)
    folder.addParmTemplate(version_lookup_button)
    folder.addParmTemplate(time_dependent)
    folder.addParmTemplate(frame)
    folder.addParmTemplate(extension)
    folder.addParmTemplate(open_in_button)
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
    
    # filename: "cshasset_identifier_v001.0001.ext"
    filename_expr = f'''ifs(strcmp(chs("{PARM_PREFIX}type"), "3dRender") == 0, "beauty/", "") + chs("{PARM_PREFIX}csequence") + "-" + chs("{PARM_PREFIX}cshasset") + "_" + chs("{PARM_PREFIX}identifier") + "_" + chs("{PARM_PREFIX}version_str") + chs("{PARM_PREFIX}frame_str") + chs("{PARM_PREFIX}extension")'''
    node.parm(f"{PARM_PREFIX}filename").setExpression(
        filename_expr,
        language=hou.exprLanguage.Hscript
    )

    # Final path: type / identifier / version / filename
    hscript_expr = f'chs("{PARM_PREFIX}base") + "/" + chs("{PARM_PREFIX}shasset") + "/" + chs("{PARM_PREFIX}etype") + "/" + chs("{PARM_PREFIX}identifier") + "/" + chs("{PARM_PREFIX}version_str") + "/" + chs("{PARM_PREFIX}filename")'
    
    parm.setExpression(hscript_expr, language=hou.exprLanguage.Hscript)        
    
    
    
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
    Finds the latest version in the output directory and sets the version
    parameter to the next available version.
    """
    import os
    import re
    
    node = kwargs['node']
    
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
        node.parm(f'{PARM_PREFIX}version').set(1)
        return
        
    versions = []
    version_pattern = re.compile(r'^v(\d+)$')
    
    for item in os.listdir(lookup_dir):
        match = version_pattern.match(item)
        if match and os.path.isdir(os.path.join(lookup_dir, item)):
            versions.append(int(match.group(1)))
            
    if versions:
        latest_version = max(versions)
        next_version = latest_version + 1
        node.parm(f'{PARM_PREFIX}version').set(next_version)
    else:
        # If no version folders are found, the first version is 1.
        node.parm(f'{PARM_PREFIX}version').set(1)

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
    if parm.evalAsString() == "From Scenefile":
        # Reset custom context parameters to their default values
        ctype_parm = node.parm(f'{PARM_PREFIX}ctype')
        cshasset_parm = node.parm(f'{PARM_PREFIX}cshasset')
        csequence_parm = node.parm(f'{PARM_PREFIX}csequence')

        ctype_parm.revertToDefaults()
        cshasset_parm.revertToDefaults()
        csequence_parm.revertToDefaults()

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