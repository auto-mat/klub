class CustomEditorApp extends _EditorApp

  # The custom editor application

  getStyles: () ->
    _styles = []
    styles = document.querySelectorAll('[id^="font_size_"]')
    for item, index in styles
      _styles.push({id: item.id, style: item.innerHTML})
    return _styles

  save: (passive) ->
    # Save changes to the current page
    if not @dispatchEvent(@createEvent('save', {passive: passive}))
      return

    # Blur any active element to ensure empty elements are not retained
    root = ContentEdit.Root.get()
    if root.focused() and not passive
      root.focused().blur()

    # Check the document has changed, if not we don't need do anything
    if root.lastModified() == @_rootLastModified and passive
      # Trigger the saved event early with no modified regions,
      @dispatchEvent(
        @createEvent('saved', {regions: {}, passive: passive})
      )
      return

    # Build a map of the modified regions
    domRegions = []
    modifiedRegions = {}
    for name, region of @_regions
      # Check for regions that contain only a place holder
      html = region.html()
      if region.children.length == 1 and not region.type() is 'Fixture'
        child = region.children[0]
        if child.content and not child.content.html()
          html = ''

      # Apply the changes made to the DOM (affectively resetting the DOM
      # to a non-editable state).
      unless passive
        # Unmount all children
        for child in region.children
          child.unmount()

        # Handle fixtures vs. standard regions
        if region.children.length is 1 and region.children[0].isFixed()
          wrapper = @constructor.createDiv()
          wrapper.innerHTML = html
          domRegions.push(wrapper.firstElementChild)
          region.domElement().parentNode.replaceChild(
            wrapper.firstElementChild,
            region.domElement()
          )
        else
          domRegions.push(region.domElement())
          region.domElement().innerHTML = html

      # Check the region has been modified, if not we don't include it in
      # the output.
      if region.lastModified() == @_regionsLastModified[name]
        continue

      modifiedRegions[name] = html

      # Set the region back to not modified
      @_regionsLastModified[name] = region.lastModified()

      # Resync the DOM regions, this is required as fixture will replace the
      # existing DOM region element (regions wont).
      @_domRegions = domRegions

      # Trigger the saved event with a region HTML map for the changed
      # content.
      @dispatchEvent(
        @createEvent(
          'saved',
          {
            regions: modifiedRegions,
            passive: passive,
            styles: @getStyles()
          }
        )
      )


class ContentTools.EditorApp

  # The `ContentTools.EditorApp` class is a singleton, this code provides
  # access to the singleton instance of the protected `_EditorApp` class which
  # is initialized the first time the class method `get` is called.

  # Storage for the singleton instance that will be created for the editor app
  instance = null

  @get: () ->
    cls = ContentTools.EditorApp.getCls()
    instance ?= new cls()

  @getCls: () ->
    return CustomEditorApp
