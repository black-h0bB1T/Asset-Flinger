![Header](http://i.imgur.com/gp3BdlI.jpg)

# Asset Flinger
Asset Flinger is a **Free Blender Add-on for simple mesh importing via graphical menu**.
It's aimed at 3D modellers who constantly import pre-made 3D assets from their libraries for building their highly detailed creations.

**This is a fork of Blender Aid's Asset Flinger which you can find [here](https://github.com/BlenderAid/Asset-Flinger). Ideas and development up to version 0.2 is made by Blender Aid, many thanks to them!**

# Additions made to the original (Version 0.3 (2017-06-27))
This version contains many new features added by h0bB1T:
* Thumbnails are automatically generated on export.
	* Thumbnails could be created using 3 different scenes and in different sizes. Selection can be done in the preferences menu, next to the library path setting. This may be enhanced in future releases.
* UI is now changed depending on the chosen blender theme.
* If more assets are available than there is space to show them, the mouse wheel can be used the scroll through.
* The primary data exchange format is now **.blend** instead of **.obj**, so materials, modifiers and other settings are preserved. Even curves and other non mesh data should work (extensive testing required).
	* When selecting an asset for import and the asset is in **.blend** format, users can choose between appending and linking the asset.
	* Old assets in **.obj** format are still supported!
	* The assets that are packed to previous versions of Asset Flinger must be copied into a subfolder in your library to use them, this is not handled in parallel yet.

!!Please understand that due to the intensive code changes, stability is not granted at the moment. Every bug report is very welcome!!

# Download

* **[Asset_Flinger_Add-on_v0.3.zip](https://github.com/black-h0bB1T/Asset-Flinger/blob/master/releases/Asset_Flinger_Add-on_v0.3.zip?raw=true)** (Blender 2.78c)
* **[Asset_Flinger_Add-on_v0.2.zip](http://files.manujarvinen.com/Asset_Flinger/Asset_Flinger_Add-on_v0.2.zip)** (Blender 2.77)
* **[Asset_Flinger_Add-on_v0.1.zip](http://files.manujarvinen.com/Asset_Flinger/Asset_Flinger_Add-on_v0.1.zip)** (Blender 2.76 or lower)

- **[Installation instructions](https://github.com/BlenderAid/Asset-Flinger#installation)**
- Includes some nice ready-made ***CC-0 / Public Domain / 100%-free-for-commercial-use*** assets.

# Demo

#### Note: This video shows Asset Flinger 0.1/0.2. The current version has a slighted enhanced UI.
<a href="http://youtu.be/qYYoSTjIOTY" target="_blank">![Video](http://i.imgur.com/BwRkfsY.jpg)</a>
#### Screenshot (Version 0.3):
![Screenshot](https://raw.githubusercontent.com/black-h0bB1T/Asset-Flinger/master/misc/af-0.3-0.jpg)

# Installation
#### Installing the Add-on :
1. Download the package
2. Open Blender
3. Go to user preferences > Add-ons > Install from File...
4. Navigate to the downloaded .zip file, click Install from File...
5. Enable the Asset Flinger Add-on from the checkbox
6. Save User Settings
7. Try it out :) **Ctrl+Shift+Alt+A** opens the Asset Flinger menu in the 3D View

#### Setting up library location for your own assets:
1. In the Add-ons panel in Blender's User Preferences, put your own Asset Library location to Asset Flinger Add-on's preferences
2. Export your 3D models to the library with **Ctrl+Shift+Alt+E**
3. Make that location as a bookmark for your convenience

# Usage
* Add a mesh asset via shortcut: **Ctrl+Shift+Alt+A**
* Export your own mesh asset to the library via shortcut: **Ctrl+Shift+Alt+E**

# Known Bugs / Issues
* Doesn't work in Local View (isolation mode)
* When Tool Shelf (T) or Properties (N) panel is open in 3D view, you can't toggle them off after you've launched the Asset Flinger menu
* While in the Asset Flinger menu and doing an Alt-Tab to switch programs, and then coming back to Blender, the menu appears to all open 3D views. Very annoying.
* While using Asset Flinger in quad view or other types of layouts that have multiple smaller 3D views, the menu appears to all of them.

# Feature Ideas

* Remembering the last used asset folder where the user picked the asset last time
* Easy Add-on preferences checkbox for the above 'Remember last used asset folder'
* Easy Add-on preferences checkbox for hiding the asset file names in the asset menu to make it more compact
* Easy Add-on preferences setting to choose the amount of columns for the asset menu to make it more compact.
* Easy Add-on preferences setting to choose between the current Normal (128x128) and Small (64x64) sized thumbnails to allow for more compact view. (In the code there are already easy parameters for this) - OR - if this appears to be hard to realize, then simply providing 2 choices of the Add-on with the different sized thumbnails and thumbnail-generation settings
* Wrapping of text for long file names
