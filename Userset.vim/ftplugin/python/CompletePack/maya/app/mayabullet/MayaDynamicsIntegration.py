"""
    MayaDynamicsIntegration - integration with the user interface for Maya's 
                              built-in Dynamics such as supporting Maya's fields
"""
import maya
maya.utils.loadStringResourcesForModule(__name__)


import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
from collections import defaultdict
import traceback, sys

kBulletRigidBodyShapeType = "bulletRigidBodyShape"
kBulletSoftBodyShapeType = "bulletSoftBodyShape"
kBulletSolverShapeType = "bulletSolverShape"

def findExisitingConnections(objects):
    '''
    In the case where we connect a field to a solver, we need to check if that
    field is already connected to any objects being handled by that solver. So, if
    we need to break those direct connections to prevent the field from affecting
    the same object twice. So, here we iterate over any solver objects and 
    build up a list of the objects they are solving and the fields that they are
    connected to.

    This function returns a tuple of:
    - solvers->fields->shapes the fields are connected to
    - solvers->connected fields

    We build these lists because, for large operations, it is more efficient
    '''
    solvers = [node for node in objects if cmds.nodeType(node) == kBulletSolverShapeType]

    node_connections = defaultdict(lambda : defaultdict(set))
    for solver in solvers:
        shapes = set()
        rigid_body_shapes = cmds.listConnections(solver, source=False, destination=True, 
                                                 sh=True, type=kBulletRigidBodyShapeType)
        soft_body_shapes  = cmds.listConnections(solver, source=False, destination=True, 
                                                 sh=True, type=kBulletSoftBodyShapeType )
        if rigid_body_shapes:
            shapes = shapes.union(set(rigid_body_shapes))
        if soft_body_shapes:
            shapes = shapes.union(set(soft_body_shapes))

        for shape in shapes:
            # find connected fields
            fields = cmds.listConnections('%s.fields' % shape, destination=False, 
                                          type="field")
            if fields:
                for field in fields:
                    node_connections[solver][field].add(shape)

    # Find all of the referenced solvers shapes and look for field connections            
    allowed = set([kBulletRigidBodyShapeType, kBulletSoftBodyShapeType])
    shapes = [node for node in objects if cmds.nodeType(node) in allowed]

    solver_connections = {}
    solvers = set(cmds.ls(type=kBulletSolverShapeType))
    for solver in solvers:
        fields = cmds.listConnections('%s.fields' % solver, 
                                      destination=False, type="field")
        solver_connections[solver] = set(fields) if fields else set()

    return node_connections, solver_connections

def connectFieldToShape(field, shape):
    '''
    Connect the given field to the given bullet shape
    '''
    try:
        # Find the next index to connect to. For some reason the nextAvailable 
        # flag on connectAttr does not work for this...
        selection_list = OpenMaya.MSelectionList()
        selection_list.clear()
        selection_list.add(shape)
        nodeFn = OpenMaya.MFnDependencyNode(selection_list.getDependNode(0))
        plug = nodeFn.findPlug(nodeFn.attribute('fields'), True)
        existing = set(plug.getExistingArrayAttributeIndices())
        next_index = 0
        while next_index in existing:
            next_index += 1
        cmds.connectAttr('%s.message' % field, '%s.fields[%d]' % (shape, next_index))
    except:
        raise RuntimeError(maya.stringTable['y_MayaDynamicsIntegration.kBulletUnableToConnectField'] % (shape, field))

def disconnectFieldFromShape(field, shape):
    '''
    Disconnect the given field from the given bullet shape
    '''
    try:
        selection_list = OpenMaya.MSelectionList()
        selection_list.clear()
        selection_list.add(field)
        selection_list.add(shape)
        nodeFn = OpenMaya.MFnDependencyNode(selection_list.getDependNode(0))
        shapeObj = selection_list.getDependNode(1)
        plug = nodeFn.findPlug(nodeFn.attribute('message'), True)
        shape_plugs = plug.connectedTo(False, True)
        for shape_plug in shape_plugs:
            if shape_plug.node() == shapeObj:
                cmds.disconnectAttr(plug.name(), shape_plug.name())
    except:
        pass

def solverForShape(shape):
    '''
    Get the solver for the given bullet shape
    '''
    try:
        return cmds.listConnections(shape, shapes=True, type=kBulletSolverShapeType)[0]
    except:
        return None

def makeConnections(bullet_shapes, fields):
    '''
    Make all of the required connections
    '''
    # Find all existing connections to objects that we might have to break
    shape_connections, solver_connections = findExisitingConnections(bullet_shapes)

    for shape in bullet_shapes:
        if cmds.nodeType(shape) == kBulletSolverShapeType:
            for field in fields:
                # When we connect a solver to a field, we need to check if
                # any of the solver's objects are connected to the field and
                # we need to break those connections
                connected_shapes = shape_connections[shape][field]
                for connected in connected_shapes:
                    try:
                        cmds.warning(
                            maya.stringTable['y_MayaDynamicsIntegration.kBulletDisconnectWarn' ] 
                            % (connected, field))
                        disconnectFieldFromShape(field, connected)
                    except:
                        cmds.warning(
                            maya.stringTable['y_MayaDynamicsIntegration.kBulletCouldNotDisconnect' ] 
                            % (connected, field))

                connectFieldToShape(field, shape) 
        else:
            # If we are connecting a field to an object, we need to see if
            # it is connected to the server already
            solver = solverForShape(shape)
            for field in fields:
                if field in solver_connections[solver]:
                    # The solver is connected, warn the user and skip 
                    # this connection
                    cmds.warning(
                        maya.stringTable['y_MayaDynamicsIntegration.kBulletSkipField' ] 
                         % field)
                    continue

                # Make the connection
                connectFieldToShape(field, shape)

def deleteConnections(bullet_shapes, fields):
    '''
    Delete all of the connections between the given fields and bullet shapes
    '''

    for shape in bullet_shapes:
        for field in fields:
            disconnectFieldFromShape(field, shape)
            

def collectBulletObjects(objects):
    ''' 
    Take the list of objects and find all Bullet shapes associated with them.

    In this case we are interested in shapes that can be affected by fields.
    '''
    result = []
    allowed = set([kBulletRigidBodyShapeType, 
                   kBulletSoftBodyShapeType,
                   kBulletSolverShapeType])

    # Look for allowed shapes as children of selected nodes
    for node in objects:
        if cmds.nodeType(node) in allowed:
            result.append(node)
        else:
            shapes = cmds.listRelatives(node, shapes=True, path=True)
            if shapes:
                result += [node for node in shapes if cmds.nodeType(node) in allowed]

    return result

connectDynamicCB_ID = None
# Detect Autodesk Maya 2014 Extension 1
try:
    strVersion = cmds.about( installedVersion=True ) 
    aVersion = strVersion.split(' ')
    gMayaVersion = float(aVersion[2])
    if gMayaVersion == 2014 and 'extension' in strVersion.lower():
        gMayaVersion = 2014.5
except:
    gMayaVersion = 2015

def addDynamicConnectHook():
    global connectDynamicCB_ID
    if connectDynamicCB_ID:
        removeDynamicConnectHook()
    if gMayaVersion>2014:
        connectDynamicCB_ID = cmds.connectDynamic(addScriptHandler=connectDynamicCB)

def removeDynamicConnectHook():
    global connectDynamicCB_ID
    if gMayaVersion>2014:
        cmds.connectDynamic(removeScriptHandler=connectDynamicCB_ID)

def connectDynamicCB(fields, emitters, collisionObjects, objects, delete):
    '''
    This is the callback that gets called when the 'connectDynamic' command
    is called. This callback looks for bullet shapes in the objects and 
    takes over if it finds some.
    '''
    try:
        bullet_shapes = collectBulletObjects(objects)
    
        if len(bullet_shapes) == 0:
            return False

        # We found bullet nodes, so we are going to take over

        if emitters and len(emitters) > 0:
            # We do not handle emitters. Warn the user and continue
            cmds.warning( maya.stringTable[ 'y_MayaDynamicsIntegration.kBulletConnectEmitter' ])
        
        if collisionObjects and len(collisionObjects) > 0:
            # We do not handle collision objects. Warn the user and continue
            cmds.warning(maya.stringTable[ 'y_MayaDynamicsIntegration.kBulletConnectCollision' ])

        if not fields or len(fields) == 0:
            raise RuntimeError(maya.stringTable[ 'y_MayaDynamicsIntegration.kBulletConnectNoField' ])

        if delete:
            deleteConnections(bullet_shapes, fields)
        else:
            makeConnections(bullet_shapes, fields)
        
        return True
    except:
        traceback.print_exc()

        # Return True even though we failed. We detected Bullet objects,
        # so we should be the ones handling this operation. If we returned
        # False, the connectDynamic command could do strange things like
        # turning meshes into Maya rigid bodies
        return True

# ===========================================================================
# Copyright 2016 Autodesk, Inc. All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# ===========================================================================
