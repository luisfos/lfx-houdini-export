# ⚠️ Beta Warning
This repository is in progress and subject to change. Use at your own discretion.

# What is this?
Houdini utilities to provide convenience for IO operations.

# Why is it useful

# Problem
Nodes like the filecache SOP are great because they come with a handy versioning slider and clean interface.
But some ROPs only have a basic $HIP expression, you need to edit it each export. When the number of exports grows, it gets tedious.

# Solution
You can have a HDA to simplify the interface and standardise the output paths. That's great, so you make a HDA for geo, then alembic, then USD, then karma. Suddenly you have 20 HDAs to maintain and they might break next update.

This alternative is one common interface, added to any filepath parameter you want. You add the interface only when you need it.
For convenience it has default configurations depending on whether the node outputs geometry, alembic, images.

For the filestructure it follows the same convention as filecache, simply storing within the `$HIP` directory.
Autoversioning for easy exports, less time spent fiddling with filecaches, more time iterating.

Another big benefit is there's no dependency, we only adds spare parameters. Therefore the file can be shared and other users don't need this tool installed. 
No slow python calls

# key points
- non destructive parameters
- once spare parameters added, no dependency needed.
- config only affects how spare parameters are initialised
- QoL & convenience for vanilla houdini experience.
- default base folder exports within $HIP
- customisable config to your own preferences
- Compatible with FX, Indie & Educational?


# Prism versionning
For those using Prism pipeline, you can choose to export your files following the Prism file structure.
The interface handles autoversioning, comments, 


# MPlay Exporting and Convertor
In vanilla houdini exporting from MPlay can be fairly tedious. 
The tool adds a new Export menu, where you can quickly export any MPlay sequence, to a folder, keeping as an image sequence and video

- Export as image sequence / video / both
- Space-saving modern video codecs AV1 / H265 supported
- Autoversioning



