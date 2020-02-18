class BackgroundImageDialog extends SuperClass

  @include ContentTools.DialogUI
  @include ContentTools.ImageDialog 

  constructor: () ->
    ContentTools.ImageDialog.call @
    
  mount: () ->
    ContentTools.DialogUI::mount.call @

    # Update dialog class
    ContentEdit.addCSSClass(@_domElement, 'ct-image-dialog')
    ContentEdit.addCSSClass(@_domElement, 'ct-image-dialog--empty')

    # Update view class
    ContentEdit.addCSSClass(@_domView, 'ct-image-dialog__view')

    # Add controls

    # Image tools & progress bar
    domTools = @constructor.createDiv(
      ['ct-control-group', 'ct-control-group--left'])
    @_domControls.appendChild(domTools)

    # Rotate CCW
    @_domRotateCCW = @constructor.createDiv([
      'ct-control',
      'ct-control--icon',
      'ct-control--rotate-ccw'
      ])
    @_domRotateCCW.setAttribute(
      'data-ct-tooltip',
      ContentEdit._('Rotate') + ' -90°'
    )
    domTools.appendChild(@_domRotateCCW)

    # Rotate CW
    @_domRotateCW = @constructor.createDiv([
      'ct-control',
      'ct-control--icon',
      'ct-control--rotate-cw'
    ])
    @_domRotateCW.setAttribute(
      'data-ct-tooltip',
      ContentEdit._('Rotate') + ' 90°'
    )
    domTools.appendChild(@_domRotateCW)

    # Rotate CW
    @_domCrop = @constructor.createDiv([
      'ct-control',
      'ct-control--icon',
      'ct-control--crop'
      ])
    @_domCrop.setAttribute('data-ct-tooltip', ContentEdit._('Crop marks'))
    domTools.appendChild(@_domCrop)

    # Progress bar
    domProgressBar = @constructor.createDiv(['ct-progress-bar'])
    domTools.appendChild(domProgressBar)

    @_domProgress = @constructor.createDiv(['ct-progress-bar__progress'])
    domProgressBar.appendChild(@_domProgress)

    # Actions
    domActions = @constructor.createDiv(
      ['ct-control-group', 'ct-control-group--right'])
    @_domControls.appendChild(domActions)

    # Upload button
    @_domUpload = @constructor.createDiv([
      'ct-control',
      'ct-control--text',
      'ct-control--upload'
      ])
    @_domUpload.textContent = ContentEdit._('Upload')
    domActions.appendChild(@_domUpload)

    # File input for upload
    @_domInput = document.createElement('input')
    @_domInput.setAttribute('class', 'ct-image-dialog__file-upload')
    @_domInput.setAttribute('name', 'file')
    @_domInput.setAttribute('type', 'file')
    @_domInput.setAttribute('accept', 'image/*')
    @_domUpload.appendChild(@_domInput)

    # Insert
    @_domInsert = @constructor.createDiv([
      'ct-control',
      'ct-control--text',
      'ct-control--insert'
      ])
    @_domInsert.textContent = ContentEdit._('Insert')
    domActions.appendChild(@_domInsert)

    # Cancel
    @_domCancelUpload = @constructor.createDiv([
      'ct-control',
      'ct-control--text',
      'ct-control--cancel'
      ])
    @_domCancelUpload.textContent = ContentEdit._('Cancel')
    domActions.appendChild(@_domCancelUpload)

    # Clear
    @_domClear = @constructor.createDiv([
      'ct-control',
      'ct-control--text',
      'ct-control--clear'
      ])
    @_domClear.textContent = ContentEdit._('Clear')
    domActions.appendChild(@_domClear)

    # Add interaction handlers
    @_addDOMEventListeners()

    @dispatchEvent(@createEvent('imageuploader.mount'))

  save: (imageURL, imageSize, imageAttrs) ->
    # Save and insert the current image
    # Set correct container height according uploaded image
    document.getElementsByClassName('content-table')[0].setAttribute('height', "#{ imageSize[1] }")
    @dispatchEvent(
      @createEvent(
        'save',
          {
            'imageURL': imageURL,
            'imageSize': imageSize,
            'imageAttrs': imageAttrs
          })
    )

  _addDOMEventListeners: () ->
    # Add event listeners for the widget

    # Call add base class event listener
    ContentTools.DialogUI::_addDOMEventListeners.call @

    # File ready for upload
    @_domInput.addEventListener 'change', (ev) =>

      # Get the file uploaded
      file = ev.target.files[0]

      # Ignore empty file changes (this may occur when we change the
      # value of the input field to '', see issue:
      # https://github.com/GetmeUK/ContentTools/issues/385
      unless file
        return

      # Clear the file inputs value so that the same file can be uploaded
      # again if the user cancels the upload or clears it and starts then
      # changes their mind.
      ev.target.value = ''
      if ev.target.value
        # Hack for clearing the file field value in IE
        ev.target.type = 'text'
        ev.target.type = 'file'

      ###
      # Set backgroundImage property
      ###
      @dispatchEvent(
        @createEvent('imageuploader.fileready', {file: file, backgroundImage: true})
      )

    # Cancel upload
    @_domCancelUpload.addEventListener 'click', (ev) =>
      @dispatchEvent(@createEvent('imageuploader.cancelupload'))

    # Clear image
    @_domClear.addEventListener 'click', (ev) =>
      @removeCropMarks()
      @dispatchEvent(@createEvent('imageuploader.clear'))

    # Rotate the image
    @_domRotateCCW.addEventListener 'click', (ev) =>
      @removeCropMarks()
      @dispatchEvent(@createEvent('imageuploader.rotateccw'))

    @_domRotateCW.addEventListener 'click', (ev) =>
      @removeCropMarks()
      @dispatchEvent(@createEvent('imageuploader.rotatecw'))

    @_domCrop.addEventListener 'click', (ev) =>
      if @_cropMarks
        @removeCropMarks()

      else
        @addCropMarks()

    @_domInsert.addEventListener 'click', (ev) =>
      @_setEmailTemplateBgImage('content-table')
      @dispatchEvent(@createEvent('imageuploader.save'))

  _setEmailTemplateBgImage: (containerClassName) ->
    ###
    # Set html email template container background image 
    ### 
    container = document.getElementsByClassName(containerClassName)[0]
    container.style.backgroundImage = "url(#{ @_imageURL })"


class BackgroundImage extends ContentTools.Tools.Image

  # Insert an image.

  ContentTools.ToolShelf.stow(@, 'background-image')

  @label = 'Background image'
  @icon = 'background-image'

  @canApply: (element, selection) ->
    # Return true if the tool can be applied to the current
    # element/selection.
    if element.isFixed()
      unless element.type() is 'ImageFixture'
        return false
    return true

  @apply: (element, selection, callback) ->

    # Dispatch `apply` event
    toolDetail = {
      'tool': this,
      'element': element,
      'selection': selection
    }
    if not @dispatchEditorEvent('tool-apply', toolDetail)
      return

    # If supported allow store the state for restoring once the dialog is
    # cancelled.
    if element.storeState
      element.storeState()

    # Set-up the dialog
    app = ContentTools.EditorApp.get()

    # Modal
    modal = new ContentTools.ModalUI()

    # Dialog
    dialog = new BackgroundImageDialog()

    # Support cancelling the dialog
    dialog.addEventListener 'cancel', () =>

      modal.hide()
      dialog.hide()

      if element.restoreState
        element.restoreState()

      callback(false)

    # Support saving the dialog
    dialog.addEventListener 'save', (ev) =>
      detail = ev.detail()
      imageURL = detail.imageURL

      if element.type() is 'ImageFixture'
        # Configure the image source against the fixture
        element.src(imageURL)

      modal.hide()
      dialog.hide()

      callback(true)
      # Dispatch `applied` event
      @dispatchEditorEvent('tool-applied', toolDetail)

    # Show the dialog
    app.attach(modal)
    app.attach(dialog)
    modal.show()
    dialog.show()


index = ContentTools.DEFAULT_TOOLS[2].indexOf('image')

ContentTools.DEFAULT_TOOLS[2].splice(index + 1, 0, 'background-image')