# RenderDoc-CSV-Strip-Blender-Import-Script

[RenderDoc](https://renderdoc.org/) is the program I exported a model from. I wanted to import this model into Blender.

The export file format is CSV but the way vertices of the model are written to the file depends on the primitive topology of the model.

This topology can be:

<dl>
  <dt>Triangle list</dt>
  <dd>Every three vertices in the list compose a triangle. See https://docs.microsoft.com/en-us/windows/win32/direct3d9/triangle-lists</dd>

  <dt>Triangle strip</dt>
  <dd>The first three vertices in the list compose a triangle. Every vertex after that makes a new triangle using previous vertices in the list in a specific order.
	  See https://docs.microsoft.com/en-us/windows/win32/direct3d9/triangle-strips</dd>
</dl>

These scripts are simply a modification of an already existing script that can be found [here.](https://github.com/sbobovyc/GameTools/blob/master/Blender/import_pix.py) 

The problem was that the script would assume a triangle list primitive topology. Therefore, when trying to import a CSV file written in triangle strip topology, the model would be missing many triangles.
I figured out that it was due to this topology and decided to write my own version of the script that would assume a triangle strip topology instead.
So now we have both versions.

I have also included two variants of this modified script:

<dl>
  <dt>_file</dt>
  <dd>Reads all the data directly from the file. Very slow, but I guess could be needed for extremely big models whose vertices list is just too big to have in memory. I would suggest having the blender console open to make sure it is actually running. You should see "Processing vertex #(vertex number)" appear in the console for every vertex in the list.</dd>

  <dt>_mem</dt>
  <dd>Puts all vertices in memory so any index can be accessed. Alot faster.</dd>
</dl>

<h2>Usage:</h2>

Install into Blender as you would any other plugin.

The import menu will now have a "PIX CSV Strip Mem (.csv)" (or "PIX CSV Strip File (.csv)" depending on the variant you installed) option you can use to import the CSV file.

Keep in mind that the models imported using this script will have degenerate triangles, triangles that have 0 area. Those are a side effect of triangle strips. I don't know how to clean them up in Blender but I know you can clean them up in Maya using the cleanup function and checking "Faces with zero geometry area" under "Remove Geometry" in the cleanup options.
I could probably have skipped the 0 area triangles in script but I figured someone might want to keep them and they are relatively easy to deal with anyway.

These scripts work with RenderDoc 1.4 and Blender 2.79 and probably work with newer versions of Blender and any other versions of RenderDoc.