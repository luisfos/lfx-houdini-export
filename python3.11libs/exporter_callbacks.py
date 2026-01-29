"""
Houdini Parameter Context Menu Callbacks

This module contains callback functions for custom parameter context menu items.

Put this in python source editor to reload module:
import importlib
import exporter_callbacks
importlib.reload(exporter_callbacks)


TODO:
- Support octane rop
- Copy improved logic from exporter_prism_callbacks
-- Handle case where no version folders exist (set version to 1)
-- connect prerender script to autoversion
-- autoversion toggle callback to min version to 1 when disabled

"""

import hou
import tomllib
from pathlib import Path

# Prefix for all spare parameters
PARM_PREFIX = "_lfx_"

# Load configuration from TOML file
def load_config():
    """Load the parameter menu configuration from TOML file."""
    config_path = Path(__file__).parent / "exporter_config.toml"
    with open(config_path, "rb") as f:
        return tomllib.load(f)

def get_optype_config(optype, config):
    """
    Get configuration for a specific optype.
    Falls back to default if optype not found.
    Supports aliases to reuse configurations.
    
    Args:
        optype: The node type name
        config: The loaded TOML configuration
        
    Returns:
        dict: Configuration dictionary for the optype
    """
    optype_config = config.get(optype, config.get("default", {}))
    
    # Check if this optype is an alias to another
    if "alias" in optype_config:
        alias_target = optype_config["alias"]
        return config.get(alias_target, config.get("default", {}))
    
    return optype_config


def convert_parm(kwargs):
    """
    Handle the 'Versionned path' context menu action for a parameter.
    
    Creates a spare folder with versioned path parameters and sets up
    a Python expression on the clicked parameter to reference them.
    
    Input must contain 'parms' which is the parameter the expression will enter.
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
    default_extension = optype_config.get("default_extension", extensions[0] if extensions else ".bgeo.sc")
    time_dependent_default = optype_config.get("time_dependent", True)
    base_folder_default = optype_config.get("base_folder", "$HIP/geo")
    
    # Create a spare folder with versioned path parameters
    folder_name = f"{PARM_PREFIX}exporter_folder"
    folder_label = "LFX Export"
    
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
    
    
    # Create base_folder parameter
    base_folder = hou.StringParmTemplate(
        f"{PARM_PREFIX}base_folder",
        "Base Folder",
        1,
        default_value=[base_folder_default],
        string_type=hou.stringParmType.Regular
    )
    
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
    folder.addParmTemplate(base_folder)
    folder.addParmTemplate(identifier)
    folder.addParmTemplate(version)
    folder.addParmTemplate(time_dependent)
    folder.addParmTemplate(frame)
    folder.addParmTemplate(extension)
    folder.addParmTemplate(hide_helpers)
    folder.addParmTemplate(version_str)
    folder.addParmTemplate(frame_str)
    folder.addParmTemplate(filename)
        
    # Insert folder at the top of the parameter list
    ptg.insertBefore((0,), folder)
    node.setParmTemplateGroup(ptg)
    
    # Set the identifier to the current node name
    node.parm(f"{PARM_PREFIX}identifier").set(node.name())
    
    # Set expressions on intermediate parameters
    # version_str: "v001"
    node.parm(f"{PARM_PREFIX}version_str").setExpression(
        f'"v" + padzero(3, ch("{PARM_PREFIX}version"))',
        language=hou.exprLanguage.Hscript
    )
    
    # frame_str: ".0001" if time_dependent, else ""
    node.parm(f"{PARM_PREFIX}frame_str").setExpression(
        f'ifs(ch("{PARM_PREFIX}time_dependent"), "." + chs("{PARM_PREFIX}frame"), "")',
        language=hou.exprLanguage.Hscript
    )
    
    # filename: "identifier_v001.0001.ext" or "identifier_v001.ext"
    # Octane ROPs typically manage/expect the extension separately, so omit it.
    if optype == "octane_rop":
        filename_expr = (
            f'chs("{PARM_PREFIX}identifier") + "_" + '
            f'chs("{PARM_PREFIX}version_str") + '
            f'chs("{PARM_PREFIX}frame_str")'
        )
    else:
        filename_expr = (
            f'chs("{PARM_PREFIX}identifier") + "_" + '
            f'chs("{PARM_PREFIX}version_str") + '
            f'chs("{PARM_PREFIX}frame_str") + '
            f'chs("{PARM_PREFIX}extension")'
        )

    node.parm(f"{PARM_PREFIX}filename").setExpression(
        filename_expr,
        language=hou.exprLanguage.Hscript
    )
    
    # Set the clicked parameter to use a simple Hscript expression
    # Final path: base / identifier / version / filename
    hscript_expr = f'chs("{PARM_PREFIX}base_folder") + "/" + chs("{PARM_PREFIX}identifier") + "/" + chs("{PARM_PREFIX}version_str") + "/" + chs("{PARM_PREFIX}filename")'
    
    if optype == "octane_rop":
        # Octane ROPs cannot handle expressions, so we use hscript eval
        parm.set('`' + hscript_expr + '`')
    else:
        parm.setExpression(hscript_expr, language=hou.exprLanguage.Hscript)
    
    
