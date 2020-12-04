class CustomAlignRightTool extends CustomAlignLeftTool

  ContentTools.ToolShelf.stow(@, 'custom-align-right')

  @label = 'Align right'
  @icon = 'align-right'
  @className = 'text-right'


index = ContentTools.DEFAULT_TOOLS[0].indexOf('align-right')

# Override default align-right tool
ContentTools.DEFAULT_TOOLS[0][index] = 'custom-align-right'
