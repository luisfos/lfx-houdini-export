import hou
__lf__parent_type = 'geo'
hou_parent = locals().get("hou_parent")
if hou_parent is None:
	pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
	ui_pwd = pane.pwd() if pane is not None else None
	if ui_pwd is not None and ui_pwd.type().name() == __lf__parent_type:
		hou_parent = ui_pwd
if hou_parent is None:
	raise hou.Error("parent of copied nodes does not match the context you are pasting into")


# Initialize parent node variable.
if locals().get("hou_parent") is None:
    hou_parent = hou.node("/obj/cp_sop_source")

# Code for /obj/cp_sop_source/mountain1
hou_node = hou_parent.createNode("attribnoise::2.0", "mountain1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-5.06523, 1.7298))
hou_node.bypass(False)
hou_node.setDisplayFlag(False)
hou_node.hide(False)
hou_node.setHighlightFlag(False)
hou_node.setHardLocked(False)
hou_node.setSoftLocked(False)
hou_node.setSelectableTemplateFlag(False)
hou_node.setSelected(True)
hou_node.setRenderFlag(False)
hou_node.setTemplateFlag(False)
hou_node.setUnloadFlag(False)

# Code for /obj/cp_sop_source/mountain1/attribs parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/mountain1")
hou_parm = hou_node.parm("attribs")
hou_parm.deleteAllKeyframes()
hou_parm.set("P")


# Code for /obj/cp_sop_source/mountain1/displace parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/mountain1")
hou_parm = hou_node.parm("displace")
hou_parm.deleteAllKeyframes()
hou_parm.set(1)


# Code for /obj/cp_sop_source/mountain1/folder1 parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/mountain1")
hou_parm = hou_node.parm("folder1")
hou_parm.deleteAllKeyframes()
hou_parm.set(1)


# Code for /obj/cp_sop_source/mountain1/noiserange parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/mountain1")
hou_parm = hou_node.parm("noiserange")
hou_parm.deleteAllKeyframes()
hou_parm.set("zcentered")


# Code for /obj/cp_sop_source/mountain1/amplitude parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/mountain1")
hou_parm = hou_node.parm("amplitude")
hou_parm.deleteAllKeyframes()
hou_parm.set(0.25)


# Code for /obj/cp_sop_source/mountain1/folder7 parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/mountain1")
hou_parm = hou_node.parm("folder7")
hou_parm.deleteAllKeyframes()
hou_parm.set(1)


# Code for /obj/cp_sop_source/mountain1/fractal parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/mountain1")
hou_parm = hou_node.parm("fractal")
hou_parm.deleteAllKeyframes()
hou_parm.set("hmfT")


# Code for /obj/cp_sop_source/mountain1/oct parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/mountain1")
hou_parm = hou_node.parm("oct")
hou_parm.deleteAllKeyframes()
hou_parm.set(8)


# Code for /obj/cp_sop_source/mountain1/rough parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/mountain1")
hou_parm = hou_node.parm("rough")
hou_parm.deleteAllKeyframes()
hou_parm.set(0.40000000000000002)


# Code for /obj/cp_sop_source/mountain1/remapramp2pos parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/mountain1")
hou_parm = hou_node.parm("remapramp2pos")
hou_parm.deleteAllKeyframes()
hou_parm.set(1)


# Code for /obj/cp_sop_source/mountain1/remapramp2value parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/mountain1")
hou_parm = hou_node.parm("remapramp2value")
hou_parm.deleteAllKeyframes()
hou_parm.set(1)


hou_node.setExpressionLanguage(hou.exprLanguage.Hscript)

# Code to establish connections for /obj/cp_sop_source/mountain1
hou_node = hou_parent.node("mountain1")
if hou_parent.node("vellumpressure1") is not None:
    hou_node.setInput(0, hou_parent.node("vellumpressure1"), 0)
hou_node.setUserData("___Version___", "")
if hasattr(hou_node, "syncNodeVersionIfNeeded"):
    hou_node.syncNodeVersionIfNeeded("")


# Initialize parent node variable.
if locals().get("hou_parent") is None:
    hou_parent = hou.node("/obj/cp_sop_source")

# Code for /obj/cp_sop_source/planarpatch1
hou_node = hou_parent.createNode("planarpatch", "planarpatch1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-4.45424, 7.70978))
hou_node.bypass(False)
hou_node.setDisplayFlag(False)
hou_node.hide(False)
hou_node.setHighlightFlag(False)
hou_node.setHardLocked(False)
hou_node.setSoftLocked(False)
hou_node.setSelectableTemplateFlag(False)
hou_node.setSelected(True)
hou_node.setRenderFlag(False)
hou_node.setTemplateFlag(False)
hou_node.setUnloadFlag(False)

hou_node.setExpressionLanguage(hou.exprLanguage.Hscript)

hou_node.setUserData("___Version___", "")
if hasattr(hou_node, "syncNodeVersionIfNeeded"):
    hou_node.syncNodeVersionIfNeeded("")


# Initialize parent node variable.
if locals().get("hou_parent") is None:
    hou_parent = hou.node("/obj/cp_sop_source")

# Code for /obj/cp_sop_source/vellumpressure1
hou_node = hou_parent.createNode("vellumconstraints", "vellumpressure1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-2.73042, 3.02166))
hou_node.bypass(False)
hou_node.setDisplayFlag(False)
hou_node.hide(False)
hou_node.setHighlightFlag(False)
hou_node.setHardLocked(False)
hou_node.setSoftLocked(False)
hou_node.setSelectableTemplateFlag(False)
hou_node.setSelected(True)
hou_node.setRenderFlag(False)
hou_node.setTemplateFlag(False)
hou_node.setUnloadFlag(False)

# Code for /obj/cp_sop_source/vellumpressure1/constrainttype parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/vellumpressure1")
hou_parm = hou_node.parm("constrainttype")
hou_parm.deleteAllKeyframes()
hou_parm.set("pressure")


# Code for /obj/cp_sop_source/vellumpressure1/stretchstiffness parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/vellumpressure1")
hou_parm = hou_node.parm("stretchstiffness")
hou_parm.deleteAllKeyframes()
hou_parm.set(6)


# Code for /obj/cp_sop_source/vellumpressure1/stretchstiffnessexp parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/vellumpressure1")
hou_parm = hou_node.parm("stretchstiffnessexp")
hou_parm.deleteAllKeyframes()
hou_parm.set("2")


hou_node.setExpressionLanguage(hou.exprLanguage.Hscript)

# Code to establish connections for /obj/cp_sop_source/vellumpressure1
hou_node = hou_parent.node("vellumpressure1")
if hou_parent.node("vellumcloth1") is not None:
    hou_node.setInput(0, hou_parent.node("vellumcloth1"), 0)
if hou_parent.node("vellumcloth1") is not None:
    hou_node.setInput(1, hou_parent.node("vellumcloth1"), 1)
if hou_parent.node("vellumcloth1") is not None:
    hou_node.setInput(2, hou_parent.node("vellumcloth1"), 2)
hou_node.setUserData("___Version___", "2")
if hasattr(hou_node, "syncNodeVersionIfNeeded"):
    hou_node.syncNodeVersionIfNeeded("2")


# Initialize parent node variable.
if locals().get("hou_parent") is None:
    hou_parent = hou.node("/obj/cp_sop_source")

# Code for /obj/cp_sop_source/vellumcloth1
hou_node = hou_parent.createNode("vellumconstraints", "vellumcloth1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-2.73042, 3.91586))
hou_node.bypass(False)
hou_node.setDisplayFlag(False)
hou_node.hide(False)
hou_node.setHighlightFlag(False)
hou_node.setHardLocked(False)
hou_node.setSoftLocked(False)
hou_node.setSelectableTemplateFlag(False)
hou_node.setSelected(True)
hou_node.setRenderFlag(False)
hou_node.setTemplateFlag(False)
hou_node.setUnloadFlag(False)

# Code for /obj/cp_sop_source/vellumcloth1/constrainttype parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/vellumcloth1")
hou_parm = hou_node.parm("constrainttype")
hou_parm.deleteAllKeyframes()
hou_parm.set("cloth")


# Code for /obj/cp_sop_source/vellumcloth1/domass parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/vellumcloth1")
hou_parm = hou_node.parm("domass")
hou_parm.deleteAllKeyframes()
hou_parm.set("on")


# Code for /obj/cp_sop_source/vellumcloth1/dothickness parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/vellumcloth1")
hou_parm = hou_node.parm("dothickness")
hou_parm.deleteAllKeyframes()
hou_parm.set("calcuniform")


# Code for /obj/cp_sop_source/vellumcloth1/stretchstiffness parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/vellumcloth1")
hou_parm = hou_node.parm("stretchstiffness")
hou_parm.deleteAllKeyframes()
hou_parm.set(6)


# Code for /obj/cp_sop_source/vellumcloth1/stretchstiffnessexp parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/vellumcloth1")
hou_parm = hou_node.parm("stretchstiffnessexp")
hou_parm.deleteAllKeyframes()
hou_parm.set("2")


# Code for /obj/cp_sop_source/vellumcloth1/dostretchgrp parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/vellumcloth1")
hou_parm = hou_node.parm("dostretchgrp")
hou_parm.deleteAllKeyframes()
hou_parm.set(1)


# Code for /obj/cp_sop_source/vellumcloth1/dobendgrp parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/cp_sop_source/vellumcloth1")
hou_parm = hou_node.parm("dobendgrp")
hou_parm.deleteAllKeyframes()
hou_parm.set(1)


hou_node.setExpressionLanguage(hou.exprLanguage.Hscript)

# Code to establish connections for /obj/cp_sop_source/vellumcloth1
hou_node = hou_parent.node("vellumcloth1")
if hou_parent.node("null1") is not None:
    hou_node.setInput(0, hou_parent.node("null1"), 0)
hou_node.setUserData("___Version___", "2")
if hasattr(hou_node, "syncNodeVersionIfNeeded"):
    hou_node.syncNodeVersionIfNeeded("2")


# Initialize parent node variable.
if locals().get("hou_parent") is None:
    hou_parent = hou.node("/obj/cp_sop_source")

# Code for /obj/cp_sop_source/vellumpack1
hou_node = hou_parent.createNode("vellumpack", "vellumpack1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-2.73042, 0.659485))
hou_node.bypass(False)
hou_node.setDisplayFlag(False)
hou_node.hide(False)
hou_node.setHighlightFlag(False)
hou_node.setHardLocked(False)
hou_node.setSoftLocked(False)
hou_node.setSelectableTemplateFlag(False)
hou_node.setSelected(True)
hou_node.setRenderFlag(False)
hou_node.setTemplateFlag(False)
hou_node.setUnloadFlag(False)

hou_node.setExpressionLanguage(hou.exprLanguage.Hscript)

# Code to establish connections for /obj/cp_sop_source/vellumpack1
hou_node = hou_parent.node("vellumpack1")
if hou_parent.node("mountain1") is not None:
    hou_node.setInput(0, hou_parent.node("mountain1"), 0)
if hou_parent.node("vellumpressure1") is not None:
    hou_node.setInput(1, hou_parent.node("vellumpressure1"), 1)
hou_node.setUserData("___Version___", "")
if hasattr(hou_node, "syncNodeVersionIfNeeded"):
    hou_node.syncNodeVersionIfNeeded("")


# Initialize parent node variable.
if locals().get("hou_parent") is None:
    hou_parent = hou.node("/obj/cp_sop_source")

# Code for /obj/cp_sop_source/null1
hou_node = hou_parent.createNode("null", "null1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-2.73042, 5.23796))
hou_node.bypass(False)
hou_node.setDisplayFlag(False)
hou_node.hide(False)
hou_node.setHighlightFlag(False)
hou_node.setHardLocked(False)
hou_node.setSoftLocked(False)
hou_node.setSelectableTemplateFlag(False)
hou_node.setSelected(True)
hou_node.setRenderFlag(False)
hou_node.setTemplateFlag(False)
hou_node.setUnloadFlag(False)

hou_node.setExpressionLanguage(hou.exprLanguage.Hscript)

# Code to establish connections for /obj/cp_sop_source/null1
hou_node = hou_parent.node("null1")
if hou_parent.node("switch1") is not None:
    hou_node.setInput(0, hou_parent.node("switch1"), 0)
hou_node.setUserData("___Version___", "21.0.631")
if hasattr(hou_node, "syncNodeVersionIfNeeded"):
    hou_node.syncNodeVersionIfNeeded("21.0.631")
# Update the parent node.
hou_parent = hou_node


# Restore the parent and current nodes.
hou_parent = hou_parent.parent()
hou_node = hou_node.parent()



# Initialize parent node variable.
if locals().get("hou_parent") is None:
    hou_parent = hou.node("/obj/cp_sop_source")

# Code for /obj/cp_sop_source/output
hou_node = hou_parent.createNode("null", "output", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-2.73042, -1.44322))
hou_node.bypass(False)
hou_node.setDisplayFlag(True)
hou_node.hide(False)
hou_node.setHighlightFlag(False)
hou_node.setHardLocked(False)
hou_node.setSoftLocked(False)
hou_node.setSelectableTemplateFlag(False)
hou_node.setSelected(True)
hou_node.setRenderFlag(True)
hou_node.setTemplateFlag(False)
hou_node.setUnloadFlag(False)

hou_node.setExpressionLanguage(hou.exprLanguage.Hscript)

# Code to establish connections for /obj/cp_sop_source/output
hou_node = hou_parent.node("output")
if hou_parent.node("vellumpack1") is not None:
    hou_node.setInput(0, hou_parent.node("vellumpack1"), 0)
hou_node.setUserData("___Version___", "21.0.631")
if hasattr(hou_node, "syncNodeVersionIfNeeded"):
    hou_node.syncNodeVersionIfNeeded("21.0.631")
# Update the parent node.
hou_parent = hou_node


# Restore the parent and current nodes.
hou_parent = hou_parent.parent()
hou_node = hou_node.parent()



# Initialize parent node variable.
if locals().get("hou_parent") is None:
    hou_parent = hou.node("/obj/cp_sop_source")

# Code for /obj/cp_sop_source/switch1
hou_node = hou_parent.createNode("switch", "switch1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-2.72444, 6.40026))
hou_node.bypass(False)
hou_node.setDisplayFlag(False)
hou_node.hide(False)
hou_node.setHighlightFlag(False)
hou_node.setHardLocked(False)
hou_node.setSoftLocked(False)
hou_node.setSelectableTemplateFlag(False)
hou_node.setSelected(True)
hou_node.setRenderFlag(False)
hou_node.setTemplateFlag(False)
hou_node.setUnloadFlag(False)

hou_node.setExpressionLanguage(hou.exprLanguage.Hscript)

# Code to establish connections for /obj/cp_sop_source/switch1
hou_node = hou_parent.node("switch1")
if hou_parent.node("planarpatch1") is not None:
    hou_node.setInput(0, hou_parent.node("planarpatch1"), 0)
if hou_parent.node("grid1") is not None:
    hou_node.setInput(1, hou_parent.node("grid1"), 0)
hou_node.setUserData("___Version___", "21.0.631")
if hasattr(hou_node, "syncNodeVersionIfNeeded"):
    hou_node.syncNodeVersionIfNeeded("21.0.631")
# Update the parent node.
hou_parent = hou_node


# Restore the parent and current nodes.
hou_parent = hou_parent.parent()
hou_node = hou_node.parent()



# Initialize parent node variable.
if locals().get("hou_parent") is None:
    hou_parent = hou.node("/obj/cp_sop_source")

# Code for /obj/cp_sop_source/grid1
hou_node = hou_parent.createNode("grid", "grid1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(0.25391, 7.70978))
hou_node.bypass(False)
hou_node.setDisplayFlag(False)
hou_node.hide(False)
hou_node.setHighlightFlag(False)
hou_node.setHardLocked(False)
hou_node.setSoftLocked(False)
hou_node.setSelectableTemplateFlag(False)
hou_node.setSelected(True)
hou_node.setRenderFlag(False)
hou_node.setTemplateFlag(False)
hou_node.setUnloadFlag(False)

hou_node.setExpressionLanguage(hou.exprLanguage.Hscript)

hou_node.setUserData("___Version___", "21.0.631")
if hasattr(hou_node, "syncNodeVersionIfNeeded"):
    hou_node.syncNodeVersionIfNeeded("21.0.631")
# Update the parent node.
hou_parent = hou_node


# Restore the parent and current nodes.
hou_parent = hou_parent.parent()
hou_node = hou_node.parent()
