###
  GetTemplateNameDialog class
###

class GetTemplateNameDialog extends FormatSelectorMixin

  constructor: (
    showDelay,
    $templateDivField,
    templateNameFieldId,
    editTemplateModalDialogId,
    popoverModalDialogEditTemplateLinkElementId,
    templateName,
    $editTemplateModalDialogPageContainer,
    $hiddenTemplateField,
  ) ->

    @_dialogId = 'get_template_name'

    @_title = gettext('Template name')

    @_showDelay  = showDelay

    @_confirmBtnId = 'confirm_btn'

    @_$templateDivField = $templateDivField

    @_templateNameInputId = 'template_name'

    @_errorListCSSClass = 'errorlist'

    @_templateNameFieldId = templateNameFieldId

    @_newEmptyTemplateName = null

    @_editTemplateModalDialogId = editTemplateModalDialogId

    @_popoverModalDialogEditTemplateLinkElementId = popoverModalDialogEditTemplateLinkElementId

    @_templateName = templateName

    @_$editTemplateModalDialogPageContainer = $editTemplateModalDialogPageContainer

    @_$hiddenTemplateField = $hiddenTemplateField

  unmount: () ->
    $(@getIdFormat @_dialogId).dialog('destroy')

  mount: () ->
    @_getContainer().dialog @_getOpt()

  _getContainer: () ->
    divContainer = $ '<div></div>'
    divContainer.attr {id:  @_dialogId}

    form = $ '<form></form>'
    form.attr {id: 'template_name_form'}

    $formContentContainer = $ '<div></div>'

    $formErrorListContainer = $ '<ul></ul>'
    $formErrorListContainer.attr {class: @_errorListCSSClass}

    $formContentLabel = $ '<label></label>'
    $formContentLabel.attr {for: @_templateNameInputId}
    $formContentLabel.text gettext 'Template name'

    $formContentInput = $ '<input>'
    $formContentInput.attr {id: @_templateNameInputId, name: @_templateNameInputId}

    $formContentContainer.append($formContentLabel)
    $formContentContainer.append($formContentInput)
    $formContentContainer.append($formErrorListContainer)

    divContainer.append(form.append($formContentContainer))

    return divContainer

  getNeEmptyTemplateName: () ->
    @_newEmptyTemplateName

  _triggerConfirmBtn: () ->
    # Trigger click on confirm btn
    triggerEvt = (evt) =>
      if evt.keyCode is $.ui.keyCode.ENTER
        $(@getIdFormat @_confirmBtnId).click()

    $(@getIdFormat @_dialogId).keypress triggerEvt

  _checkRegexp: (o, regexp, m) ->
    if not regexp.test(o.val())
      errorList = o.closest('form').find @getClassFormat @_errorListCSSClass
      errorList.append "<li>#{ m }</li>"
      return false
    else
      return true

  _checkTemplateName: (o, name, m) ->
    opts = []
    $("#{ @getIdFormat @_templateNameFieldId } > option").each () -> opts.push($(@).text())

    if opts.indexOf(name) > -1
      errorList = o.closest('form').find @getClassFormat @_errorListCSSClass
      errorList.append("<li>#{ m }</li>")
      return false
    else
      return true

  _validateTemplateName: () ->
    # Validate template name
    valid = true
    $templateName = $ @getIdFormat @_templateNameInputId
    $(@getClassFormat @_errorListCSSClass).html ''

    message = gettext('Template name may consist of a-z, 0-9, ' +
                      'underscores, not spaces and must begin with a letter,' +
                      'and be lowercase.')
    valid = valid and @_checkRegexp $templateName, /^[a-z]([0-9a-z_])+$/, message

    message = gettext 'Template name exist.'
    $templateNameInput = $ @getIdFormat @_templateNameInputId

    valid = valid and @_checkTemplateName $templateNameInput, $templateName.val(), message

    return valid

  _confirmTemplateName: () =>
    valid = @_validateTemplateName()

    if valid
      @_newEmptyTemplateName = $(@getIdFormat @_templateNameInputId).val()

      # Destroy dialog
      @unmount()

      @_setNewEmptyTemplateName()

      templateType = [@_newEmptyTemplateName]

      # Show edit template modal dialog
      dialog = new EditTemplateModalDialog(
        @_editTemplateModalDialogId,
        @_popoverModalDialogEditTemplateLinkElementId,
        @_$editTemplateModalDialogPageContainer,
        @_$hiddenTemplateField,
        @_$templateDivField
        )

      dialog.mount @_templateName, 'openViaSelectBox', templateType

  _setNewEmptyTemplateName: () ->
    if @_newEmptyTemplateName?
      sessionStorage.setItem('newEmptyTemplateName', @_newEmptyTemplateName)

  _getBtns: () =>
    # Get dialog buttons
    btnNames = {}

    okBtnClick = () =>
      @_confirmTemplateName()

    btnNames.ok = 
      text: gettext('Ok'),
      id: @_confirmBtnId,
      click: okBtnClick

    return btnNames

  _getOpt: () ->
    # Get dialog option

    open = (evt, ui) =>
      @_triggerConfirmBtn()

    close = (evt, ui) =>
      @unmount()
      @_$templateDivField.html('')

    opt =
      modal: true,
      title: @_title,
      show:
        effect: 'fade',
        delay: @_showDelay,
      resizable: false
      open: open,
      beforeClose: close
      buttons: @_getBtns()

    return opt
