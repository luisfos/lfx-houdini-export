# this script doesn't need to be reloaded

# entry point for exportercallback
# get this to call exporter 
import lfx.exporter_callbacks as exporter_callbacks
# print(kwargs)
# TODO some point will need to differentiate between prism and base exporter
exporter_callbacks.convert_node(kwargs)