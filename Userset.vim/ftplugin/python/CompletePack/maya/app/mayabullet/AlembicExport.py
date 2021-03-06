"""
BulletBaking - Python module containing bullet baking commands
	for use with MayaBullet.

"""
# Python
import maya
maya.utils.loadStringResourcesForModule(__name__)

import os
import re
import types
# Maya
import maya.cmds
import maya.mel
import maya.api.OpenMaya as OpenMaya

# MayaBullet
import maya.app.mayabullet.BulletUtils as BulletUtils
import CommandWithOptionVars
from maya.app.mayabullet import logger
from maya.app.mayabullet.Trace import Trace

############################### Global Variables ###########################
gAbcBulletExportLastDirectory=""
gAbcBulletExportLastWorkspace=""

############################### BulletExport ###############################

@Trace()
def containsWhiteSpace(str):
	pattern = re.compile(r'\s+')
	return pattern.match(str)

@Trace()
def setOptionVars(forceFactorySettings=False):

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportCacheTimeRanges") :
		maya.cmds.optionVar( clearArray="Alembic_exportCacheTimeRanges" )
		maya.cmds.optionVar( intValueAppend=["Alembic_exportCacheTimeRanges", 2])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportStarts") :
		maya.cmds.optionVar( clearArray="Alembic_exportStarts" )
		maya.cmds.optionVar( floatValueAppend=["Alembic_exportStarts", 1] )

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportEnds") :
		maya.cmds.optionVar( clearArray="Alembic_exportEnds" )
		maya.cmds.optionVar( floatValueAppend=["Alembic_exportEnds", 10])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportEvaluateEverys") :
		maya.cmds.optionVar( clearArray="Alembic_exportEvaluateEverys" )
		maya.cmds.optionVar( floatValueAppend=["Alembic_exportEvaluateEverys", 1])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportEnableFrameRelativeSamples") :
		maya.cmds.optionVar( clearArray="Alembic_exportEnableFrameRelativeSamples" )
		maya.cmds.optionVar( intValueAppend=["Alembic_exportEnableFrameRelativeSamples", 0])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportLowFrameRelativeSamples") :
		maya.cmds.optionVar( clearArray="Alembic_exportLowFrameRelativeSamples" )
		maya.cmds.optionVar( floatValueAppend=["Alembic_exportLowFrameRelativeSamples", -0.2])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportHighFrameRelativeSamples") :
		maya.cmds.optionVar( clearArray="Alembic_exportHighFrameRelativeSamples" )
		maya.cmds.optionVar( floatValueAppend=["Alembic_exportHighFrameRelativeSamples", 0.2])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportEnablePreRoll") :
		maya.cmds.optionVar( intValue=["Alembic_exportEnablePreRoll", 0])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportPreRollStartFrame") :
		maya.cmds.optionVar( floatValue=["Alembic_exportPreRollStartFrame", 0])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportAttr") :
		maya.cmds.optionVar( stringValue=["Alembic_exportAttr", ""])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportAttrPrefix") :
		maya.cmds.optionVar( stringValue=["Alembic_exportAttrPrefix", ""])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportVerbose") :
		maya.cmds.optionVar( intValue=["Alembic_exportVerbose", 0])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportNoNormals") :
		maya.cmds.optionVar( intValue=["Alembic_exportNoNormals", 0])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportRenderableOnly") :
		maya.cmds.optionVar( intValue=["Alembic_exportRenderableOnly", 0])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportStripNamespaces") :
		maya.cmds.optionVar( intValue=["Alembic_exportStripNamespaces", 0])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportUVWrite") :
		maya.cmds.optionVar( intValue=["Alembic_exportUVWrite", 0])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportWholeFrameGeo") :
		maya.cmds.optionVar( intValue=["Alembic_exportWholeFrameGeo", 0])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportWorldSpace") :
		maya.cmds.optionVar( intValue=["Alembic_exportWorldSpace", 0])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportWriteVisibility") :
		maya.cmds.optionVar( intValue=["Alembic_exportWriteVisibility", 0])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportPerFrameCallbackMel") :
		maya.cmds.optionVar( stringValue=["Alembic_exportPerFrameCallbackMel", ""])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportPostJobCallbackMel") :
		maya.cmds.optionVar( stringValue=["Alembic_exportPostJobCallbackMel", ""])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportPerFrameCallbackPython") :
		maya.cmds.optionVar( stringValue=["Alembic_exportPerFrameCallbackPython", ""])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportPostJobCallbackPython") :
		maya.cmds.optionVar( stringValue=["Alembic_exportPostJobCallbackPython", ""])

	# version 2
	#
	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportFilterEulerRotations") :
		maya.cmds.optionVar( intValue=["Alembic_exportFilterEulerRotations", 0])

	# version 3
	#
	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportWriteColorSets") :
		maya.cmds.optionVar( intValue=["Alembic_exportWriteColorSets", 0])

	if forceFactorySettings or not maya.cmds.optionVar(exists="Alembic_exportWriteFaceSets") :
		maya.cmds.optionVar( intValue=["Alembic_exportWriteFaceSets", 0])

	# version 4
	#
	if (forceFactorySettings or not bool(maya.cmds.optionVar(exists="Alembic_exportDataFormat"))) :
		maya.cmds.optionVar( intValue=["Alembic_exportDataFormat", 2])
	

	# version 5
	#
	if (forceFactorySettings or not bool(maya.cmds.optionVar(exists="Alembic_exportPreRollStep"))) :
		maya.cmds.optionVar( floatValue=["Alembic_exportPreRollStep", 1])
	
	# version 6
	#
	if (forceFactorySettings or not bool(maya.cmds.optionVar(exists="Alembic_exportWriteCreases"))) :
		maya.cmds.optionVar( intValue=["Alembic_exportWriteCreases", 0])
	
@Trace()
def captureAlembicExportOptionVars(*args, **kw):
	version = args[0]

	setOptionVars(0)

	cacheTimeRanges			= maya.cmds.optionVar(q="Alembic_exportCacheTimeRanges")
	startFrames				= maya.cmds.optionVar(q="Alembic_exportStarts")
	endFrames				= maya.cmds.optionVar(q="Alembic_exportEnds")
	evaluateEvery			= maya.cmds.optionVar(q="Alembic_exportEvaluateEverys")
	enableSample			= maya.cmds.optionVar(q="Alembic_exportEnableFrameRelativeSamples")
	lowFrameRelativeSamples	= maya.cmds.optionVar(q="Alembic_exportLowFrameRelativeSamples")
	highFrameRelativeSamples= maya.cmds.optionVar(q="Alembic_exportHighFrameRelativeSamples")
	enablePreRoll			= maya.cmds.optionVar(q="Alembic_exportEnablePreRoll")
	preRollStartFrame		= maya.cmds.optionVar(q="Alembic_exportPreRollStartFrame")
	attr					= maya.cmds.optionVar(q="Alembic_exportAttr")
	attrPrefix				= maya.cmds.optionVar(q="Alembic_exportAttrPrefix")
	verbose					= maya.cmds.optionVar(q="Alembic_exportVerbose")
	noNormals				= maya.cmds.optionVar(q="Alembic_exportNoNormals")
	renderableOnly			= maya.cmds.optionVar(q="Alembic_exportRenderableOnly")
	stripNamespaces			= maya.cmds.optionVar(q="Alembic_exportStripNamespaces")
	uvWrite					= maya.cmds.optionVar(q="Alembic_exportUVWrite")
	wholeFrameGeo			= maya.cmds.optionVar(q="Alembic_exportWholeFrameGeo")
	worldSpace				= maya.cmds.optionVar(q="Alembic_exportWorldSpace")
	writeVisibility			= maya.cmds.optionVar(q="Alembic_exportWriteVisibility")
	perFrameCallbackMel		= maya.cmds.optionVar(q="Alembic_exportPerFrameCallbackMel")
	postJobCallbackMel		= maya.cmds.optionVar(q="Alembic_exportPostJobCallbackMel")
	perFrameCallbackPython	= maya.cmds.optionVar(q="Alembic_exportPerFrameCallbackPython")
	postJobCallbackPython	= maya.cmds.optionVar(q="Alembic_exportPostJobCallbackPython")

	optionArgs = [
		exportAll,
		cacheTimeRanges,
		startFrames,
		endFrames,
		evaluateEvery,
		enableSample,
		lowFrameRelativeSamples,
		highFrameRelativeSamples,
		enablePreRoll,
		preRollStartFrame,
		attr,
		attrPrefix,
		verbose,
		noNormals,
		renderableOnly,
		stripNamespaces,
		uvWrite,
		wholeFrameGeo,
		worldSpace,
		writeVisibility,
		perFrameCallbackMel,
		postJobCallbackMel,
		perFrameCallbackPython,
		postJobCallbackPython
		]

	if (version >= 2) :
		filterEulerRotations	= maya.cmds.optionVar(q="Alembic_exportFilterEulerRotations")

		optionArgs.append(str(filterEulerRotations))

	if (version >= 3) :
		writeColorSets	  = maya.cmds.optionVar(q="Alembic_exportWriteColorSets")
		writeFaceSets	   = maya.cmds.optionVar(q="Alembic_exportWriteFaceSets")

		optionArgs.append(writeColorSets)
		optionArgs.append(writeFaceSets)

	if (version >= 4) :
		dataFormat = maya.cmds.optionVar(q="Alembic_exportDataFormat")

		optionArgs.append(dataFormat)

	if (version >= 5) :
		preRollStep = maya.cmds.optionVar(q="Alembic_exportPreRollStep")

		optionArgs.append(preRollStep)

	if (version >= 6) :
		writeCreases = maya.cmds.optionVar(q="Alembic_exportWriteCreases")

		optionArgs.append(writeCreases)

	return optionArgs

@Trace()
def syncOptionVars(versionNum, args):

	cacheTimeRanges			= args[1] if len(args)>1 and args[1] else []
	startFrames				= args[2] if len(args)>2 and args[2] else []
	endFrames				= args[3] if len(args)>3 and args[3] else []
	evaluateEvery			= args[4] if len(args)>4 and args[4] else []
	enableSample			= args[5] if len(args)>5 and args[5] else []
	lowFrameRelativeSamples	= args[6] if len(args)>6 and args[6] else []
	highFrameRelativeSamples= args[7] if len(args)>7 and args[7] else []

	enablePreRoll			= args[8] if len(args)>8 else None
	preRollStartFrame		= args[9] if len(args)>9 else None
	attr					= args[10] if len(args)>10 else None
	attrPrefix				= args[11] if len(args)>11 else None
	verbose					= args[12] if len(args)>12 else None
	noNormals				= args[13] if len(args)>13 else None
	renderableOnly			= args[14] if len(args)>14 else None
	stripNamespaces			= args[15] if len(args)>15 else None
	uvWrite					= args[16] if len(args)>16 else None
	wholeFrameGeo			= args[17] if len(args)>17 else None
	worldSpace				= args[18] if len(args)>18 else None
	writeVisibility			= args[19] if len(args)>19 else None
	perFrameCallbackMel		= args[20] if len(args)>20 else None
	postJobCallbackMel		= args[21] if len(args)>21 else None
	perFrameCallbackPython	= args[22] if len(args)>22 else None
	postJobCallbackPython	= args[23] if len(args)>23 else None

	for i, (tmpRangeMode, tmpStart, tmpEnd, tmpEvaluateEvery,tmpEnableSample,tmpLowSample, tmpHighSample) \
		in enumerate(zip(cacheTimeRanges, startFrames, endFrames, evaluateEvery, enableSample, lowFrameRelativeSamples, highFrameRelativeSamples)):

		if i==0:
			maya.cmds.optionVar( clearArray="Alembic_exportCacheTimeRanges" )
			maya.cmds.optionVar( clearArray="Alembic_exportStarts" )
			maya.cmds.optionVar( clearArray="Alembic_exportEnds" )
			maya.cmds.optionVar( clearArray="Alembic_exportEvaluateEverys" )
			maya.cmds.optionVar( clearArray="Alembic_exportEnableFrameRelativeSamples" )
			maya.cmds.optionVar( clearArray="Alembic_exportLowFrameRelativeSamples" )
			maya.cmds.optionVar( clearArray="Alembic_exportHighFrameRelativeSamples" )

		maya.cmds.optionVar( intValueAppend=	["Alembic_exportCacheTimeRanges",            int(tmpRangeMode)])
		maya.cmds.optionVar( floatValueAppend=	["Alembic_exportStarts",                     float(tmpStart)])
		maya.cmds.optionVar( floatValueAppend=	["Alembic_exportEnds",                       float(tmpEnd)])
		maya.cmds.optionVar( floatValueAppend=	["Alembic_exportEvaluateEverys",             float(tmpEvaluateEvery)])
		maya.cmds.optionVar( intValueAppend=	["Alembic_exportEnableFrameRelativeSamples", int(tmpEnableSample)])
		maya.cmds.optionVar( floatValueAppend=	["Alembic_exportLowFrameRelativeSamples",    float(tmpLowSample)])
		maya.cmds.optionVar( floatValueAppend=	["Alembic_exportHighFrameRelativeSamples",   float(tmpHighSample)])

	if enablePreRoll:
		maya.cmds.optionVar( intValue=		["Alembic_exportEnablePreRoll",			int(enablePreRoll)])
	if preRollStartFrame:
		maya.cmds.optionVar( floatValue=	["Alembic_exportPreRollStartFrame",		float(preRollStartFrame)])
	if attr:
		maya.cmds.optionVar( stringValue=	["Alembic_exportAttr",					attr])
	if attrPrefix:
		maya.cmds.optionVar( stringValue=	["Alembic_exportAttrPrefix",			attrPrefix])
	if verbose:
		maya.cmds.optionVar( intValue=		["Alembic_exportVerbose",				int(verbose)])
	if noNormals:
		maya.cmds.optionVar( intValue=		["Alembic_exportNoNormals",				int(noNormals)])
	if renderableOnly:
		maya.cmds.optionVar( intValue=		["Alembic_exportRenderableOnly",		int(renderableOnly)])
	if stripNamespaces:
		maya.cmds.optionVar( intValue=		["Alembic_exportStripNamespaces",		int(stripNamespaces)])
	if uvWrite:
		maya.cmds.optionVar( intValue=		["Alembic_exportUVWrite",				int(uvWrite)])
	if wholeFrameGeo:
		maya.cmds.optionVar( intValue=		["Alembic_exportWholeFrameGeo",			int(wholeFrameGeo)])
	if worldSpace:
		maya.cmds.optionVar( intValue=		["Alembic_exportWorldSpace",			int(worldSpace)])
	if writeVisibility:
		maya.cmds.optionVar( intValue=		["Alembic_exportWriteVisibility",		int(writeVisibility)])
	if perFrameCallbackMel:
		maya.cmds.optionVar( stringValue=	["Alembic_exportPerFrameCallbackMel",	perFrameCallbackMel])
	if postJobCallbackMel:
		maya.cmds.optionVar( stringValue=	["Alembic_exportPostJobCallbackMel",	postJobCallbackMel])
	if perFrameCallbackPython:
		maya.cmds.optionVar( stringValue=	["Alembic_exportPerFrameCallbackPython",perFrameCallbackPython])
	if postJobCallbackPython:
		maya.cmds.optionVar( stringValue=	["Alembic_exportPostJobCallbackPython",	postJobCallbackPython])

	if (versionNum >= 2) :
		filterEulerRotations	= args[24] if len(args)>24 else None
		if filterEulerRotations:
			maya.cmds.optionVar( intValue=	["Alembic_exportFilterEulerRotations",	filterEulerRotations])

	if (versionNum >= 3) :
		writeColorSets		= args[25] if len(args)>25 else None
		writeFaceSets		= args[26] if len(args)>26 else None
		if writeColorSets:
			maya.cmds.optionVar( intValue=	["Alembic_exportWriteColorSets",	writeColorSets])
		if writeFaceSets:
			maya.cmds.optionVar( intValue=	["Alembic_exportWriteFaceSets",		writeFaceSets])

	if (versionNum >= 4):
		dataFormat = args[27] if len(args)>25 else None
		if dataFormat:
			maya.cmds.optionVar( intValue=	["Alembic_exportDataFormat",		dataFormat])

	if (versionNum >= 5):
		preRollStep = args[28]
		if preRollStep:
			maya.cmds.optionVar( floatValue=	["Alembic_exportPreRollStep",		preRollStep])

	if (versionNum >= 6):
		writeCreases = args[29]
		if writeCreases:
			maya.cmds.optionVar( intValue=	["Alembic_exportWriteCreases",		writeCreases])

@Trace()
def getObjectsToExport(*args, **kw):
	result = set([])

	sl = kw['sl'] if kw.has_key('sl') else False
	slist = maya.cmds.ls( sl=sl, long=True )

	# filter rigid sets
	rbSets = maya.cmds.ls( slist, type='bulletRigidSet' )

	for rbSet in rbSets:
		# get initial state
		rbInitialState = maya.cmds.listConnections( '{0}.usedBy'.format(rbSet), sh=True, t='bulletInitialState')
		if  rbInitialState:
			# get solved state
			rbSolvedState = maya.cmds.listConnections( '{0}.solvedState'.format(rbInitialState[0]), sh=True, t='bulletRigidCollection')
			if  rbSolvedState:
				result.add(rbSolvedState[0])

	# filter rigid solved states
	rbSolvedStates = maya.cmds.ls( slist, type='bulletRigidCollection' )
	result = result.union(set(rbSolvedStates))

	# filter rigid body shapes
	trans = maya.cmds.ls( slist, transforms=True )
	if trans and len(trans):
		rbShapes = maya.cmds.listRelatives( trans, c=True, type='bulletRigidBodyShape' )
		if rbShapes and len(rbShapes):
			rbTrans = maya.cmds.listRelatives( rbShapes, p=True )
			if rbTrans and len(rbTrans):
				result = result.union(set(rbTrans))

	return result

@Trace()
def doExportArgList(*args, **kw):
	# back up the current option values so that we can restore
	# them later if the dialog is cancelled
	exportAll = kw['exportAll'] if kw.has_key('exportAll') else False
	version = kw['version'] if kw.has_key('version') else 1

	optionVarsBackup = captureAlembicExportOptionVars(version, exportAll)

	# synchronize the option values with the argument list
	syncOptionVars(version, args)

	# prepare filter and starting dir for file dialog
	filter = maya.stringTable['y_AlembicExport.kAlembic'] + " (*.abc);;" + maya.stringTable['y_AlembicExport.kAllFiles'] + " (*.*)"
	if (len(maya.cmds.workspace(fileRuleEntry='alembicCache')) == 0) :
		maya.cmds.workspace( fileRule=["alembicCache","cache/alembic"] )
		maya.cmds.workspace( saveWorkspace=True )
		
	workspace = maya.cmds.workspace( fileRuleEntry='alembicCache')
	workspace = maya.cmds.workspace( expandName=workspace )
	maya.cmds.sysFile( workspace, makeDir=True )

	global gAbcBulletExportLastDirectory
	global gAbcBulletExportLastWorkspace
	startingDir = gAbcBulletExportLastDirectory
	if (len(startingDir) == 0 or gAbcBulletExportLastWorkspace != maya.cmds.workspace(q=True, rootDirectory=True)) :
		startingDir = workspace

	# choose a file to export
	result=[]
	if (exportAll) :
		result = maya.cmds.fileDialog2(\
					returnFilter=1,
					fileFilter=filter,
					caption=maya.stringTable['y_AlembicExport.kExportAll2'],
					startingDirectory=startingDir,
					fileMode=0,
					okCaption=maya.stringTable['y_AlembicExport.kExportAll3'],
					optionsUICreate="Alembic_exportFileOptionsUICreate",
					optionsUIInit="Alembic_exportFileOptionsUIInit",
					optionsUICommit="Alembic_exportAllFileOptionsUICommit"
					)
	else:
		result = maya.cmds.fileDialog2(
					returnFilter=1,
					fileFilter=filter,
					caption=maya.stringTable['y_AlembicExport.kExportSelection2'],
					startingDirectory=startingDir,
					fileMode=0,
					okCaption=maya.stringTable['y_AlembicExport.kExportSelection3'],
					optionsUICreate="Alembic_exportFileOptionsUICreate",
					optionsUIInit="Alembic_exportFileOptionsUIInit",
					optionsUICommit="Alembic_exportSelectionFileOptionsUICommit",
					)

	if (not result or len(result) == 0 or len(result[0]) == 0) :
		# cancelled
		# Restore optionVars to the state before this procedure is called
		#
		syncOptionVars(version, optionVarsBackup)
		return


	# Save the last directory
	gAbcBulletExportLastDirectory = os.path.dirname(result[0])
	gAbcBulletExportLastWorkspace = maya.cmds.workspace(q=True, rootDirectory=True)

	# parameters
	cacheTimeRanges				= maya.cmds.optionVar(q='Alembic_exportCacheTimeRanges')
	startFrames					= maya.cmds.optionVar(q='Alembic_exportStarts')
	endFrames					= maya.cmds.optionVar(q='Alembic_exportEnds')
	evaluateEverys				= maya.cmds.optionVar(q='Alembic_exportEvaluateEverys')
	enableSamples				= maya.cmds.optionVar(q='Alembic_exportEnableFrameRelativeSamples')
	lowFrameRelativeSamples		= maya.cmds.optionVar(q='Alembic_exportLowFrameRelativeSamples')
	highFrameRelativeSamples		= maya.cmds.optionVar(q='Alembic_exportHighFrameRelativeSamples')

	enablePreRoll				= bool(maya.cmds.optionVar(q='Alembic_exportEnablePreRoll'))
	preRollStartFrame			= float(maya.cmds.optionVar(q='Alembic_exportPreRollStartFrame'))
	preRollStep					= float(maya.cmds.optionVar(q='Alembic_exportPreRollStep'))
	attr						= maya.cmds.optionVar(q='Alembic_exportAttr')
	attrPrefix					= maya.cmds.optionVar(q='Alembic_exportAttrPrefix')
	verbose						= bool(maya.cmds.optionVar(q='Alembic_exportVerbose'))
	noNormals					= bool(maya.cmds.optionVar(q='Alembic_exportNoNormals'))
	renderableOnly				= bool(maya.cmds.optionVar(q='Alembic_exportRenderableOnly'))
	stripNamespaces				= bool(maya.cmds.optionVar(q='Alembic_exportStripNamespaces'))
	uvWrite						= bool(maya.cmds.optionVar(q='Alembic_exportUVWrite'))
	writeColorSets				= bool(maya.cmds.optionVar(q='Alembic_exportWriteColorSets'))
	writeFaceSets				= bool(maya.cmds.optionVar(q='Alembic_exportWriteFaceSets'))
	wholeFrameGeo				= bool(maya.cmds.optionVar(q='Alembic_exportWholeFrameGeo'))
	worldSpace					= bool(maya.cmds.optionVar(q='Alembic_exportWorldSpace'))
	writeVisibility				= bool(maya.cmds.optionVar(q='Alembic_exportWriteVisibility'))
	filterEulerRotations		= bool(maya.cmds.optionVar(q='Alembic_exportFilterEulerRotations'))
	writeCreases				= bool(maya.cmds.optionVar(q='Alembic_exportWriteCreases'))
	dataFormat					= int(maya.cmds.optionVar(q='Alembic_exportDataFormat'))
	perFrameCallbackMel			= maya.cmds.optionVar(q='Alembic_exportPerFrameCallbackMel')
	postJobCallbackMel				= maya.cmds.optionVar(q='Alembic_exportPostJobCallbackMel')
	perFrameCallbackPython		= maya.cmds.optionVar(q='Alembic_exportPerFrameCallbackPython')
	postJobCallbackPython		= maya.cmds.optionVar(q='Alembic_exportPostJobCallbackPython')

	# build AbcExport command
	command = "AbcBulletExport "
	job=""

	firstCacheFrame = None
	startEnd = [firstCacheFrame,firstCacheFrame]

	for cacheTimeRange, startFrame, endFrame, evaluateEvery,enableSample, lowSample, highSample \
		in zip(cacheTimeRanges, startFrames, endFrames, evaluateEverys, enableSamples, lowFrameRelativeSamples, highFrameRelativeSamples):

		if (cacheTimeRange != 3) :
			startEnd = maya.mel.eval('Alembic_getStartEndFrames({0});'.format(cacheTimeRange))
		else :
			startEnd[0] = startFrame
			startEnd[1] = endFrame

		if (firstCacheFrame==None) :
			firstCacheFrame = startEnd[0]
		
		job += "-frameRange {0} {1} ".format(startEnd[0],startEnd[1])

		if (evaluateEvery != 1) :
			if (evaluateEvery <= 0) :
				OpenMaya.MGlobal.displayError( maya.stringTable['y_AlembicExport.kInvalidEvaluateEvery'])
				return

			job += "-step {0} ".format(evaluateEvery)

		if (enableSample) :
			if (lowSample > 0 or lowSample < -evaluateEvery) :
				OpenMaya.MGlobal.displayError( maya.stringTable['y_AlembicExport.kInvalidLowFrameRelativeSample'])
				return
			
			if (highSample < 0 or highSample > evaluateEvery) :
				OpenMaya.MGlobal.displayError( maya.stringTable['y_AlembicExport.kInvalidHighFrameRelativeSample'])
				return
			
			job += "-frameRelativeSample {0} ".format(lowSample)
			job += "-frameRelativeSample 0 -frameRelativeSample {0} ".format(highSample)

	if (enablePreRoll) :
		# Check arguments.
		if (preRollStep <= 0) :
			OpenMaya.MGlobal.displayError( maya.stringTable['y_AlembicExport.kInvalidPreRollStep'])
			return


		if (preRollStartFrame >= firstCacheFrame) :
			OpenMaya.MGlobal.displayError( maya.stringTable['y_AlembicExport.kInvalidPreRollStartFrame'])
			return

		# Compute the pre-roll end frame.
		preRollEndFrame = maya.mel.eval('Alembic_getPrerollEndFrame({preRollStartFrame}, {firstCacheFrame}, {preRollStep});'
								  .format(preRollStartFrame=preRollStartFrame,firstCacheFrame=firstCacheFrame,preRollStep=preRollStep))

		preRollFlags = "-frameRange {0} {1} -step {2} -preRoll ".format(preRollStartFrame, preRollEndFrame, preRollStep)
		job = preRollFlags + job

	attrArray = attr.split(',')
	attrPrefixArray = attrPrefix.split(',')

	for i in attrArray:
		if (len(i) > 0) :
			job += "-attr "
			job += maya.cmds.formValidObjectName(i)
			job += " "

	for i in attrPrefixArray :
		if (len(i) > 0) :
			job += "-attrPrefix "
			job += maya.cmds.formValidObjectName(i)
			job += " "

	if (verbose) :
		command += "-verbose "
		

	if (noNormals) :
		job += "-noNormals "
		

	if (renderableOnly) :
		job += "-ro "
		

	if (stripNamespaces) :
		job += "-stripNamespaces "

	if (uvWrite) :
		job += "-uvWrite "

	if (writeColorSets) :
		job += "-writeColorSets "

	if (writeFaceSets) :
		job += "-writeFaceSets "

	if (wholeFrameGeo) :
		job += "-wholeFrameGeo "

	if (worldSpace) :
		job += "-worldSpace "

	if (writeVisibility) :
		job += "-writeVisibility "

	if (filterEulerRotations) :
		job += "-eulerFilter "

	if (writeCreases) :
		job += "-writeCreases "
		
	if (dataFormat == 2):
		job += "-dataFormat ogawa "

	if (len(perFrameCallbackMel) > 0) :
		if (containsWhiteSpace(perFrameCallbackMel)) :
			perFrameCallbackMel = "\"" + maya.cmds.encodeString(perFrameCallbackMel) + "\"" 

		job += ("-melPerFrameCallback " + maya.cmds.encodeString(perFrameCallbackMel) + " ")

	if (len(postJobCallbackMel) > 0) :
		if (containsWhiteSpace(postJobCallbackMel)) :
			postJobCallbackMel = "\"" + maya.cmds.encodeString(postJobCallbackMel) + "\"" 

		job += ("-melPostJobCallback " + maya.cmds.encodeString(postJobCallbackMel) + " ")


	if (len(perFrameCallbackPython) > 0) :
		if (containsWhiteSpace(perFrameCallbackPython)) :
			perFrameCallbackPython = "\"" + maya.cmds.encodeString(perFrameCallbackPython) + "\"" 
			
		job += ("-pythonPerFrameCallback " + maya.cmds.encodeString(perFrameCallbackPython) + " ")


	if (len(postJobCallbackPython) > 0) :
		if (containsWhiteSpace(postJobCallbackPython)) :
			postJobCallbackPython = "\"" + maya.cmds.encodeString(postJobCallbackPython) + "\"" 

		job += ("-pythonPostJobCallback " + maya.cmds.encodeString(postJobCallbackPython) + " ")


	# get objects to export
	roots = getObjectsToExport(sl=not exportAll)

	if len(roots):
		for root in roots:
			job += "-root {0} ".format(root)

		file = result[0]
		if (containsWhiteSpace(file)) :
			file = "\"" + file + "\""

		command += ("-j \"" + job + "-file " + maya.cmds.encodeString(file) + "\"")

		# execute command
		if not maya.cmds.pluginInfo( 'AbcBullet', q=True, loaded=True):
			OpenMaya.MGlobal.displayError(maya.stringTable['y_AlembicExport.kAbcExportNotLoaded'])
			return

		print command

		result = maya.mel.eval(command)
	else:
		OpenMaya.MGlobal.displayError( maya.stringTable['y_AlembicExport.kInvalidRoots'])
		return

	return

@Trace()
def exportSelected( *args, **kw ):
	kw['exportAll']=False
	doExportArgList( *args, **kw )

@Trace()
def exportAll( *args, **kw ):
	kw['exportAll']=True
	doExportArgList( *args, **kw )

# ===========================================================================
# Copyright 2016 Autodesk, Inc. All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# ===========================================================================
