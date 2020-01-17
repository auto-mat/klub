###
  EditTemplateModalDialog class
###

class EditTemplateModalDialog extends FormatSelectorMixin

  constructor: (
    dialogId,
    popoverEditTemplateLinkElementId,
    $editTemplateModalDialogPageContainer,
    $hiddenTemplateField,
    $templateDivField,
  ) ->

    @_dialogId = dialogId

    @_sessionStorageKey = 'dbTemplateName'

    @_popoverEditTemplateLinkElementId = popoverEditTemplateLinkElementId

    @_closeBtnClass = 'mdl-close'

    @_$editTemplateModalDialogPageContainer = $editTemplateModalDialogPageContainer

    @_$hiddenTemplateField = $hiddenTemplateField

    @_$templateDivField = $templateDivField

    @_popoverDialog = null

  mount: (templateName, openType, templateType) ->

    sessionStorage.removeItem @_sessionStorageKey

    # if openType is 'openViaSelectBox'

    if !@_popoverDialog
      # Append popover edit dialog content
      # needed for correct dialog initialization
      @_popoverDialog = PopoverModalDialog.getContent(
        @_popoverEditTemplateLinkElementId,
        @getIdFormat @_dialogId
        )

      $('body').append @_popoverDialog 

    # Initialize dialog
    @init @getIdFormat @_popoverEditTemplateLinkElementId

    # Set html template page container attr
    if templateType.length > 1
      url = @_setPageContainerArgs templateName, 'aklub:get_email_template_from_db'
      sessionStorage.setItem @sessionStorageKey, url
    else
      url = @_setPageContainerArgs templateName, 'aklub:get_email_template'

    # Show dialog
    @show @getIdFormat @_dialogId

    # Bind close modal template dialog event
    $closeBtn = $ "#{ @getIdFormat @_dialogId } #{ @getClassFormat @_closeBtnClass }"
    $closeBtn.off 'click', @_closeEditTemplateModalDialog
    $closeBtn.on 'click', @_closeEditTemplateModalDialog

    # Remove popover edit dialog content
    if openType is 'openViaSelectBox'
      $(@getIdFormat @_popoverEditTemplateLinkElementId).remove()

  _closeEditTemplateModalDialog: (evt) =>

    templatePageHtlmDoc = @_getIframeTemplateContent()

    processHtmlTemplate = new PostProcessHtmlTemplate(
      templatePageHtlmDoc,
      $(templatePageHtlmDoc).find('article'),
      @_$templateDivField,
      @_$hiddenTemplateField
    )

  _getIframeTemplateContent: () ->
    templatePage = document.querySelector @getIdFormat @_$editTemplateModalDialogPageContainer.attr 'id'
    templatePage?.contentDocument

  _setPageContainerArgs: (templateName, urlName) ->
    # Set html template page container attr
    url = window.reverse urlName, {template_name: templateName}

    attr = 
      data: url,
      width: $(window).width(),
      height: $(window).height()

    @_$editTemplateModalDialogPageContainer.attr attr

    return url

  init: (elementId) ->
    $(elementId).mdl()

  show: (elementId) ->
    mdl_open(elementId)

