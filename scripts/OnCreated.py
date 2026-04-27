# this script doesn't need to be reloaded
# entry point for exportercallback

# kwargs is predefined when this callback script runs, how do we get IDE to know this?
optype = str(kwargs['node'].type().nameWithCategory())    

# if optype isnt in this list then we just ignore it and do nothing, otherwise we will export it
BASE_NODE_PARMS: dict[str, str] = {
    "Driver/alembic": "filename",
    "Driver/geometry": "sopoutput",
    "Driver/ifd": "vm_picture",
    "Driver/karma": "picture",
    "Driver/octane_rop": "HO_img_fileName",
    "Driver/octanerendersetup": "HO_img_fileName",
    "Driver/opengl": "picture",
    "Driver/redshift_rop": "RS_outputFileNamePrefix",
    "Driver/rop_alembic": "filename",
    "Driver/rop_geometry": "sopoutput",
    "Driver/image": "copoutput",
    "Lop/karmarendersettings": "picture",
    "Lop/usd_rop": "lopoutput",
    "Lop/usdrender_rop": "outputimage",
    "Sop/file": "file",
    "Sop/filecache": "file",
    "Cop/file": "filename",
    "Cop/rop_image": "copoutput",
}

if optype in BASE_NODE_PARMS.keys():
    import lfx.exporter_callbacks as exporter_callbacks
    exporter_callbacks.convert_node(kwargs)
# print(kwargs)
# print("running onCreated")
# TODO some point will need to differentiate between prism and base exporter
# maybe in here actually we should check the prefs and then call the appropriate exporter callback