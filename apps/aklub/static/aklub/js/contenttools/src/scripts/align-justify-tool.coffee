class AlignJustifyTool extends CustomAlignLeftTool

  # Apply a class to justify align the contents of the current text block.
  
  # Register the tool with the toolshelf
  ContentTools.ToolShelf.stow(@, 'align-justify')

  # The tooltip and icon modifier CSS class for the tool
  @label = 'Align justify'
  @icon = 'align-justify'
  @className = 'text-justify'


ContentTools.DEFAULT_TOOLS[0].push('align-justify')