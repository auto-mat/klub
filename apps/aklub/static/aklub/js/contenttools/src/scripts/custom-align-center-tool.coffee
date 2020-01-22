class CustomAlignCentertTool extends CustomAlignLeftTool

  ContentTools.ToolShelf.stow(@, 'custom-align-center')

  @label = 'Align center'
  @icon = 'align-center'
  @className = 'text-center'


index = ContentTools.DEFAULT_TOOLS[0].indexOf('align-center')

# Override default align-center tool
ContentTools.DEFAULT_TOOLS[0][index] = 'custom-align-center'
