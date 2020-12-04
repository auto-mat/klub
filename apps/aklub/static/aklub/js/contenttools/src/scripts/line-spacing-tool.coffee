class LineSpacingTool extends CustomAlignLeftTool

  # Apply a class to justify align the contents of the current text block.

  # Register the tool with the toolshelf
  ContentTools.ToolShelf.stow(@, 'line-spacing')

  # The tooltip and icon modifier CSS class for the tool
  @label = 'Line spacing'
  @icon = 'line-spacing'
  @className = 'line-spacing'

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

    # # Measure a rectangle of the content selected so we can position the
    # # dialog centrally to it.
    domElement = element.domElement()
    rect = domElement.getBoundingClientRect()

    # Set-up the dialog
    app = ContentTools.EditorApp.get()

    # Modal
    modal = new ContentTools.ModalUI()

    # List items and table cells use child nodes to manage their content
    # which don't support classes, so we need to use the parent.
    if element.type() in ['ListItemText', 'TableCellText']
      element = element.parent()

    dialog = new LineSpacingDialog()
    dialog.position @getDialogPosition rect

    # Listen for save events against the dialog
    dialog.addEventListener 'save', (ev) =>

      # Get line spacing number value
      @_lineSpacing = ev.detail().lineSpacing

      modal.hide()
      dialog.hide()

      @_apply element, selection

      # Trigger the callback
      callback(true)

    app.attach modal
    app.attach dialog

    modal.show()
    dialog.show()

    callback(true)

    callback(true)

    # Dispatch `applied` event
    @dispatchEditorEvent('tool-applied', toolDetail)

  @getDialogPosition: (rect) ->
    [
      rect.left + (rect.width / 2) + window.scrollX,
      rect.top + (rect.height / 2) + window.scrollY
    ]

  @setNewCSS: (fontSizeId, fontSizeCSSClass) ->
    style = document.createElement('style')
    style.type = 'text/css'
    style.id =  fontSizeId
    style.innerHTML = fontSizeCSSClass
    document.getElementsByTagName('head')[0].appendChild(style)

  @index: (elementRef) ->
    nodes = Array.prototype.slice.call \
      document.getElementsByClassName('[ article__content ]')[0].children
    return nodes.indexOf elementRef

  @_apply: (element, selection) =>

    elementIndex = @index element.domElement()
    [from, to] = selection.get()
    lineSpacingCSSClassName = "line-spacing-#{ elementIndex }"
    lineSpacingId = "line_spacing_#{ elementIndex }"

    lineSpacingCSSClass = """
    .article__content .#{ lineSpacingCSSClassName } {
      line-height: #{ @_lineSpacing };
      }
      """

    style = document.getElementById lineSpacingId
    if style?
      style.innerHTML = lineSpacingCSSClass
    else
      @setNewCSS lineSpacingId, lineSpacingCSSClass

    # Add the alignment class to the element
    element.addCSSClass(lineSpacingCSSClassName)


class LineSpacingDialog extends ContentTools.LinkDialog

  # An anchored dialog to support inserting/modifying a line spacing
  # css prop value

  constructor: (@lineSpacing) ->
    super()

    @_defLineSpacingValue = 1.0

  mount: () ->
    super()

    @lineSpacing = if @lineSpacing? then @lineSpacing else \
      @_defLineSpacingValue
    @_domInput.setAttribute 'name', 'lineSpacing'
    @_domInput.setAttribute 'value', @lineSpacing
    @_domInput.setAttribute 'placeholder', \
      ContentEdit._ 'Enter number to set the line height'

    # Remove the new window target DOM element
    @_domElement.removeChild @_domTargetButton

  save: () ->
    # Save the line spacing value.
    detail = {
      lineSpacing: @_domInput.value.trim()
    }
    @dispatchEvent(@createEvent('save', detail))


ContentTools.DEFAULT_TOOLS[0].push('line-spacing')
