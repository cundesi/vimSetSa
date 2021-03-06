"""
This module defines all the image formats tht Maya can handle
"""
import maya
maya.utils.loadStringResourcesForModule(__name__)


import maya.cmds as cmds

# ---------------------------------------------------------------------------
def cmpFormat(x, y):
  """Helper method to compare two formats, using the description as
  the key"""
  return x.description < y.description

# =============================================================================
class ImageDescriptor:
  """All information necessary to identify an image format"""

  # Property constants
  kIsImage   = 1
  kIsMovie   = 2
  kIsVector  = 4
  kIsSixteen = 8
  kIsLayered = 16

  # ---------------------------------------------------------------------------
  def __init__(self, ident, extension, description, properties, imfKey=None, otherExtensions=None):
    self.extension		= extension
    self.ident			= ident
    if imfKey is None:
      imfKey = extension
    self.imfKey			= imfKey
    self.description	= description
    self.properties		= properties
    self.otherExtensions= otherExtensions
    self.oldOutf		= 7
    self.oldImfKey		= ""

  # ---------------------------------------------------------------------------
  def filterFormat(self):
    'Helper method to return this format as a file browser filter'
    if self.otherExtensions is not None:
        return "%s (%s)" % (self.description, 
            " ".join(["*." + s for s in ([self.extension] + self.otherExtensions.split(" "))]))
    return "%s (*.%s)" % (self.description, self.extension)

  # ---------------------------------------------------------------------------
  def menuFormat(self):
    'Helper method to return this format as a suitable menu item'
    return "%s (%s)" % (self.description, self.extension)

  # ---------------------------------------------------------------------------
  def prop(self, propBits):
    'True if the file format has all those propeties'
    return (self.properties & propBits) == propBits

# =============================================================================
class ImageFormats:
  """Storage to keep track of all defined formats"""

  # ---------------------------------------------------------------------------
  def __init__(self):
    self.formats = []

    # These are the default formats that ship with Maya.

    self.addFormat( 0, "gif", maya.stringTable['y_createImageFormats.kGIF' ])
    self.addFormat( 1, "pic", maya.stringTable['y_createImageFormats.kSoftImage' ], imfKey="si")
    self.addFormat( 2, "rla", maya.stringTable['y_createImageFormats.kRLA' ])
    self.addFormat( 3, "tif", maya.stringTable['y_createImageFormats.kTiff' ])
    self.addFormat( 4, "tif", maya.stringTable['y_createImageFormats.kTiff16' ],
                   properties = ImageDescriptor.kIsImage + ImageDescriptor.kIsSixteen)
    self.addFormat( 5, "sgi", maya.stringTable['y_createImageFormats.kSGI' ])

    self.addFormat( 7, "iff", maya.stringTable['y_createImageFormats.kMayaIFF' ], imfKey="maya")
    self.addFormat( 6, "als", maya.stringTable['y_createImageFormats.kAliasPIX' ])
    self.addFormat( 8, "jpg",maya.stringTable['y_createImageFormats.kJPEG' ], imfKey="jpg", otherExtensions="jpeg")
    self.addFormat( 9, "eps", maya.stringTable['y_createImageFormats.kEPS' ],
                   properties = ImageDescriptor.kIsImage + ImageDescriptor.kIsVector)
    self.addFormat(10, "iff", maya.stringTable['y_createImageFormats.kMaya16IFF' ],
                   imfKey="maya",
                   properties = ImageDescriptor.kIsImage + ImageDescriptor.kIsSixteen)
    self.addFormat(11, "cin", maya.stringTable['y_createImageFormats.kCineon' ])
    self.addFormat(12, "yuv", maya.stringTable['y_createImageFormats.kQuantel' ])
    self.addFormat(13, "sgi", maya.stringTable['y_createImageFormats.kSGI16' ],
                   properties = ImageDescriptor.kIsImage + ImageDescriptor.kIsSixteen)
    # 14-18 are not used any more
    self.addFormat(19, "tga", maya.stringTable['y_createImageFormats.kTarga' ])
    self.addFormat(20, "bmp", maya.stringTable['y_createImageFormats.kWindowsBitmap' ])

    self.addFormat(31, "psd", maya.stringTable['y_createImageFormats.kPSD' ])
    self.addFormat(32, "png", maya.stringTable['y_createImageFormats.kPNG' ])
    self.addFormat(35, "dds", maya.stringTable['y_createImageFormats.kDDS' ])
    self.addFormat(36, "psd",maya.stringTable['y_createImageFormats.kPSDLayered' ],
                   imfKey="psdLayered",
                   properties = ImageDescriptor.kIsImage + ImageDescriptor.kIsLayered)

    if cmds.about(mac=True):
      self.addFormat(22, "mov", maya.stringTable['y_createImageFormats.kQuicktimeMovie' ],
                     imfKey="qt", properties = ImageDescriptor.kIsMovie)
      self.addFormat(30, "pntg", maya.stringTable['y_createImageFormats.kMacPaint' ])
      self.addFormat(33, "pict", maya.stringTable['y_createImageFormats.kQuickDraw' ])
      self.addFormat(34, "qtif", maya.stringTable['y_createImageFormats.kQuicktimeImage' ])

    if cmds.about(nt=True):
      self.addFormat(23, "avi", maya.stringTable['y_createImageFormats.kAVI' ], properties = ImageDescriptor.kIsMovie)

    # Add the vector only formats
    self.addFormat(60, "swf", maya.stringTable['y_createImageFormats.kMacromediaSWF' ],
                   properties=ImageDescriptor.kIsVector)
    self.addFormat(63, "swft", maya.stringTable['y_createImageFormats.kSwift3DImporter' ],
                   properties=ImageDescriptor.kIsVector)
    self.addFormat(61, "ai", maya.stringTable['y_createImageFormats.kAdobeIllustrator' ],
                   properties=ImageDescriptor.kIsVector)
    self.addFormat(62, "svg", maya.stringTable['y_createImageFormats.kSVG' ],
                   properties=ImageDescriptor.kIsVector)

    # Add the IMF plug-ins
    self.imfPlugins = cmds.imfPlugins(query=True)
    for imf in self.imfPlugins:
      key = cmds.imfPlugins(imf, query=True, keyword=True)
      if (key == '') or not cmds.imfPlugins(key, query=True, writeSupport=True):
        continue

      # Check if this plug-in was already registered
      ident = 1000
      if self.findKey(key) is None:
        ext = cmds.imfPlugins(imf, query=True, extension=True).replace('.', '')
        self.addFormat(ident, ext, imf, imfKey=key)
        ident += 1

  # ---------------------------------------------------------------------------
  def findKey(self, key):
    'return the format description corresponding to this IMF key, or None'
    for fmt in self.formats:
      if key == fmt.imfKey:
        return fmt
    return None

  # ---------------------------------------------------------------------------
  def findIdent(self, ident):
    'return the format description corresponding to this Id, or None'
    for fmt in self.formats:
      if ident == fmt.ident:
        return fmt
    return None

  # ---------------------------------------------------------------------------
  def addFormat(self, ident, extension, description, properties=1, imfKey=None, otherExtensions=None):
    'Add a new format to the table'
    desc = ImageDescriptor(ident, extension, description, properties, imfKey, otherExtensions)
    self.formats.append(desc)

  # ---------------------------------------------------------------------------
  def listFormats(self, type=255, returnFormat=None):
    """List all the image formats that match the given type
    \param[in] type Property bits to test.
    \param[in] returnFormat Callback to format the result of matching
    items.
    """
    res = []
    for fmt in self.formats:
      if fmt.prop(type):
        if returnFormat is None:
          res.append(fmt)
        else:
          res.append(returnFormat(fmt))

    if returnFormat is None:
      return sorted(res, cmpFormat)

    return sorted(res)

  # ---------------------------------------------------------------------------
  def pushRenderGlobalsForDesc(self, description):
    'return the format description corresponding to this Id, or None'
    self.oldOutf = cmds.getAttr("defaultRenderGlobals.outf")
    self.oldImfKey = cmds.getAttr("defaultRenderGlobals.imfkey")
    for fmt in self.formats:
      if description == fmt.description:
        newIdent = fmt.ident
        if newIdent >= 1000:
          newIdent = 50  # for IMF formats we use 50 for outf
        cmds.setAttr("defaultRenderGlobals.outf", newIdent)
        cmds.setAttr("defaultRenderGlobals.imfkey", fmt.imfKey, type="string")

  def popRenderGlobals(self):
    cmds.setAttr("defaultRenderGlobals.outf", self.oldOutf)
    cmds.setAttr("defaultRenderGlobals.imfkey", self.oldImfKey, type="string")
    self.oldOutf = 7
    self.oldImfKey = ""
# ===========================================================================
# Copyright 2016 Autodesk, Inc. All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# ===========================================================================
