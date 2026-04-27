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


# Pass 3b deny-list: single-line calls that are either default-value no-ops,
# version bookkeeping, or cosmetic state we never want to reproduce on paste.
_STRIP_LINES: frozenset[str] = frozenset({
	# flag calls — only False values land here; True values are intentional
	"hou_node.hide(False)",
	"hou_node.bypass(False)",
	"hou_node.setDisplayFlag(False)",
	"hou_node.setRenderFlag(False)",
	"hou_node.setTemplateFlag(False)",
	"hou_node.setSelectableTemplateFlag(False)",
	"hou_node.setHighlightFlag(False)",
	"hou_node.setHardLocked(False)",
	"hou_node.setSoftLocked(False)",
	"hou_node.setUnloadFlag(False)",
	# Hscript is the default expression language
	'hou_node.setExpressionLanguage(hou.exprLanguage.Hscript)',
	# selection state — not meaningful on paste (confusing alongside existing selection)
	'hou_node.setSelected(True)',
	# fresh nodes have no keyframes — deleteAllKeyframes() is always a no-op on paste
	'hou_parm.deleteAllKeyframes()',
})


def _clean_ascode(code: str) -> str:
	import re
	import hou  # type: ignore[import-not-found]

	# Pass 1 — strip dead hou_parent re-init block
	code = re.sub(
		r'# Initialize parent node variable\.\n'
		r'if locals\(\)\.get\("hou_parent"\) is None:\n'
		r'    hou_parent = hou\.node\("[^"]*"\)\n',
		"",
		code,
	)

	# Pass 2 — strip dead hou_node guard inside parm blocks
	code = re.sub(
		r'if locals\(\)\.get\("hou_node"\) is None:\n'
		r'    hou_node = hou\.node\("[^"]*"\)\n',
		"",
		code,
	)

	# Pass 3a — strip 2-line syncNodeVersionIfNeeded block
	code = re.sub(
		r'if hasattr\(hou_node, "syncNodeVersionIfNeeded"\):\n'
		r'    hou_node\.syncNodeVersionIfNeeded\("[^"]*"\)\n?',
		"",
		code,
	)

	# Pass 3b — strip single-line boilerplate deny-list
	lines = []
	for line in code.splitlines():
		if line.strip() not in _STRIP_LINES:
			lines.append(line)
	code = "\n".join(lines)

	# Pass 3c — strip setUserData() calls whose key is wrapped in ___ (Houdini internal
	# metadata such as ___Version___, ___toolid___, ___toolcount___). The exact-match
	# deny-list can't cover all variants, so use a regex across the whole line.
	code = re.sub(
		r'^hou_node\.setUserData\("___[^"]*___"[^\n]*\n?',
		'',
		code,
		flags=re.MULTILINE,
	)

	# Pass 4a — strip entire parm blocks for folder/tab-visibility parms.
	# These control which tab is open in the parameter editor — purely cosmetic;
	# the node will open to its default tab on paste, which is fine.
	_FOLDER_NAME_RE = re.compile(r'/folder\d* parm\s*$')
	blocks = re.split(r'\n{2,}', code)
	kept = []
	for block in blocks:
		if not block.strip():
			continue
		if _FOLDER_NAME_RE.search(block.strip().splitlines()[0]):
			continue
		kept.append(block.strip())
	code = "\n\n".join(kept)

	# Pass 4b — strip entire parm blocks whose value is at default.
	# Relies on hou.node() being resolvable at copy time (nodes still exist).
	_PARM_BLOCK_RE = re.compile(
		r'^# Code for (/.+)/([^/\s]+) parm\s*$'
	)
	blocks = re.split(r'\n{2,}', code)
	kept = []
	for block in blocks:
		if not block.strip():
			continue
		block_lines = block.strip().splitlines()
		m = _PARM_BLOCK_RE.match(block_lines[0])
		if m:
			node_path, parm_name = m.group(1), m.group(2)
			try:
				node = hou.node(node_path)
				if node is not None:
					# try parm first, fall back to parmTuple
					p = node.parm(parm_name)
					if p is not None:
						if p.isAtDefault():
							continue
					else:
						pt = node.parmTuple(parm_name)
						if pt is not None and all(c.isAtDefault() for c in pt):
							continue
			except Exception:
				pass
		kept.append(block.strip())
	code = "\n\n".join(kept)

	# Pass 6b — strip "Update the parent node" line emitted after each node's connection
	# block. These two patterns appear independently so are matched separately.
	code = re.sub(
		r'# Update the parent node\.\n'
		r'hou_parent = hou_node\n?',
		'',
		code,
	)
	# Pass 6b (cont.) — strip "Restore the parent and current nodes" block
	code = re.sub(
		r'# Restore the parent and current nodes\.\n'
		r'hou_parent = hou_parent\.parent\(\)\n'
		r'hou_node = hou_node\.parent\(\)\n?',
		'',
		code,
	)

	# Pass 5 — collapse 3+ blank lines to 2
	code = re.sub(r'\n{3,}', '\n\n', code)

	return code


def _clean_connections(code: str) -> str:
	import re

	# Step 1 — defer all connection blocks to the end so that setInput() calls only
	# run after every node has been created, regardless of asCode() emission order.
	_CONN_HEADER_RE = re.compile(r'^# Code to establish connections for ')
	blocks = [b.strip() for b in re.split(r'\n{2,}', code) if b.strip()]
	node_blocks = [b for b in blocks if not _CONN_HEADER_RE.match(b)]
	conn_blocks = [b for b in blocks if _CONN_HEADER_RE.match(b)]
	code = "\n\n".join(node_blocks + conn_blocks)

	# Step 2 — build a name→stable-variable map from every createNode call in the
	# joined text. Needs full visibility across all nodes, which is why this runs here
	# rather than inside _clean_ascode (which is per-node).
	_CREATE_RE = re.compile(
		r'(hou_node = hou_parent\.createNode\("[^"]+",\s*"([^"]+)"[^\n]*)'
	)
	name_to_var = {
		name: "_lf_" + re.sub(r'\W', '_', name)
		for _, name in _CREATE_RE.findall(code)
	}

	if name_to_var:
		# Step 3a — insert `_lf_<name> = hou_node` after each createNode line
		def _insert_capture(m: re.Match) -> str:
			var = name_to_var[m.group(2)]
			return m.group(1) + f"\n{var} = hou_node  # stable ref, immune to Houdini rename-for-uniqueness"
		code = _CREATE_RE.sub(_insert_capture, code)

		# Step 3b — strip `if hou_parent.node("xxx") is not None:` guards;
		# after capture the variable is always set, so the guard is always true.
		code = re.sub(
			r'^if hou_parent\.node\("[^"]+"\) is not None:\n((?:    .+\n?)+)',
			lambda m: re.sub(r'^    ', '', m.group(1), flags=re.MULTILINE),
			code,
			flags=re.MULTILINE,
		)

		# Step 3c — replace all hou_parent.node("xxx") lookups (in setInput and
		# hou_node reassignments) with the stable variable.
		for name, var in name_to_var.items():
			code = code.replace(f'hou_parent.node("{name}")', var)

	return code


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

	code_blocks = [_clean_ascode(node.asCode(brief=True, recurse=True)) for node in nodes]

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

	joined = _clean_connections("\n\n".join(code_blocks).strip())
	text = bootstrap + "\n\n" + joined + "\n"
	_set_clipboard_text(text)


def paste() -> None:
	import re
	import hou  # type: ignore[import-not-found]

	text = _get_clipboard_text()
	if not text.strip():
		hou.ui.displayMessage("Clipboard is empty.")
		return

	try:
		# Identify the expected parent network type from the bootstrap marker so we
		# know what kind of temp container to create.
		_type_m = re.search(r"^__lf__parent_type\s*=\s*'([^']+)'", text, re.MULTILINE)
		parent_type = _type_m.group(1) if _type_m else None

		pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
		real_parent = pane.pwd() if pane is not None else None

		temp = None
		new_nodes = None

		if (
			parent_type
			and real_parent is not None
			and real_parent.type().name() == parent_type
		):
			container_parent = real_parent.parent()
			if container_parent is not None:
				try:
					# Create a temp network of the same type. Nodes are built inside it
					# first, then copied as a group into real_parent. Houdini remaps
					# internal path references (e.g. "../flow_block_end1") during the
					# group copy, solving both the name-collision and path-mismatch problems.
					temp = container_parent.createNode(parent_type, "__lf_copypaste_tmp__")
				except Exception:
					temp = None

		if temp is not None:
			# Pass hou_parent so the bootstrap skips its own pane lookup and targets temp
			_globs: dict = {"__builtins__": __builtins__, "hou": hou}
			_locs: dict = {"hou_parent": temp}
			exec(text, _globs, _locs)  # noqa: S102
			children = temp.children()
			if children:
				new_nodes = hou.copyNodesTo(children, real_parent)
			temp.destroy()
		else:
			exec(text)  # noqa: S102

		if pane is not None:
			if new_nodes:
				for i, node in enumerate(new_nodes):
					node.setSelected(True, clear_all_selected=(i == 0))
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