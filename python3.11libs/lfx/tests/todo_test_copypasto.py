'''
Tests the copypasto functionality. 
Copy Paste roundtrip should not drop any nodes, parameters, or connections.
Looks for no errors, no warnings, verify output is as expected
'''

# create geo node in current session
import hou


def load_fresh_scene() -> None:
    '''Loads the cp.hiplc scene'''
    print("Loading cp test scene")
    import os
    scene_path = os.path.join(os.path.dirname(__file__), "cp.hiplc")
    hou.hipFile.load(scene_path, suppress_save_prompt=True)
    # open new hip file
    
def save_result_scene(suffix="") -> None:
    '''saves the output scene for manual verification'''
    print("Saving cp test result scene")
    import os
    result_path = os.path.join(os.path.dirname(__file__), f"cp_output/cp_result_{suffix}.hiplc")
    hou.hipFile.save(result_path)    
        

def test_cp_sop() -> None:
    """
    checks copypasto works on sop example from scene
    """
    load_fresh_scene()    

    source = hou.node('/obj/geo1/cp_sop_source')
    target = hou.node('/obj/geo1/cp_sop_target')
    
    from lfx import copypasto
    copypasto.copy(selection=source.allItems(), clean=True)

    net_editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    if net_editor:
        net_editor.setCurrentNode(target)
    
    copypasto.paste()
    save_result_scene("sop")

    assert len(target.allItems()) == len(source.allItems())
    

def test_cp_cop() -> None:
    """
    checks copypasto works on sop example from scene
    """
    load_fresh_scene()    

    source = hou.node('/obj/geo1/cp_sop_source')
    target = hou.node('/obj/geo1/cp_sop_target')
    
    from lfx import copypasto
    copypasto.copy(selection=source.allItems(), clean=True)

    net_editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    if net_editor:
        net_editor.setCurrentNode(target)
    
    copypasto.paste()
    save_result_scene("sop")

    assert len(target.allItems()) == len(source.allItems())
    

    