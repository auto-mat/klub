###
  PopoverModalDialog class
###

class PopoverModalDialog extends FormatSelectorMixin

  @editTemplateLinkText = gettext('Edit template')
  
  constructor: (
    title,
    backdrop,
    editTemplateModalDialogId,
    $templateNameField,
    destroyDelay,
    $mountElement,
    popoverModalDialogEditTemplateLinkElementId,
    $editTemplateModalDialogPageContainer,
    $hiddenTemplateField,
  ) ->

    @_title = title

    @_editTemplateModalDialogId = editTemplateModalDialogId

    @_backdrop = backdrop

    @_$templateNameField = $templateNameField

    @_destroyDelay = destroyDelay

    @_$mountElement = $mountElement

    @_popoverModalDialogEditTemplateLinkElementId = popoverModalDialogEditTemplateLinkElementId

    @_$editTemplateModalDialogPageContainer = $editTemplateModalDialogPageContainer

    @_$hiddenTemplateField = $hiddenTemplateField

    @_$templateDivField = $mountElement


  show: (element) ->

    element.click (evt) =>

      evt.preventDefault()
      
      templateNameSelectedOpt = @_$templateNameField.find('option:selected')
      templateName = templateNameSelectedOpt.text()
      templateType = templateNameSelectedOpt.val().split(':')

      # Show edit template modal dialog
      dialog = new EditTemplateModalDialog(
        @_editTemplateModalDialogId, 
        @_popoverModalDialogEditTemplateLinkElementId,
        @_$editTemplateModalDialogPageContainer,
        @_$hiddenTemplateField,
        @_$templateDivField
        )
    
      dialog.mount templateName, 'openViaPopoverDialog', templateType

      # Destroy popover dialog
      @unmount()

   # Destroy dialog
    @delay @_destroyDelay, => @unmount()

  mount: (offsetTop, offsetLeft) ->

    opts = @_getOpt()
    opts.offsetTop = offsetTop
    opts.offsetLeft = offsetLeft

    WebuiPopovers.show(@_$mountElement, opts)

  unmount: () ->

    @_$mountElement.webuiPopover('hide')
    @_$mountElement.webuiPopover('destroy')

  delay: (ms, func) -> setTimeout func, ms

  @getContent: (popoverModalDialogEditTemplateLinkElementId, editTemplateModalDialogId) ->

    $element = $ '<a></a>'
    $element.attr
      id: @dialogId,
      href: ''

    editTemplateModalDialogAttr =
      id: popoverModalDialogEditTemplateLinkElementId,
      'data-type': 'modal',
      'data-target': editTemplateModalDialogId,
      'data-fullscreen': 'true',
      'data-overlayClick': 'true'

    $element.attr editTemplateModalDialogAttr
    $element.html "<b>#{ @editTemplateLinkText }</b>"
    return $element

  _getOpt: () ->

    show = (element) =>
      @show element

    content = PopoverModalDialog.getContent(
      @_popoverModalDialogEditTemplateLinkElementId, 
      @getIdFormat @_editTemplateModalDialogId
      )

    opt =
      placement: 'top-right',
      trigger: 'manual,'
      title: @_title,
      content: content,
      offsetTop: 0,
      offsetLeft: 0,
      animation: 'fade'
      backdrop: @_backdrop,
      onShow: show

