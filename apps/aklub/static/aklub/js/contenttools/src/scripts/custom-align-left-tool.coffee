class CustomAlignLeftTool extends ContentTools.Tools.AlignLeft

  ContentTools.ToolShelf.stow(@, 'custom-align-left')

  @apply: (element, selection, callback) ->
    # Apply the tool to the current element

    # Dispatch `apply` event
    toolDetail = {
      'tool': this,
      'element': element,
      'selection': selection
    }
    if not @dispatchEditorEvent('tool-apply', toolDetail)
      return

    # List items and table cells use child nodes to manage their content
    # which don't support classes, so we need to use the parent.
    if element.type() in ['ListItemText', 'TableCellText']
      element = element.parent()

    # Remove any existing text alignment classes applied
    alignmentClassNames = [
      ContentTools.Tools.AlignLeft.className,
      ContentTools.Tools.AlignCenter.className,
      ContentTools.Tools.AlignRight.className,
      AlignJustifyTool.className
    ]

    for className in alignmentClassNames
      if element.hasCSSClass(className)
        element.removeCSSClass(className)

        # If we're removing the class associated with the tool then we
        # can return early (this allows the tool to be toggled on/off).
        if className == @className
          return callback(true)

    # Add the alignment class to the element
    element.addCSSClass(@className)

    callback(true)

    # Dispatch `applied` event
    @dispatchEditorEvent('tool-applied', toolDetail)

index = ContentTools.DEFAULT_TOOLS[0].indexOf('align-left')

# Override default align-left tool
ContentTools.DEFAULT_TOOLS[0][index] = 'custom-align-left'
