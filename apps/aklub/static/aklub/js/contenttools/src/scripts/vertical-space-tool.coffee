class VerticalSpace extends ContentTools.Tool

  # Insert a vertical space in to the current element at the specified
  # selection.

  ContentTools.ToolShelf.stow(@, 'vertical-space')

  @label = 'Add vertical space'
  @icon = 'vertical-space'

  @canApply: (element, selection) ->
    # Return true if the tool can be applied to the current
    # element/selection.
    return element.content

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

    # Set-up the dialog
    app = ContentTools.EditorApp.get()

    # Add an invisible modal that we'll use to detect if the user clicks away
    # from the dialog to close it.
    modal = new ContentTools.ModalUI transparent=true, allowScrolling=true

    # Measure a rectangle of the content selected so we can position the
    # dialog centrally to it.
    domElement = element.domElement()
    rect = domElement.getBoundingClientRect()

    # Create vertical space dialog
    verticalSpaceDialog = new GetVerticalSpaceDialog()
    verticalSpaceDialog.position @getDialogPosition rect

    # Listen for save events against the dialog
    verticalSpaceDialog.addEventListener 'save', (ev) =>

      # Get link value
      verticalSpace = ev.detail().verticalSpace

      if verticalSpace
        @_insertSpace(verticalSpace, element, selection)

      # Hide modal/dialog
      modal.unmount()
      verticalSpaceDialog.hide()

      # Trigger the callback
      callback(true)

    app.attach modal
    app.attach verticalSpaceDialog

    modal.show()
    verticalSpaceDialog.show()

    callback(true)

  @_insertSpace: (verticalSpace, element, selection, toolDetail) ->
    # Insert a table at the current in index
    cursor = selection.get()[0] + 1

    tip = element.content.substring(0, selection.get()[0])
    tail = element.content.substring(selection.get()[1])

    tdContent="vertical space: #{ verticalSpace } px"

    tableHtmlString = "<table cellspacing='0' cellpadding='0' border='0'" +
      " class='vertical-space'><tbody><tr>" +
      "<td style='border:none;padding:0' height='#{ verticalSpace }'>" +
      "<center><b>vertical space</b></center></td></tr></tbody></table>"

    table = new HTMLString.String(
      tableHtmlString,
      element.content.preserveWhitespace()
    )
    element.content = tip.concat(table, tail)
    element.updateInnerHTML()
    element.taint()

    # Restore the selection
    selection.set(cursor, cursor)
    element.selection(selection)


    # Dispatch `applied` event
    @dispatchEditorEvent('tool-applied', toolDetail)

    element = ContentEdit.Root.get().focused()

    # If the element isn't a text element find the nearest top level
    # node and insert a new paragraph element after it.
    if element.parent().type() != 'Region'
      element = element.closest (node) ->
        return node.parent().type() is 'Region'

    region = element.parent()
    paragraph = new ContentEdit.Text('p')
    region.attach(paragraph, region.children.indexOf(element) + 1, false)

    # Give the newely inserted paragraph focus
    paragraph.focus()

  @getDialogPosition: (rect) ->
    [
      rect.left + (rect.width / 2) + window.scrollX,
      rect.top + (rect.height / 2) + window.scrollY
    ]


class GetVerticalSpaceDialog extends ContentTools.LinkDialog

  # An anchored dialog to support inserting/modifying a vertical space
  # px unit

  constructor: (@verticalSpace) ->
    super()

    @_defVerticalSpace = '10'

  mount: () ->
    super()

    # Update the name and placeholder for the input field provided by the
    # link dialog.

    @verticalSpace = if @verticalSpace then @verticalSpace else \
      @_defVerticalSpace
    @_domInput.setAttribute 'name', 'verticalSpace'
    @_domInput.setAttribute 'value', @verticalSpace
    @_domInput.setAttribute 'placeholder', \
      ContentEdit._ 'Enter a vertical space (px)'

    # Remove the new window target DOM element
    @_domElement.removeChild @_domTargetButton

  save: () ->
    # Save the padding.
    detail = {
      verticalSpace: @_domInput.value.trim()
    }
    @dispatchEvent(@createEvent('save', detail))


index = ContentTools.DEFAULT_TOOLS[2].indexOf('line-break')

ContentTools.DEFAULT_TOOLS[2].splice(index + 1, 0, 'vertical-space')
