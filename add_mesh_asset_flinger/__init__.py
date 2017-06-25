# ##### BEGIN GPL LICENSE BLOCK #####
#
#  Copyright (C) 2014 Blender Aid
#  http://www.blendearaid.com
#  blenderaid@gmail.com

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
        "name": "Asset Flinger",
        "version": (0, 1),
        "blender": (2, 70, 0),
        "location": "View3D > Add > Mesh > Asset Flinger",
        "description": "Simple Mesh Importer",
        "category": "Add Mesh"
}

import subprocess, re, os, threading

import bpy, bgl, blf, pprint
from bpy.types import AddonPreferences, Operator
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    StringProperty
    )
from bpy_extras.io_utils import ExportHelper

# TODO: Scrollable.
# TODO: Link-Append sub-buttons.
# TODO: Better error handling.
# TODO: Change access to paths of af-things as function.
# TODO: Standalone version für blend export (remove export selected dependency).
# TODO: Update author + copyright.
# TODO: Support multiple asset dirs? Not really useful, could be done file system wise.

# Full path to "\addons\add_mesh_asset_flinger\" -directory
paths = bpy.utils.script_paths("addons")

libraryPath = 'assets'
for path in paths:
    libraryPath = os.path.join(path, "add_mesh_asset_flinger")
    if os.path.exists(libraryPath):
        break

if not os.path.exists(libraryPath):
    raise NameError('Did not find assets path from ' + libraryPath)
libraryIconsPath = os.path.join(libraryPath, "icons")

def log(s):
    """
    Central log fn, lets modify logging behavior in a single place.
    """
    print("[asset-flinger, %5i] - %s" % (threading.get_ident(), s))

# https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
def execute(cmd):
    """
    Runs an external application, in this case the blender executable for
    thumbnail generation. Returns all lines written by this application to stdout
    immediately on a line by line basis.
    """
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    #if return_code:
    #    raise subprocess.CalledProcessError(return_code, cmd)

def createThumbnail(blender, thumbscene, scene, material = ""):
    """
    Used to create the thumbnail for the obj object specified in parameter 'scene', full path
    is required. 'blender' is the path to the blender executable (bpy.app.binary_path).
    'thumbscene' is the scene to place the object in for thumbnail and contains itself some python
    scripting. If 'material' is specified, objects are prepared with the material, which must exist
    in the 'thumbscene'. Atm the thumbscene is bundled with Asset-Flinger.
    """
    log("*** CALL THUMBNAIL GEN ***")
    wm = bpy.context.window_manager
    # Parse Tracing Sample to show as progress.
    wm.progress_begin(0, 300)
    ptrn = re.compile(".*Path Tracing Sample\\s+(\\d+)/\\d+.*")
    # Run external instance of blender like the original thumbnail generator.
    for l in execute([blender, "-b", thumbscene, "--python-text", "ThumbScript", "--", "obj:" + scene, "mat:" + material]):
        # Log special prefixed lines (using log/log_object functions in thumnbail scripts).
        if l.startswith("[]scr"):
            log(l.strip()[5:])

        # If contains progress analyse and update progress.
        pts = ptrn.match(l)
        if pts:
            wm.progress_update(int(pts.group(1)))
            #print(float(pts.group(1))/3)

    wm.progress_end()

def exportSelectedInstalled():
    """
    Check if the export selected addon is installed, which allows export as .blend, so
    all settings (material, modifiers, ...) are preserved.
    https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Import-Export/Export_Selected
    """
    return hasattr(bpy.types, "OBJECT_MT_selected_export")

def preferences():
    """
    Return the instance of the AF user preferences.
    """
    return bpy.context.user_preferences.addons[__name__].preferences

def importObject(filename):
    """
    Imports the specified object, prefer .blend if available, otherwise take .obj.
    """
    # Cut off extension, import object by extension preference.
    basename, _ = os.path.splitext(filename)
    log("Import object '%s'" % basename)

    # Prefer the blend to .obj.
    if os.path.exists(basename + ".blend"):
        log("Use .blend version")
        # https://blender.stackexchange.com/questions/34540/how-to-link-append-a-data-block-using-the-python-api
        with bpy.data.libraries.load(basename + ".blend", link=True) as (dfrom, dto):
            dto.objects = dfrom.objects

        for obj in dto.objects:
            if obj is not None:
                log("  Append: %s" % obj)
                bpy.context.scene.objects.link(obj)

        bpy.ops.view3d.snap_selected_to_cursor()
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]

        return

    # Ok hopefully the obj exists.
    if os.path.exists(basename + ".obj"):
        log("Use .obj version")
        bpy.ops.import_scene.obj(filepath=basename + ".obj")

class RenderTools:
    """
    Handle drawing functionality in one place. If future versions of blender
    have a different API, changes are restricted to this class.
    """
    @staticmethod
    def renderTexture(texture, x, y, width, height):
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)

        texture.gl_load()
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, texture.bindcode[0])

        bgl.glEnable(bgl.GL_TEXTURE_2D)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_NEAREST)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_NEAREST)

        bgl.glColor4f(1, 1, 1, 1)

        bgl.glBegin(bgl.GL_QUADS)
        bgl.glTexCoord2d(0, 0)
        bgl.glVertex2d(x, y)
        bgl.glTexCoord2d(0, 1)
        bgl.glVertex2d(x, y + height)
        bgl.glTexCoord2d(1, 1)
        bgl.glVertex2d(x + width, y + height)
        bgl.glTexCoord2d(1, 0)
        bgl.glVertex2d(x + width , y)
        bgl.glEnd()

        texture.gl_free()

    @staticmethod
    def renderRect(color, x, y, width, height):
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(color[0], color[1], color[2], color[3])
        bgl.glRectf(x, y, x + width, y + height)

    @staticmethod
    def renderText(color, x, y, size, text, dpi = 72):
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(color[0], color[1], color[2], color[3])

        font_id = 0
        blf.position(font_id, x, y, 0)
        blf.size(font_id, size, dpi)
        blf.draw(font_id, text)

class AssetFlingerPreferences(AddonPreferences):
    """
    Preferences from addons menu. In addition, contains all information used
    for visualization. So it could easily be enhanced for visual settings.
    """
    bl_idname = __name__

    custom_library_path = StringProperty(
        name="Your Library",
        subtype='FILE_PATH',
        )

    def draw(self, context):
        layout = self.layout

        split = layout.split(percentage=1)

        col = split.column()
        sub = col.column(align=True)
        sub.prop(self, "custom_library_path")

        sub.separator()

    def iconSize(self): return 128
    def menuItemMargins(self): return 4
    def menuItemHeight(self): return self.iconSize() + 2 * self.menuItemMargins()
    def menuItemWidth(self): return 400
    def itemTextSize(self): return 16

    def bgColor(self): return (0, 0, 0, 0.6)
    def menuColor(self): return (0.447, 0.447, 0.447, 0.8)
    def menuColorHighlighted(self): return (0.555, 0.555, 0.555, 0.8)
    def itemTextColor(self): return (0, 0, 0, 0.8)

class MenuItem:
    """
    Represents an existing asset or folder. Handles drawing of the visual representation
    as well as every user interaction with it.
    """
    def __init__(self, texture, text, folderInfo = None, assetInfo = None):
        self._texture = texture
        self._text = text
        self._folderInfo = folderInfo
        self._assetInfo = assetInfo

    def draw(self, rect, mouse):
        """
        Draws the menu item i the given rect.
        """
        x, y, w, h = rect
        mx, my = mouse[0] - x, mouse[1] - y
        isInside = mx >= 0 and mx < w and my >= 0 and my < h

        p = preferences()
        margins = p.menuItemMargins()
        iconSize = p.iconSize()

        # Render background triangle.
        RenderTools.renderRect(
            p.menuColorHighlighted() if isInside else p.menuColor(),
            x + margins,
            y + margins,
            w - 2 * margins,
            h - 2 * margins
        )

        # Render icon.
        RenderTools.renderTexture(
            self._texture,
            x + margins,
            y + margins,
            iconSize,
            iconSize
        )

        # Render text for asset.
        RenderTools.renderText(
            p.itemTextColor(),
            x + 3 * margins + iconSize,
            y + h / 2,
            p.itemTextSize(),
            self._text + " - %i, %i" % (mx, my)
        )

    def testClick(self, rect, mouse):
        """
        Handle user click, can be everywhere!
        """
        x, y, w, h = rect
        mx, my = mouse[0] - x, mouse[1] - y
        isInside = mx >= 0 and mx < w and my >= 0 and my < h

        # If clicked inside this instance ...
        if isInside:
            # Check if its a folder entry ..
            if self._folderInfo:
                # Update menu in renderer.
                self._folderInfo[2].setMenuItems(MenuItem.buildListForFolder(*self._folderInfo))
            elif self._assetInfo:
                # If this is an asset, import, link or whatever.
                importObject(self._assetInfo[0])
                self._assetInfo[1].setFinished()

    @staticmethod
    def buildListForFolder(path, level, renderer):
        """
        Create the list of menu items for the given path. Level
        is used to determine if the top level has been reached (.. prevented).
        """
        r = []
        if level != 0:
            r.append(MenuItem(
                renderer.folderIcon(),
                "..",
                folderInfo = (os.path.abspath(os.path.join(path, os.pardir)), level - 1, renderer)
            ))

        # Folders first ...
        for e in sorted(os.listdir(path)):
            full = os.path.join(path, e)
            if os.path.isdir(full):
                r.append(MenuItem(
                    renderer.folderIcon(),
                    e,
                    folderInfo = (full, level + 1, renderer)
                ))

        for e in sorted(os.listdir(path)):
            full = os.path.join(path, e)
            basename, ext = os.path.splitext(full)
            if ext.lower() == ".obj":
                iconImage = basename + ".png"
                icon = renderer.loadIcon(iconImage, False) if os.path.exists(iconImage) else renderer.noThumbnailIcon()
                if not os.path.isdir(full):
                    r.append(MenuItem(
                        icon,
                        os.path.basename(basename),
                        assetInfo = (full, renderer)
                    ))

        return r

class ScreenRenderer:
    """
    Handles the rendering of the asset selection OSD as well as user interaction
    with the OSD. Manages loaded textures and cleans them up when calling dispose() which
    is done before releasing the object.
    """
    def __init__(self):
        self._dbg = ""
        self._finished = False

        # Last known mouse positions.
        self._mouseX = -1
        self._mouseY = -1

        # Store screen dimension in last draw call.
        self._width = -1
        self._height = -1

        # Scroll through assets.
        self._scrollPos = 0

        # Limit the asset menu area (for e.g. later additions).
        self._menuTop = 20

        self._items = []

        # Lists to store info about loaded textures (for later cleanup).
        self._genericIcons = []
        self._specificIcons = []

        # Some icons for multiple uses.
        self._folderIcon = self.loadIcon(os.path.join(libraryIconsPath, "folder.png"), True)
        self._noThumbnailIcon = self.loadIcon(os.path.join(libraryIconsPath, "nothumbnail.png"), True)

    def loadIcon(self, path, generic):
        """
        Load icon as texture and return id. Stores information for later cleanup in one
        of the internal lists. One will cleanup of on every folder change, the other on final cleanup.
        """
        log("Load image: " + path)
        tid = bpy.data.images.load(filepath = path, check_existing = True)
        if generic:
            self._genericIcons.append(tid.filepath_raw)
        else:
            self._specificIcons.append(tid.filepath_raw)
        #log("   RAW: " + tid.filepath_raw)
        return tid

    def freeImages(self, lst):
        """
        Free textures not needed anymore.
        """
        for image in bpy.data.images:
            if image.filepath_raw in lst:
                #log("CLEAN TEX:" + image.filepath_raw)
                image.user_clear()
                bpy.data.images.remove(image, do_unlink=True)
        lst.clear()

    def dispose(self):
        """
        Called on termination, frees all loaded resources.
        """
        self.freeImages(self._genericIcons)
        self.freeImages(self._specificIcons)

    def folderIcon(self): return self._folderIcon
    def noThumbnailIcon(self): return self._noThumbnailIcon

    def setMenuItems(self, items):
        """
        Set new list of menu items.
        """
        # Clear previous resources.
        #self.freeImages(self._specificIcons)
        self._items = items

    def setFinished(self):
        """
        Set finish state from outside (used after asset load).
        """
        self._finished = True

    def isFinished(self):
        """
        Reports if finished is reached (if asset has been load or any user interaction).
        """
        return self._finished

    def renderInfo(self, s, height):
        """
        Render textual info in the top area.
        """
        RenderTools.renderText((0.6, 1, 0.6, 1), 5, height - 16, 16, s)

    def renderDebug(self):
        """
        Render text in the lower area.
        """
        if len(self._dbg) > 0:
            RenderTools.renderText((0.6, 0.6, 1, 1), 5, 8, 16, self._dbg)

    def calcMenuItemRect(self, index, count, width, height):
        """
        Based on valid area size, return the position of item number 'index', if count items should be rendered.
        """
        count = len(self._items)
        itemsPerLine = round(width / preferences().menuItemWidth())
        lines = round(count / itemsPerLine) + (1 if (count % itemsPerLine) != 0 else 0)
        effectiveItemWidth = width / itemsPerLine

        col = index % itemsPerLine
        row = int(index / itemsPerLine)

        # self._dbg = "w: %f, c: %f, ipl: %f, lns: %f, eiw: %f" % (width, count, itemsPerLine, lines, effectiveItemWidth)
        # log("%i - %f, %f" % (index, row, col))
        # print((
        #     col * effectiveItemWidth,
        #     height - row * preferences().menuItemHeight(),
        #     effectiveItemWidth,
        #     preferences().menuItemHeight()
        # ))

        return (
            col * effectiveItemWidth,
            height - (row + 1) * preferences().menuItemHeight() - self._menuTop,
            effectiveItemWidth,
            preferences().menuItemHeight()
        )

    def draw(self, width, height):
        self._width = width
        self._height = height
        menuHeight = height - self._menuTop

        # Render the background darker.
        RenderTools.renderRect(preferences().bgColor(), 0, 0, width, height)

        # Render the menu items.
        if not self._items:
            # Show informational text at the top.
            self.renderInfo("No items in asset folder, verify path (%s)." % preferences().custom_library_path)
        else:
            # Render item by item.
            for index, e in enumerate(self._items):
                # The target rectangle, based on current view size.
                itemRect = self.calcMenuItemRect(index, len(self._items), width, height)
                e.draw(itemRect, (self._mouseX, self._mouseY))

        self.renderDebug()

        # Cleanup render states.
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_TEXTURE_2D)

    def mouseMove(self, x, y):
        self._mouseX = x
        self._mouseY = y

    def mouseClick(self, x, y, button, event):
        #self._dbg = "%f, %f, %s, %s" % (x, y, button, event)
        # Prevent crash.
        if self._width < 1 or self._height < 1:
            return

        if button == "LEFTMOUSE" and event == "RELEASE":
            for index, e in enumerate(self._items):
                # The target rectangle, based on current view size.
                itemRect = self.calcMenuItemRect(index, len(self._items), self._width, self._height)
                e.testClick(itemRect, (x, y))

        if button == "RIGHTMOUSE":
            self._finished = True

    def otherEvent(self, event):
        if event.type == "ESC":
            self._finished = True

class AssetFlingerMenu(Operator):
    """
    Renders the OSD menu to select an existing asset for import.
    """
    bl_idname = "view3d.asset_flinger"
    bl_label = "Asset Flinger"

    def __init__(self):
        self._renderer = None
        self._handle = None

    def modal(self, context, event):
        context.area.tag_redraw()

        # Forward several events to the renderer.
        if event.type == 'MOUSEMOVE':
            self._renderer.mouseMove(event.mouse_region_x, event.mouse_region_y)
        elif event.type == "LEFTMOUSE" or event.type == "MIDDLEMOUSE" or event.type == "RIGHTMOUSE":
            self._renderer.mouseClick(event.mouse_region_x, event.mouse_region_y, event.type, event.value)
        else:
            self._renderer.otherEvent(event)

        # Check if renderer signals that it can be removed.
        if self._renderer.isFinished():
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self._renderer.dispose()
            self._renderer = None
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        """
        Called if user triggers the operator. Adds a custom render callback.
        """
        # Only this area type is supported.
        if context.area.type == 'VIEW_3D':
            self._renderer = ScreenRenderer()
            assets = preferences().custom_library_path
            if len(assets) > 0:
                self._renderer.setMenuItems(MenuItem.buildListForFolder(assets, 0, self._renderer))
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.drawCallback, (context, ), 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot show asset flinger")
            return {'CANCELLED'}

    def drawCallback(self, context):
        self._renderer.draw(
            context.area.regions[4].width,
            context.area.regions[4].height
        )

class AssetFlingerExport(Operator, ExportHelper):
    """
    Manages all export related tasks. Uses ExportHelper for export file selection.
    """
    bl_idname = "export.asset_flinger"
    bl_label = "Asset Flinger Model Export"

    # Exporter stuff.
    filename_ext = ".obj"
    filter_glob = StringProperty(
            default="*.obj;*.blend",
            options={'HIDDEN'},
            )

    def execute(self, context):
        """
        This gets called after user has selected a file for export.
        """
        basename, _ = os.path.splitext(self.properties.filepath)

        ###########################################
        # .blend export

        # If the 'export selected' addon is installed ...
        if exportSelectedInstalled():
            log("Export as .blend")
            bpy.ops.export_scene.selected(
                exporter_str = "BLEND",
                filepath = basename + ".blend"
            )

        ###########################################
        # .obj export and thumb generation

        # Write wavefront obj to file.
        log("Export as .obj");
        bpy.ops.export_scene.obj(
            filepath = basename + ".obj",
            use_selection = True,
            use_mesh_modifiers = True,
            use_materials = False
        )

        # Run thumbnail generator for this .obj.
        log("Create thumbnail.")
        createThumbnail(
            bpy.app.binary_path,
            os.path.join(libraryPath, "thumbnailer/Thumbnailer.blend"),
            self.properties.filepath
        )

        ###########################################
        # Done
        log("Completed.")
        return {'FINISHED'}

# store keymaps here to access after registration
addon_keymaps = []

def menu_draw(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(AssetFlingerMenu.bl_idname, icon='MOD_SCREW')

def register():
    bpy.utils.register_class(AssetFlingerMenu)
    bpy.utils.register_class(AssetFlingerExport)
    bpy.types.INFO_MT_mesh_add.append(menu_draw)
    bpy.utils.register_class(AssetFlingerPreferences)

    # handle the keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('view3d.asset_flinger', 'A', 'PRESS', ctrl=True, shift=True, alt=True)
        kmi = km.keymap_items.new('export.asset_flinger', 'E', 'PRESS', ctrl=True, shift=True, alt=True)
        addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_class(AssetFlingerMenu)
    bpy.utils.unregister_class(AssetFlingerExport)
    bpy.utils.unregister_class(AssetFlingerPreferences)

    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
