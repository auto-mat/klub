class ButtonTool extends ContentTools.Tools.Bold
  # Insert/Remove a <a><button></button><a> tag.

  # Register the tool with the toolshelf
  ContentTools.ToolShelf.stow(@, 'button')

  # The tooltip and icon modifier CSS class for the tool
  @label = 'Button'
  @icon = 'button'

  # The Bold provides a tagName attribute we can override to make inheriting
  # from the class cleaner.
  @tagName = 'button'
  @wrapperParentTagName = 'a'

  @_btnCSSProp = {}

  @_btnHrefParentAttr = {target: '_blank'}
  @_btnHrefParentAttrDef = @_btnHrefParentAttr

  @_btnAttr = {onclick: 'btnClickListener(this)'}
  @_btnAttrDef = @_btnAttr

  @_openDialogDelay = 1000

  @apply: (element, selection, callback, btnHrefParentAttr, btnCSSStyle,
    btnCreate = true) ->
    # Apply the tool to the specified element and selection

    # Store the selection state of the element so we can restore it once done
    element.storeState()

    # Add a fake selection wrapper to the selected text so that it appears to be
    # selected when the focus is lost by the element.
    selectTag = new HTMLString.Tag 'span', {'class': 'ct--pseudo-select'}
    [from, to] = selection.get()

    # Add btn position
    @_btnAttr.position = "#{ from },#{ to }"

    element.content = element.content.format from, to, selectTag
    element.updateInnerHTML()

    # Set-up the dialog
    app = ContentTools.EditorApp.get()

    # Add an invisible modal that we'll use to detect if the user clicks away
    # from the dialog to close it.
    modal = new ContentTools.ModalUI transparent=true, allowScrolling=true

    # modal.addEventListener 'click', () ->
      # Close the dialog
      # @unmount()
      # dialog.hide()

      # Remove the fake selection from the element
      # element.content = element.content.unformat(from, to, selectTag)
      # element.updateInnerHTML()

      # Restore the real selection
      # element.restoreState()

      # Trigger the callback
      # callback(false)

    # Measure a rectangle of the content selected so we can position the
    # dialog centrally to it.
    domElement = element.domElement()
    measureSpan = domElement.getElementsByClassName 'ct--pseudo-select'
    rect = measureSpan[0].getBoundingClientRect()

    # Create background color dialog
    bgColorDialog = new GetBgColorDialog @getBgColor btnCSSStyle, \
      element, selection
    bgColorDialog.position @getDialogPosition rect

    # Create text color dialog
    textColorDialog = new GetTextColorDialog @getTextColor btnCSSStyle, \
      element,  selection
    textColorDialog.position @getDialogPosition rect

    # Create btn url link dialog
    hrefAttr = @getHrefAttr btnHrefParentAttr, element, selection
    targetAttr = @getTargetAttr btnHrefParentAttr, element, selection
    btnLinkDialog = new ContentTools.LinkDialog hrefAttr, targetAttr
    btnLinkDialog.position @getDialogPosition rect

    # Create padding dialog
    paddingDialog = new GetPaddindDialog @parsePaddingToInput \
      @getPadding btnCSSStyle, element, selection
    paddingDialog.position @getDialogPosition rect

    # Listen for save events against the dialog
    paddingDialog.addEventListener 'save', (ev) =>

      # Get link value
      padding = ev.detail().padding

      if padding
        cssProp = {'padding': @parsePaddingToCSS padding}
        @_btnCSSProp = @extendObj false, cssProp, @_btnCSSProp

      # Hide dialog
      paddingDialog.hide()

      # Show get btn link dialog
      @delay @_openDialogDelay, => @showDialog btnLinkDialog, false

      # Trigger the callback
      callback(true)

    # Listen for save events against the dialog
    btnLinkDialog.addEventListener 'save', (ev) =>

      # Get link value
      link = ev.detail().href

      if link
        @_btnHrefParentAttr = @extendObj false, {'href': link}, \
          @_btnHrefParentAttr

      # Insert btn element
      applyBtn()

      # Trigger the callback
      callback(true)

    # Listen for save events against the dialog
    textColorDialog.addEventListener 'save', (ev) =>

      # Get color value
      color = ev.detail().color

      if color
        @_btnCSSProp = @extendObj false, {'color': color}, @_btnCSSProp

      # Hide dialog
      textColorDialog.hide()

      # Show get btn link dialog
      @delay @_openDialogDelay, => @showDialog paddingDialog, false

      # Trigger the callback
      callback(true)

    # Listen for save events against the dialog
    bgColorDialog.addEventListener 'save', (ev) =>

      # Get color value
      color = ev.detail().color

      if color
        @_btnCSSProp = @extendObj false, {'background-color': color}, \
          @_btnCSSProp

      # Hide dialog
      bgColorDialog.hide()

      # Show get text color dialog
      @delay @_openDialogDelay, => @showDialog textColorDialog

      # Trigger the callback
      callback(true)

    applyBtn = () =>
      # Clear any existing link
      element.content = element.content.unformat from, to, @tagName
      element.content = element.content.unformat from, to, @wrapperParentTagName

      if Object.keys(@_btnCSSProp).length > 0

        # Btn href parent elelement
        btnHrefParent = new HTMLString.Tag @wrapperParentTagName, \
          @_btnHrefParentAttr
        element.content = element.content.format from, to, btnHrefParent

        # Btn element
        btn = new HTMLString.Tag @tagName, @extendObj(false, \
          @_btnAttr, @getCCCStr(@_btnCSSProp))
        element.content = element.content.format from, to, btn

      element.updateInnerHTML()
      element.taint()

      # Close the modal and dialog
      modal.unmount()
      btnLinkDialog.hide()

      # Remove the fake selection from the element
      element.content = element.content.unformat from, to, selectTag
      element.updateInnerHTML()

      # Restore the real selection
      element.restoreState()

      # Reset btn prop
      @_btnCSSProp = {}
      @_btnAttr = {}
      @_btnHrefParentAttr = @_btnHrefParentAttrDef
      @_btnAttr = @_btnAttrDef

      # Add btn listener
      # @addBtnListener(element)

      selection = window.getSelection()
      selection.removeAllRanges()

    app.attach modal
    app.attach bgColorDialog
    app.attach textColorDialog
    app.attach paddingDialog
    app.attach btnLinkDialog

    modal.show()
    bgColorDialog.show()

    # Initialize color picker
    @initColorPicker 'input.color'

  window.btnClickListener = (evt) =>
    # Click on btn element

    editor = ContentTools.EditorApp.get()

    # Prevent deafult if editor is not in editing mode
    if editor.isEditing() is true
      # Get evt target
      btn = evt
      btnText = btn.innerText

      # Create btn text node
      btnToText = document.createTextNode btnText

      # Replace btn node with text
      btnParent = btn.parentElement
      btnHrefParent = btnParent.parentElement

      # Get position
      [from, to] = btn.getAttribute('position').split ','

      # Get btn css prop
      btnCSSStyle = @getBtnCSSProp btn

      # Get btn attr
      link = btnParent.getAttribute 'href'
      btnHrefParentAttr = @extendObj false, {'href': link}, \
        @_btnHrefParentAttrDef

      # Replace btn with btn text node
      btnHrefParent.replaceChild btnToText, btnParent

      # Create selection range
      range = new ContentSelect.Range parseInt(from), parseInt(to)
      range.select btnHrefParent

      # Get selected text element
      element = ContentEdit.Root.get().focused()

      selection = null
      if element and element.selection
        selection = element.selection()
      [from, to] = selection.get()

      callback = () ->

      # Apply tool
      @apply element, selection, callback, btnHrefParentAttr, \
        btnCSSStyle, false

      # @addBtnListener: (element) ->
      # btns = element.domElement().getElementsByTagName('button')

      # for btn in btns
      # btn.addEventListener 'click', @btnClickListener

  @getBgColor: (btnCSSStyle, element, selection,
    cssPropName = 'background-color') ->
    # Get CSS bg color prop value
    if btnCSSStyle?
      btnCSSStyle[cssPropName]
    else @getCSSStyle(cssPropName, element, selection, @tagName)

  @getTextColor: (btnCSSStyle, element, selection, cssPropName = 'color') ->
    # Get CSS color prop value
    if btnCSSStyle?
      btnCSSStyle[cssPropName]
    else @getCSSStyle(cssPropName, element, selection, @tagName)

  @getHrefAttr: (tnHrefParentAttr, element, selection, attrName = 'href') ->
    # Get href attr value
    if btnHrefParentAttr?
      btnHrefParentAttr[attrName]
    else @getAttr(attrName, element, selection, 'a')

  @getTargetAttr: (btnHrefParentAttr, element, selection,
    attrName = 'target') ->
    # Get target attr value
    if btnHrefParentAttr?
      btnHrefParentAttr[attrName]
    else @getAttr(attrName, element, selection, 'a')

  @getPadding: (btnCSSStyle, element, selection, cssPropName = 'padding') ->
    # Get CSS padding prop value
    if btnCSSStyle?
      btnCSSStyle[cssPropName]
    else @getCSSStyle(cssPropName, element, selection, @tagName)

  @getCCCStr: (cssProp) ->
    prop = []

    for k, v of cssProp
      prop.push "#{ k }:#{ v }"

    {'style': prop.join ';'}

  @getBtnCSSProp: (element) ->
    # Get btn css prop
    cssStyle =
    'color': @getColorCSSProp 'color', element
    'background-color': @getColorCSSProp 'background-color', element
    'padding': @getPaddingCSSProp @getCSSProp 'padding', element

    cssStyle

  @getColorCSSProp: (propName, element) ->
    # Convert rgb(255, 255, 255) to the #ffffff format
    regExp = /\(([^)]+)\)/
    color = element.style[propName]

    if color.length > 0
      [r, g, b] = regExp.exec(color)[1].split ','
      return @rgbToHex parseInt(r), parseInt(g), parseInt(b)

    return ''

  @getCSSProp: (propName, element) ->
    element.style[propName]

  @getPaddingCSSProp: (prop) ->
    # If padding is same in every direction
    # set two same padding value in return string
    propSplit = prop.split ' '
    return if propSplit.length > 1 then prop else [prop, prop].join ' '

  @parsePaddingToCSS: (value) ->
    # Append padding unit
    paddingUnit = []

    padding = value.replace(/\s/g, '').split ','
    addUnit = (value, unit='px') -> paddingUnit.push "#{ value }#{ unit }"
    addUnit value for value in padding

    paddingUnit.join(' ')

  @parsePaddingToInput: (value) ->
    # Remove padding unit
    padding = value.replace(/px/g, '').split ' '
    padding.join ', '

  @getDialogPosition: (rect) ->
    [
      rect.left + (rect.width / 2) + window.scrollX,
      rect.top + (rect.height / 2) + window.scrollY
    ]

  @delay = (ms, func) -> setTimeout func, ms

  @showDialog: (dialog, colorPicker = true) ->
    # Show dialog
    dialog.show()

    # Initialize color picker
    if colorPicker
      @initColorPicker 'input.color'

  @initColorPicker: (selector) ->
    # Initialize color picker
    initial = (elm, colors) ->
      elm.style.backgroundColor = elm.value
      elm.style.color = if colors.rgbaMixBG.luminance > 0.22 \
        then '#222' else '#ddd'

    jsColorPicker(selector, {
      memoryColors: @getAutomatColors(),
      init: initial
      })

  @getAutomatColors: () ->
    # Default Automat colors
    red = {r: 233, g: 76, b: 77, a: 1.0}
    green = {r: 174, g: 216, b: 198, a: 1.0}
    purple = {r: 69, g: 56, b: 142, a: 1.0}
    [red, purple, green]

  @rgbToHex: (r, g, b) ->
    "##{ ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1) }"

  @getHexFormat: (rgba) ->
    @rgbToHex(rgba.r, rgba.g, rgba.b)

  @getCSSStyle: (cssPropName, element, selection, childElement) ->
    # Return any existing style value for the element and selection
    # Find the first character in the selected text that has a
    # `childElement` tag and
    # return its `cssPropName` value.

    [from, to] = selection.get()
    selectedContent = element.content.slice from, to

    for c in selectedContent.characters
      # Does this character have a button tag applied?
      if not c.hasTags childElement
        continue

      # Find the button tag and return the attribute value
      for tag in c.tags()
        if tag.name() == childElement
          return tag.style cssPropName

    return ''

  @getAttr: (attrName, element, selection, childElement) ->
    # Return any existing attribute value for the element and selection
    # Find the first character in the selected text that has a
    # `childElement` tag and
    # return its `attrName` value.

    [from, to] = selection.get()
    selectedContent = element.content.slice from, to

    for c in selectedContent.characters
      # Does this character have a time tag applied?
      if not c.hasTags childElement
        continue

      # Find the time tag and return the datetime attribute value
      for tag in c.tags()
        if tag.name() == childElement
          return tag.attr attrName

    return ''

  @extendObj: (deep, objs...) ->
    extended = {}

    # Merge the object into the extended object
    merge = (obj) ->

      for prop in Object.keys obj

        if Object.prototype.hasOwnProperty.call obj, prop

          # If deep merge and property is an object, merge properties
          if (
            deep and
            Object.prototype.toString.call obj[prop] is '[object Object]'
          )
            extended[prop] = @extendObj true, extended[prop], obj[prop]
          else
            extended[prop] = obj[prop]

    # Loop through each object and conduct a merge
    for obj in objs
      merge obj

    return extended


class GetBgColorDialog extends ContentTools.LinkDialog

  # An anchored dialog to support inserting/modifying a
  # background css color prop value

  constructor: (color) ->
    @_color = color

    super()

  mount: () ->
    super()

    # Update the name and placeholder for the input field provided by the
    # link dialog.
    cssClass = @_domInput.getAttribute 'class'
    colorPickerCssClass = 'color'
    color = if @_color then @_color else \
      ButtonTool.getHexFormat ButtonTool.getAutomatColors()[1]
    # purpleColor = ButtonTool.getHexFormat ButtonTool.getAutomatColors()[1]

    @_domInput.setAttribute 'name', 'color'
    @_domInput.setAttribute 'class', "#{ cssClass } #{ colorPickerCssClass }"
    @_domInput.setAttribute 'value', color
    @_domInput.setAttribute 'placeholder', ContentEdit._ \
      'Enter a background color'

    # Remove the new window target DOM element
    @_domElement.removeChild @_domTargetButton

  save: () ->
    # Save the bg color.
    detail = {
      color: @_domInput.value.trim()
    }
    @dispatchEvent(@createEvent('save', detail))

  show: () ->
    super()
    # Once visible automatically unfocus to the color input
    @_domInput.blur()


class GetTextColorDialog extends GetBgColorDialog

  # An anchored dialog to support inserting/modifying a
  # text-color css color prop value

  mount: () ->
    super()

    defTextColor = '#ffffff'

    color = if @_color then @_color else defTextColor
    @_domInput.setAttribute 'value', color

    @_domInput.setAttribute 'placeholder', ContentEdit._ 'Enter a text color'


class GetPaddindDialog extends ContentTools.LinkDialog

  # An anchored dialog to support inserting/modifying a padding css prop value

  constructor: (@padding) ->
    super()

    @_defPadding = '20, 20'

  mount: () ->
    super()

    # Update the name and placeholder for the input field provided by the
    # link dialog.

    @padding = if @padding then @padding else @_defPadding
    @_domInput.setAttribute 'name', 'padding'
    @_domInput.setAttribute 'value', @padding
    @_domInput.setAttribute 'placeholder', \
      ContentEdit._ 'Enter a button padding space'

    # Remove the new window target DOM element
    @_domElement.removeChild @_domTargetButton

  save: () ->
    # Save the padding.
    detail = {
      padding: @_domInput.value.trim()
    }
    @dispatchEvent(@createEvent('save', detail))


ContentTools.DEFAULT_TOOLS[0].push('button')
