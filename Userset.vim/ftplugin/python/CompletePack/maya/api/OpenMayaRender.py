# Copyright 2012 Autodesk, Inc. All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk
# license agreement provided at the time of installation or download,
# or which otherwise accompanies this software in either electronic
# or hard copy form.

# This module has a dependency to OpenMaya:
import maya.api.OpenMaya

# See OpenMaya.py for an explanation of what we're doing here.
#
import maya.api._OpenMayaRender_py2

ourdict = globals()
py2dict = maya.api._OpenMayaRender_py2.__dict__

for (key, val) in py2dict.iteritems():
    if key not in ourdict:
        ourdict[key] = val
