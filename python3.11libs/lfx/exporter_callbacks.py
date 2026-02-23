"""
Houdini Parameter Context Menu Callbacks

This module contains callback functions for custom parameter context menu items.

Put this in python source editor to reload module:
import importlib
import lfx.exporter_callbacks as exporter_callbacks
importlib.reload(exporter_callbacks)


TODO:
- Support octane rop
- Copy improved logic from exporter_prism_callbacks
-- Handle case where no version folders exist (set version to 1)
-- connect prerender script to autoversion
-- autoversion toggle callback to min version to 1 when disabled

"""

import hou
import os
import re
import textwrap
import tomllib
from pathlib import Path

# Prefix for all spare parameters
PARM_PREFIX = "_lfx_"


def sanitise_multiline(code: str) -> str:
    '''
    Checks multiline python code that is often used for houdini parameter callbacks
    Dedents code to allow us to write nicely formatted multiline code
    Compile() to check for syntax errors early
    Wraps code in a dummy function to allow return statements
    '''
    sanitised_code = textwrap.dedent(code).strip("\n")
    wrapped_for_compile = "def __callback_wrapper__():\n" + textwrap.indent(
        sanitised_code or "pass",
        "    ",
    )
    compile(wrapped_for_compile, "<multiline_callback>", "exec")
    return sanitised_code

def load_prefs() -> dict:
    """Load user preferences from preferences_config.toml."""
    prefs_path = Path(__file__).parent / "preferences_config.toml"
    if not prefs_path.exists():
        return {}
    try:
        with open(prefs_path, "rb") as f:
            data = tomllib.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _join_base_and_suffix(base_folder: str, base_suffix: str) -> str:
    base = "" if base_folder is None else str(base_folder)
    suffix = "" if base_suffix is None else str(base_suffix)

    base = base.rstrip("/\\")
    suffix = suffix.strip()
    if not suffix:
        return base
    if not base:
        return suffix
    return base + "/" + suffix.lstrip("/\\")

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
    
    kparm = parms[0]
    knode = kparm.node()
    optype = knode.type().name()    
    optype_name = knode.type().nameComponents()[-2].lower()
    

    # Create autoversion toggle parameter only if node has a prerender parm
    has_prerender = knode.parm("prerender") is not None
    
    # Load configuration and get optype-specific settings
    config = load_config()
    optype_config = get_optype_config(optype, config)
    
    # Get extension settings from config
    extensions = optype_config.get("extensions", [".bgeo.sc"])
    default_extension = optype_config.get("default_extension", extensions[0] if extensions else ".bgeo.sc")
    time_dependent_default = optype_config.get("time_dependent", True)
    base_suffix_default = optype_config.get("base_suffix", "/geo")

    prefs = load_prefs()
    prefs_base_folder = prefs.get("base_folder", "$HIP")
    base_folder_default = _join_base_and_suffix(prefs_base_folder, base_suffix_default)
    
    # Create a spare folder with versioned path parameters
    folder_name = f"{PARM_PREFIX}exporter_folder"
    folder_label = "LFX Export"
    
    # Check if the folder already exists - if so, remove it and clear the expression
    existing_folder = knode.parm(folder_name)
    if existing_folder is not None:
        # Clear the expression on the original parameter
        try:
            kparm.deleteAllKeyframes()
        except Exception:
            pass
        
        # Remove the existing folder
        ptg = knode.parmTemplateGroup()
        try:
            ptg.remove(folder_name)
            knode.setParmTemplateGroup(ptg)
        except Exception:
            pass
    
    # Create the folder and parameters
    ptg = knode.parmTemplateGroup()
    
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
    
    identifier_item_generator_code = sanitise_multiline("""
        import lfx.exporter_callbacks as exporter_callbacks
        return exporter_callbacks.get_existing_identifiers(kwargs)
    """)

    # Create identifier parameter
    identifier = hou.StringParmTemplate(
        f"{PARM_PREFIX}identifier",
        "Identifier",
        1,
        default_value=["$OS"],
        string_type=hou.stringParmType.Regular,
        menu_items=[],
        menu_labels=[],
        menu_type=hou.menuType.StringReplace,
        item_generator_script=identifier_item_generator_code,
        item_generator_script_language=hou.scriptLanguage.Python
    )
    identifier.setJoinWithNext(True)

    # When identifier changes, press Latest to refresh version suggestion
    identifier_changed_callback_code = sanitise_multiline(f"""
        kwargs['node'].parm('{PARM_PREFIX}version_lookup').pressButton()
    """)
    identifier.setScriptCallback(identifier_changed_callback_code)
    identifier.setScriptCallbackLanguage(hou.scriptLanguage.Python)

    open_in_button_callback_code = sanitise_multiline(f"""
        import lfx.exporter_callbacks as exporter_callbacks
        exporter_callbacks.open_folder_callback(kwargs, parm_name='{kparm.name()}')
    """)

    open_in_button = hou.ButtonParmTemplate(
        f"{PARM_PREFIX}open_in",
        "Open Folder",
        script_callback=open_in_button_callback_code,
        script_callback_language=hou.scriptLanguage.Python
    )
    
    # Create version parameter
    version = hou.IntParmTemplate(
        f"{PARM_PREFIX}version",
        "Version",
        1,
        default_value=[1],
        min=0,
        min_is_strict=False
    )
    # When autoversion exists, keep Version + Auto Version on the same row.
    if has_prerender:
        version.setJoinWithNext(True)
    folder.setTags({"sidefx::header_parm": f"{PARM_PREFIX}version"})

    # Disable version parm when autoversion is enabled (only if autoversion exists)
    if has_prerender:
        version.setConditional(
            hou.parmCondType.DisableWhen, f"{{ {PARM_PREFIX}autoversion == 1 }}"
        )

    version_lookup_button_callback_code = sanitise_multiline("""
        import lfx.exporter_callbacks as exporter_callbacks
        exporter_callbacks.version_lookup_callback(kwargs)
    """)

    version_lookup_button = hou.ButtonParmTemplate(
        f"{PARM_PREFIX}version_lookup",
        "Latest",
        script_callback=version_lookup_button_callback_code,
        script_callback_language=hou.scriptLanguage.Python
    )

    if has_prerender:
        autoversion = hou.ToggleParmTemplate(
            f"{PARM_PREFIX}autoversion",
            "Auto Version",
            default_value=True
        )
        # When toggled on, press Latest to auto-pick next version
        autoversion_toggle_callback_code = sanitise_multiline(f"""
            autoversion = kwargs['parm']
            if autoversion and autoversion.evalAsInt() == 1:
                kwargs['node'].parm('{PARM_PREFIX}version_lookup').pressButton()
            else:
                v = kwargs['node'].parm('{PARM_PREFIX}version')
                v.set(max(v.evalAsInt(), 1))
        """)

        autoversion.setScriptCallback(autoversion_toggle_callback_code)
        autoversion.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        autoversion.setJoinWithNext(True)
    
    
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
    frame.setJoinWithNext(True)
    
    # Create time_dependent toggle parameter
    time_dependent = hou.ToggleParmTemplate(
        f"{PARM_PREFIX}time_dependent",
        "Time Dependent",
        default_value=time_dependent_default
    )
    time_dependent.setJoinWithNext(True)
    
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

    # Final output path helper
    output_path = hou.StringParmTemplate(
        f"{PARM_PREFIX}output_path",
        "Output Path",
        1,
        default_value=[""],
        string_type=hou.stringParmType.Regular
    )
    output_path.setConditional(hou.parmCondType.HideWhen, f'{{ {PARM_PREFIX}hide_helpers == 1 }}')
    
    # Add parameters to folder
    folder.addParmTemplate(base_folder)
    folder.addParmTemplate(identifier)
    folder.addParmTemplate(open_in_button)
    # Place autoversion before version when present
    if has_prerender:
        folder.addParmTemplate(autoversion)
    folder.addParmTemplate(version)
    folder.addParmTemplate(version_lookup_button)
    folder.addParmTemplate(time_dependent)
    folder.addParmTemplate(frame)
    folder.addParmTemplate(extension)
    folder.addParmTemplate(hide_helpers)
    folder.addParmTemplate(version_str)
    folder.addParmTemplate(frame_str)
    folder.addParmTemplate(filename)
    folder.addParmTemplate(output_path)
        
    # Insert folder at the top of the parameter list
    ptg.insertBefore((0,), folder)
    knode.setParmTemplateGroup(ptg)
    
    # Set the identifier to the current node name
    knode.parm(f"{PARM_PREFIX}identifier").set(knode.name())
    
    # Set expressions on intermediate parameters
    # version_str: "v001"
    knode.parm(f"{PARM_PREFIX}version_str").setExpression(
        f'"v" + padzero(3, ch("{PARM_PREFIX}version"))',
        language=hou.exprLanguage.Hscript
    )
    
    # frame_str: ".0001" if time_dependent, else ""
    frame_hscript_code: str = '''{ 
            if( ch("_lfx_time_dependent")==1 ) {
                return "." + chs("_lfx_frame");
            } else {
                return "";
            }       
        }'''
    frame_hscript_code = textwrap.dedent(frame_hscript_code).strip("\n")
    knode.parm(f"{PARM_PREFIX}frame_str").setExpression(
        frame_hscript_code,
        language=hou.exprLanguage.Hscript
    )

    
    # filename: "identifier_v001.0001.ext" or "identifier_v001.ext"
    # Octane ROPs typically manage/expect the extension separately, so omit it.
    if optype == "octane_rop":
        filename_expr = (
            f'chs("{PARM_PREFIX}identifier") + "_" + chs("{PARM_PREFIX}version_str") + chs("{PARM_PREFIX}frame_str")'
        )
    else:
        filename_expr = (
            f'chs("{PARM_PREFIX}identifier") + "_" + chs("{PARM_PREFIX}version_str") + chs("{PARM_PREFIX}frame_str") + chs("{PARM_PREFIX}extension")'
        )

    knode.parm(f"{PARM_PREFIX}filename").setExpression(
        filename_expr,
        language=hou.exprLanguage.Hscript
    )
    
    # Final path helper: base / identifier / version / filename
    output_path_expr = f'chs("{PARM_PREFIX}base_folder") + "/" + chs("{PARM_PREFIX}identifier") + "/" + chs("{PARM_PREFIX}version_str") + "/" + chs("{PARM_PREFIX}filename")'

    knode.parm(f"{PARM_PREFIX}output_path").setExpression(
        output_path_expr,
        language=hou.exprLanguage.Hscript
    )

    # Set the clicked parameter to evaluate output_path helper
    target_expr = f'chs("{PARM_PREFIX}output_path")'       
    # set final expression
    kparm.setExpression(target_expr, language=hou.exprLanguage.Hscript)

    # If the node has a prerender script parm, set it to auto-version
    prerender_parm = knode.parm("prerender")
    if prerender_parm is not None:
        knode.parm("tprerender").setExpression(f'ch("{PARM_PREFIX}autoversion")')
        knode.parm("lprerender").set("python")
        pre_python = sanitise_multiline(f"""
        hou.parm('`opfullpath(".")`/'+'{PARM_PREFIX}version_lookup').pressButton()
        v = hou.parm('`opfullpath(".")`/'+'{PARM_PREFIX}version')
        v.set(v.evalAsInt() + 1)
        """)
        prerender_parm.set(pre_python)

    # Ensure version lookup is run once to set initial version
    knode.parm(f'{PARM_PREFIX}version_lookup').pressButton()

    '''
    CUSTOM LINKS BASED ON NODE TYPE
    '''    
    if optype_name == "octane_rop":        
        # Octane ROPs cannot handle expressions, so we use hscript eval
        kparm.deleteAllKeyframes()
        kparm.set('`' + target_expr + '`')
        knode.parm(f'{PARM_PREFIX}extension').set("See Octane parameter")

        # deep
        knode.parm('HO_img_deepFile').set('`' + target_expr + '`' + '_deep')
    
    ### TIME DEPENDENT DEFAULTS
    # Link time_dependent based on node type specifics
    
    td_parm = knode.parm(f"{PARM_PREFIX}time_dependent")    
    # For filecache types, mirror the node's existing 'timedependent' parm
    if "filecache" in optype_name and knode.parm("timedependent") is not None:
        td_parm.set(knode.parm("timedependent"))
        knode.parm('filemethod').set('explicit') # set to explicit


def version_lookup_callback(kwargs):
    """Callback for the 'Latest' button and autoversion behaviour.

    Scans the output directory for folders named like v### and sets the
    helper version parameter to the latest existing version. Sets to 0 if no
    versions exist.
    """
    node = kwargs.get('node')
    if node is None:
        return

    try:
        base_path = node.parm(f'{PARM_PREFIX}base_folder').eval()
        identifier_path = node.parm(f'{PARM_PREFIX}identifier').eval()
    except AttributeError:
        hou.ui.displayMessage(
            "Helper parameters not found. Cannot look up version.",
            severity=hou.severityType.Warning,
        )
        return

    lookup_dir = f'{base_path}/{identifier_path}'

    if not os.path.isdir(lookup_dir):
        node.parm(f'{PARM_PREFIX}version').set(0)
        return

    versions: list[int] = []
    version_pattern = re.compile(r'^v(\d+)$')

    for item in os.listdir(lookup_dir):
        match = version_pattern.match(item)
        if match and os.path.isdir(os.path.join(lookup_dir, item)):
            try:
                versions.append(int(match.group(1)))
            except ValueError:
                continue

    if versions:
        node.parm(f"{PARM_PREFIX}version").set(max(versions))
    else:
        node.parm(f'{PARM_PREFIX}version').set(0)
    
    
def open_folder_callback(kwargs, parm_name):
    """
    Callback function to open/explore the folder containing the output file.
    If the folder does not exist, it tries parent directories up to X levels.
    """
    LEVELS = 4
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

    # Try to find a valid parent directory up to X levels up
    for i in range(LEVELS+1):
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

def get_existing_identifiers(kwargs):
    """
    Finds existing identifiers in the output directory to populate a menu.
    """
    import os
    
    node = kwargs.get('node')
    if not node:
        return []

    try:
        base_path = node.parm(f'{PARM_PREFIX}base_folder').eval()
    except AttributeError:
        # This can happen when the menu is being built before parms are evaluated.
        return []

    lookup_dir = f'{base_path}/'
    
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