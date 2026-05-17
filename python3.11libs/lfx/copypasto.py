import base64


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


def copy_asData(selection: list = None, compression: bool = False) -> None:
	'''
	instead of relying on asCode, we use asData which is more modern but
	might require more handling on the paste side.
	'''
	import hou
	if selection is None:
		selection = hou.selectedItems()
		data = hou.selectedItemsAsData()
	else:
		data = hou.itemsAsData(selection)

	# get the parent, check the type. ensure when we paste we are in the same type of network
	parent = selection[0].parent()

	first_position = list(selection[0].position())

	import json	
	if compression:
		import zlib
		import base64
		compressed_data = zlib.compress(json.dumps(data, separators=(',', ':')).encode('utf-8'), level=9)
		data = base64.b64encode(compressed_data).decode('ascii')

	# store the data dict in the clipboard as a string
	envelope = json.dumps({
		"lfx_format": "asData_v1",
		"parent_type": parent.childTypeCategory().name(),
		"data": data,
		"first_position": first_position,
		"compression": compression,
	})
	_set_clipboard_text(json.dumps(envelope))


def paste_asData() -> None:
	import hou
	import json

	text = _get_clipboard_text()
	if not text.strip():
		hou.ui.displayMessage("Clipboard is empty.")
		return

	
	envelope = json.loads(text)
	if isinstance(envelope, str):
		envelope = json.loads(envelope)  # handle double-encoded string

	if not isinstance(envelope, dict) or not envelope.get("lfx_format"):
		hou.ui.displayMessage("Clipboard info not as expected.")
		return

	parent_type = envelope.get("parent_type")
	data = envelope.get("data")

	if envelope.get("compression", False):
		import zlib
		import base64
		data = json.loads(zlib.decompress(base64.b64decode(data)).decode('utf-8'))

	pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
	target_parent = pane.pwd() 
	c_pos = pane.visibleBounds().center()
	offset = c_pos - hou.Vector2(envelope.get("first_position", (0, 0)))
	


	if target_parent.childTypeCategory().name() != parent_type:
		hou.ui.displayMessage(
			f"Current context is not compatible with copied data (expected parent type: {parent_type})."
		)
		return

	# hou.copyNodesFromData(data, target_parent)
	hou.createItemsFromData(target_parent,data, offset_position=offset )
