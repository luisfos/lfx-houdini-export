def _set_clipboard_text(text: str) -> None:
	import hou  # type: ignore[import-not-found]

	if hasattr(hou.ui, "copyTextToClipboard"):
		hou.ui.copyTextToClipboard(text)
		return
	if hasattr(hou.ui, "setTextToClipboard"):
		hou.ui.setTextToClipboard(text)
		return

	raise AttributeError("No supported Houdini clipboard setter found on hou.ui")


def _get_clipboard_text() -> str:
	import hou  # type: ignore[import-not-found]

	if hasattr(hou.ui, "getTextFromClipboard"):
		return hou.ui.getTextFromClipboard() or ""
	if hasattr(hou.ui, "textFromClipboard"):
		return hou.ui.textFromClipboard() or ""

	raise AttributeError("No supported Houdini clipboard getter found on hou.ui")


def copy() -> None:
	import hou  # type: ignore[import-not-found]

	nodes = hou.selectedNodes()
	if not nodes:
		hou.ui.displayMessage("No nodes selected.")
		return

	parents = {node.parent() for node in nodes}
	if len(parents) != 1:
		hou.ui.displayMessage("Selected nodes must share the same parent.")
		return

	parent = next(iter(parents))
	parent_type = parent.type().name()

	code_blocks = [node.asCode(brief=True, recurse=True) for node in nodes]

	bootstrap = f"""import hou
__lf__parent_type = {parent_type!r}
hou_parent = locals().get(\"hou_parent\")
if hou_parent is None:
	pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
	ui_pwd = pane.pwd() if pane is not None else None
	if ui_pwd is not None and ui_pwd.type().name() == __lf__parent_type:
		hou_parent = ui_pwd
if hou_parent is None:
	raise hou.Error(\"parent of copied nodes does not match the context you are pasting into\")
"""

	text = bootstrap + "\n\n" + "\n\n".join(code_blocks).strip() + "\n"
	_set_clipboard_text(text)


def paste() -> None:
	import hou  # type: ignore[import-not-found]

	text = _get_clipboard_text()
	if not text.strip():
		hou.ui.displayMessage("Clipboard is empty.")
		return

	try:
		exec(text)
		pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
		if pane is not None:
			for meth in ("homeToSelection", "frameSelection", "homeToSelected"):
				fn = getattr(pane, meth, None)
				if callable(fn):
					try:
						fn()
					except TypeError:
						fn(True)
					break
	except Exception as exc:
		hou.ui.displayMessage(f"paste asCode failed: {exc}")


'''
example clipboard text
import hou
# Initialize parent node variable.
if locals().get("hou_parent") is None:
    hou_parent = hou.node("/obj/turb_amplitude")

if hou_parent is None:
    hou_parent = import importlib
import prism_callbacks
importlib.reload(prism_callbacks)
# Code for /obj/turb_amplitude/interpolate2
hou_node = hou_parent.createNode("attribwrangle", "interpolate2", run_init_scripts=False, load_contents=True, exact_type_name=True)
hou_node.move(hou.Vector2(25.8756, -29.3249))
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

# Code for /obj/turb_amplitude/interpolate2/snippet parm 
if locals().get("hou_node") is None:
    hou_node = hou.node("/obj/turb_amplitude/interpolate2")
hou_parm = hou_node.parm("snippet")
hou_parm.deleteAllKeyframes()
hou_parm.set("float t = @TimeInc;\nfloat b = 1.0;\nfloat s = rand(@ptnum,@Time);\nfloat s2 = rand(@ptnum-100,@Time-100);\nfloat s3 = rand(@ptnum-69,@Time-42);\n\n// keeps more points towards centre frame\n// less points on the boundaries between frames, so less visible step overlapping\nfloat bell(float u) // input 0-1\n{\n    float x = 2.0*u - 1.0;\n    float a = abs(x);\n    return 0.5 * ((x < 0.0 ? -a : a) * sqrt(a) + 1.0);\n}\n// s = bell(s);\n// s2 = bell(s2);\ns = (s-.5) *2.0 * b; // recentre -1 1\ns2 = (s2-.5) *2.*b;\ns3 = (s3-.5) *2.*b;\n\nfloat bias = s * t;\nf@bias = bias;\nvector oldv = v@v;\n\nv@P = v@P +\n     v@v * bias +\n     v@accel * bias * bias * .5 +\n     v@jerk * bias * bias * bias / 6.0;\n\n// diff seed for velocity bias helps avoid steps on simple cases\nbias = s2 * t;\nv@v = v@emitv +\n      v@emita * bias +\n      v@emitj * bias * bias * .5;\n      \n\nbias = s3 * t;\n// at this point our P has jittered but not with respect to the emit velocity\nv@P += v@v * bias;\n// f@dot = dot(normalize(oldv),normalize(v@v));\n")


hou_node.setColor(hou.Color([0.89, 0.412, 0.761]))
hou_node.setExpressionLanguage(hou.exprLanguage.Hscript)


'''