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


# Code for /obj/cp_sop_source/mountain1
hou_node = hou_parent.createNode("attribnoise::2.0", "mountain1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-5.06523, 1.7298))

# Code for /obj/cp_sop_source/mountain1/attribs parm 
hou_parm = hou_node.parm("attribs")
hou_parm.set("P")

# Code for /obj/cp_sop_source/mountain1/displace parm 
hou_parm = hou_node.parm("displace")
hou_parm.set(1)

# Code for /obj/cp_sop_source/mountain1/noiserange parm 
hou_parm = hou_node.parm("noiserange")
hou_parm.set("zcentered")

# Code for /obj/cp_sop_source/mountain1/amplitude parm 
hou_parm = hou_node.parm("amplitude")
hou_parm.set(0.25)

# Code for /obj/cp_sop_source/mountain1/fractal parm 
hou_parm = hou_node.parm("fractal")
hou_parm.set("hmfT")

# Code for /obj/cp_sop_source/mountain1/oct parm 
hou_parm = hou_node.parm("oct")
hou_parm.set(8)

# Code for /obj/cp_sop_source/mountain1/rough parm 
hou_parm = hou_node.parm("rough")
hou_parm.set(0.40000000000000002)

# Code for /obj/cp_sop_source/mountain1/remapramp2pos parm 
hou_parm = hou_node.parm("remapramp2pos")
hou_parm.set(1)

# Code for /obj/cp_sop_source/mountain1/remapramp2value parm 
hou_parm = hou_node.parm("remapramp2value")
hou_parm.set(1)

# Code to establish connections for /obj/cp_sop_source/mountain1
hou_node = hou_parent.node("mountain1")
if hou_parent.node("vellumpressure1") is not None:
    hou_node.setInput(0, hou_parent.node("vellumpressure1"), 0)

# Code for /obj/cp_sop_source/planarpatch1
hou_node = hou_parent.createNode("planarpatch", "planarpatch1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-4.45424, 7.70978))

# Code for /obj/cp_sop_source/vellumcloth1
hou_node = hou_parent.createNode("vellumconstraints", "vellumcloth1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-2.73042, 3.91586))

# Code for /obj/cp_sop_source/vellumcloth1/constrainttype parm 
hou_parm = hou_node.parm("constrainttype")
hou_parm.set("cloth")

# Code for /obj/cp_sop_source/vellumcloth1/domass parm 
hou_parm = hou_node.parm("domass")
hou_parm.set("on")

# Code for /obj/cp_sop_source/vellumcloth1/dothickness parm 
hou_parm = hou_node.parm("dothickness")
hou_parm.set("calcuniform")

# Code for /obj/cp_sop_source/vellumcloth1/stretchstiffness parm 
hou_parm = hou_node.parm("stretchstiffness")
hou_parm.set(6)

# Code for /obj/cp_sop_source/vellumcloth1/stretchstiffnessexp parm 
hou_parm = hou_node.parm("stretchstiffnessexp")
hou_parm.set("2")

# Code for /obj/cp_sop_source/vellumcloth1/dostretchgrp parm 
hou_parm = hou_node.parm("dostretchgrp")
hou_parm.set(1)

# Code for /obj/cp_sop_source/vellumcloth1/dobendgrp parm 
hou_parm = hou_node.parm("dobendgrp")
hou_parm.set(1)

# Code to establish connections for /obj/cp_sop_source/vellumcloth1
hou_node = hou_parent.node("vellumcloth1")
if hou_parent.node("null1") is not None:
    hou_node.setInput(0, hou_parent.node("null1"), 0)

# Code for /obj/cp_sop_source/vellumpressure1
hou_node = hou_parent.createNode("vellumconstraints", "vellumpressure1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-2.73042, 3.02166))

# Code for /obj/cp_sop_source/vellumpressure1/constrainttype parm 
hou_parm = hou_node.parm("constrainttype")
hou_parm.set("pressure")

# Code for /obj/cp_sop_source/vellumpressure1/stretchstiffness parm 
hou_parm = hou_node.parm("stretchstiffness")
hou_parm.set(6)

# Code for /obj/cp_sop_source/vellumpressure1/stretchstiffnessexp parm 
hou_parm = hou_node.parm("stretchstiffnessexp")
hou_parm.set("2")

# Code to establish connections for /obj/cp_sop_source/vellumpressure1
hou_node = hou_parent.node("vellumpressure1")
if hou_parent.node("vellumcloth1") is not None:
    hou_node.setInput(0, hou_parent.node("vellumcloth1"), 0)
if hou_parent.node("vellumcloth1") is not None:
    hou_node.setInput(1, hou_parent.node("vellumcloth1"), 1)
if hou_parent.node("vellumcloth1") is not None:
    hou_node.setInput(2, hou_parent.node("vellumcloth1"), 2)

# Code for /obj/cp_sop_source/null1
hou_node = hou_parent.createNode("null", "null1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-2.73042, 5.23796))

# Code to establish connections for /obj/cp_sop_source/null1
hou_node = hou_parent.node("null1")
if hou_parent.node("switch1") is not None:
    hou_node.setInput(0, hou_parent.node("switch1"), 0)
# Update the parent node.
hou_parent = hou_node

# Restore the parent and current nodes.
hou_parent = hou_parent.parent()
hou_node = hou_node.parent()

# Code for /obj/cp_sop_source/vellumpack1
hou_node = hou_parent.createNode("vellumpack", "vellumpack1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-2.73042, 0.659485))

# Code to establish connections for /obj/cp_sop_source/vellumpack1
hou_node = hou_parent.node("vellumpack1")
if hou_parent.node("mountain1") is not None:
    hou_node.setInput(0, hou_parent.node("mountain1"), 0)
if hou_parent.node("vellumpressure1") is not None:
    hou_node.setInput(1, hou_parent.node("vellumpressure1"), 1)

# Code for /obj/cp_sop_source/output
hou_node = hou_parent.createNode("null", "output", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-2.73042, -1.44322))
hou_node.setDisplayFlag(True)
hou_node.setRenderFlag(True)

# Code to establish connections for /obj/cp_sop_source/output
hou_node = hou_parent.node("output")
if hou_parent.node("vellumpack1") is not None:
    hou_node.setInput(0, hou_parent.node("vellumpack1"), 0)
# Update the parent node.
hou_parent = hou_node

# Restore the parent and current nodes.
hou_parent = hou_parent.parent()
hou_node = hou_node.parent()

# Code for /obj/cp_sop_source/switch1
hou_node = hou_parent.createNode("switch", "switch1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(-2.72444, 6.40026))

# Code to establish connections for /obj/cp_sop_source/switch1
hou_node = hou_parent.node("switch1")
if hou_parent.node("planarpatch1") is not None:
    hou_node.setInput(0, hou_parent.node("planarpatch1"), 0)
if hou_parent.node("grid1") is not None:
    hou_node.setInput(1, hou_parent.node("grid1"), 0)
# Update the parent node.
hou_parent = hou_node

# Restore the parent and current nodes.
hou_parent = hou_parent.parent()
hou_node = hou_node.parent()

# Code for /obj/cp_sop_source/grid1
hou_node = hou_parent.createNode("grid", "grid1", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(0.25391, 7.70978))

# Update the parent node.
hou_parent = hou_node

# Restore the parent and current nodes.
hou_parent = hou_parent.parent()
hou_node = hou_node.parent()
