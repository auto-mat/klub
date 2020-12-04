class IncreaseFontSizeTool extends ContentTools.Tools.Bold

  # Increase font size of the current selection of text.

  # Register the tool with the toolshelf
  ContentTools.ToolShelf.stow(@, 'increase-font-size')

  # The tooltip and icon modifier CSS class for the tool
  @label = 'Increase font size'
  @icon = 'increase-font-size'
  @tagName = 'span'
  @showOnce = false

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

    element.storeState()

    DecreaseFontSizeTool.showOnce = false

    if not @showOnce
      # Add a fake selection wrapper to the selected text so that it
      # appears to be
      # selected when the focus is lost by the element.
      selectTag = new HTMLString.Tag 'span', {'class': 'ct--pseudo-select'}
      [from, to] = selection.get()

      element.content = element.content.format from, to, selectTag
      element.updateInnerHTML()

      # Measure a rectangle of the content selected so we can position the
      # dialog centrally to it.
      domElement = element.domElement()
      measureSpan = domElement.getElementsByClassName 'ct--pseudo-select'
      rect = measureSpan[0].getBoundingClientRect()

      element.content = element.content.unformat from, to, selectTag
      element.updateInnerHTML()

      # Set-up the dialog
      app = ContentTools.EditorApp.get()

      # Modal
      modal = new ContentTools.ModalUI()

      # Dialog
      size = if DecreaseFontSizeTool._fontSizeFactor? \
        then DecreaseFontSizeTool._fontSizeFactor else null
      dialog = new GetIncreaseFontSizeValueDialog(size)
      dialog.position @getDialogPosition rect

      # Listen for save events against the dialog
      dialog.addEventListener 'save', (ev) =>

        # Get color value
        @_fontSizeFactor = ev.detail().size

        modal.hide()
        dialog.hide()

        @_apply element, selection

        # Trigger the callback
        callback(true)

      app.attach modal
      app.attach dialog

      modal.show()
      dialog.show()
    else
      @_apply element, selection

    callback(true)

    # Dispatch `applied` event
    @dispatchEditorEvent('tool-applied', toolDetail)

  @getDialogPosition: (rect) ->
    [
      rect.left + (rect.width / 2) + window.scrollX,
      rect.top + (rect.height / 2) + window.scrollY
    ]

  @getNewFontSize: (styleClass) =>
    defaultFontSize = styleClass.getPropertyValue 'font-size'
    defaultFontSize = parseInt \
      defaultFontSize.slice 0, defaultFontSize.length - 2
    newFontSize = defaultFontSize + parseInt @_fontSizeFactor

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
    fontSizeCSSClassName = "font-size-#{ elementIndex }-#{ from }-#{ to }"
    fontSizeId = "font_size_#{ elementIndex }_#{ from }_#{ to }"

    styleClass = window.getComputedStyle element.domElement()
    @_newFontSize = @getNewFontSize styleClass

    if @isApplied element, selection

      style = document.getElementById fontSizeId

      styleClass = window.getComputedStyle \
        document.getElementsByClassName(fontSizeCSSClassName)[0]
      @_newFontSize = @getNewFontSize styleClass

      fontSizeCSSClass = """
        .#{ fontSizeCSSClassName } {
          font-size: #{ @_newFontSize }px;
        }
       """
      style.innerHTML = fontSizeCSSClass

      element.content = element.content.format(
        from,
        to,
        new HTMLString.Tag @tagName, {'class': fontSizeCSSClassName}
      )
      @_newFontSize += parseInt @_fontSizeFactor

      @showOnce = true

    else

      fontSizeCSSClass = """
        .#{ fontSizeCSSClassName } {
          font-size: #{ @_newFontSize }px;
        }
       """

      style = document.getElementById fontSizeId
      if style?
        style.innerHTML = fontSizeCSSClass
      else
        @setNewCSS fontSizeId, fontSizeCSSClass

      element.content = element.content.format(
        from,
        to,
        new HTMLString.Tag @tagName, {'class': fontSizeCSSClassName}
        )

      @showOnce = true

    element.content.optimize()
    element.updateInnerHTML()
    element.taint()

    element.restoreState()


class GetIncreaseFontSizeValueDialog extends ContentTools.LinkDialog

  # An anchored dialog to support inserting/modifying a increase font
  # size value

  constructor: (@size) ->
    super()

    @_defIncreaseFontSizeValue = '1'

  mount: () ->
    super()

    @size = if @size? then @size else @_defIncreaseFontSizeValue
    @_domInput.setAttribute 'name', 'size'
    @_domInput.setAttribute 'value', @size
    @_domInput.setAttribute 'placeholder', \
      ContentEdit._ 'Enter a font size increase factor (px)'

    # Remove the new window target DOM element
    @_domElement.removeChild @_domTargetButton

  save: () ->
    # Save the increase font size value.
    detail = {
      size: @_domInput.value.trim()
    }
    @dispatchEvent(@createEvent('save', detail))


ContentTools.DEFAULT_TOOLS[0].push('increase-font-size')
