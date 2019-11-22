class HtmlTemplateFormFieldWidget

  constructor: (
    editTemplateModalDialogId,
    popoverModalDialogEditTemplateLinkElementId,
    getTemplateNameDialogShowDelay,
    templateNameFieldId,
    templateTypeFieldId,
    hiddenTemplateFieldId,
    templateDivFormFieldContainerCSSClass,
    templateTextAreaFormFieldContainerCSSClass,
    templateTextareaFieldId,
    editTemplateModalDialogPageContainerId,
    templateDivFieldId,
    showPopoverModalDialogDelay,
    popoverModalDialogBackDrop,
    popoverModalDialogDestroyDelay
  ) ->

    @_templateDivFieldId = templateDivFieldId

    @_hiddenTemplateFieldId = hiddenTemplateFieldId

    @_templateNameFieldId = templateNameFieldId

    @_getTemplateNameDialogShowDelay = getTemplateNameDialogShowDelay

    @_editTemplateModalDialogId = editTemplateModalDialogId

    @_popoverModalDialogEditTemplateLinkElementId = popoverModalDialogEditTemplateLinkElementId

    @_templateDivFormFieldContainerCSSClass = templateDivFormFieldContainerCSSClass

    @_templateTextareaFieldId = templateTextareaFieldId 

    @_editTemplateModalDialogPageContainerId = editTemplateModalDialogPageContainerId

    @_$templateDivFieldContainer = null

    @_$templateTextareaFieldContainer = null

    @_templateTextareaFieldValue = ''

    @_showPopoverModalDialogDelay = showPopoverModalDialogDelay

    @_popoverModalDialogBackDrop = popoverModalDialogBackDrop

    @_popoverModalDialogDestroyDelay = popoverModalDialogDestroyDelay

    @_templateTextAreaFormFieldContainerCSSClass = templateTextAreaFormFieldContainerCSSClass

    @_templateTypeFieldId = templateTypeFieldId

    @_newEmptyTemplateName = null

    @_getTemplateNameDialog = null
    
    @_popoverDialogOpts = null

    # Methods
    @_cacheDom()

    @_bindEvents()

    @_bindPopoverDialogMouseMoveEvt()

    @_templateFormFieldWidgetInit()

  _cacheDom: () ->
    @_$templateDivField = $ @getIdFormat @_templateDivFieldId
    @_$hiddenTemplateField = $ @getIdFormat @_hiddenTemplateFieldId
    @_$templateNameField = $ @getIdFormat @_templateNameFieldId
    @_$templateTypeField = $ @getIdFormat @_templateTypeFieldId
    @_$templateDivFormFieldContainer = $ @getClassFormat @_templateDivFormFieldContainerCSSClass
    @_$templateTextAreaFormFieldContainer = $ @getClassFormat @_templateTextAreaFormFieldContainerCSSClass
    @_$templateTextareaField = $ @getIdFormat @_templateTextareaFieldId
    @_$editTemplateModalDialogPageContainer = $ @getIdFormat @_editTemplateModalDialogPageContainerId

  _bindEvents: () ->
    @_$templateNameField.bind 'change', @_showEditTemplateModalDialog
    @_$templateTypeField.bind 'change', @_replaceTemplateFieldContent
    @_$editTemplateModalDialogPageContainer.bind 'load', @_loadTemplateContent

  _templateFormFieldWidgetInit: () ->

    @_$templateTextAreaFormFieldContainer.addClass('hidden')

    if @_$templateTypeField.val() is 'new'

      @_exchangeFormFieldContainerContent()

      # Copy value from template form field div widget to textarea and save as global value
      textareaValue = @_$templateDivField.html()
      @_$templateTextareaField.html textareaValue 
      @_templateTextareaFieldValue = textareaValue

      @_$templateDivField.html ''

    else if @_$templateTypeField.val() is 'existed'
      # Copy value from template form field div widget into hidden field after form page loaded
      @_$hiddenTemplateField.val @_$templateDivField.html()

  _getTemplateFieldContainer: () ->
    @_$templateDivFieldContainer = @_$templateDivFormFieldContainer
    @_$templateTextareaFieldContainer = @_$templateTextAreaFormFieldContainer
    return 

  _checkTemplateFieldWidget: () ->
    @_getTemplateFieldContainer()
    textareaWidget =  @_$templateDivFieldContainer.find('textarea')

    if textareaWidget.length
      return 'textarea'
    else
      return 'div'

  _replaceTemplateFieldContent: (evt) =>
    templateType = $(evt.target).val()

    if templateType is 'new'
      if @_checkTemplateFieldWidget() isnt 'textarea'
        @_exchangeFormFieldContainerContent()
    else if templateType is 'existed'
        if @_checkTemplateFieldWidget() isnt 'div'
          @_exchangeFormFieldContainerContentBack()
    return

  _exchangeFormFieldContainerContentBack: () ->
    # Replace 'template' textarea form field widget container
    # childrens with childrens from the 'template_textarea' div
    # form field widget container

    # Disable tinymce form field widget editor
    @_disableFormFieldWysiwygEditor()

    @_$templateNameField.attr('disabled', false)

    # Exchange form field container childrens
    @_exchangeContent()

    # Replace template div form field widget id
    attr =
      id: @_templateTextareaFieldId
      name: @_templateTextareaFieldId.slice(3)

    @_$templateDivField.attr attr

    # Replace template textarea form field widget id
    attr =
      id: @_templateDivFieldId
      name: @_templateDivFieldId.slice(3)

    @_$templateTextareaField.attr attr

    @_bindPopoverDialogMouseMoveEvt()

  delay: (ms, func) -> setTimeout func, ms

  _mouseMoveOverTemplateEvt: (evt) =>
    # Mouse move event over template content 
    # Initialize popover dialog
    offset = $(evt.currentTarget).offset()
    relX = evt.pageX - offset.left
    relY = evt.pageY - offset.top
    offsetTop = relY
    offsetLeft = relX

    @delay @_showPopoverModalDialogDelay, => @_initPopoverModalDialog offsetTop, offsetLeft

  _initPopoverModalDialog: (offsetTop, offsetLeft) ->
    @_popoverDialogOpts.mount(offsetTop, offsetLeft)

  _bindPopoverDialogMouseMoveEvt: () ->
    @_popoverDialogOpts = new PopoverModalDialog(
      gettext('Edit template'), 
      @_popoverModalDialogBackDrop,
      @_editTemplateModalDialogId,
      @_$templateNameField,
      @_popoverModalDialogDestroyDelay,
      @_$templateDivField,
      @_popoverModalDialogEditTemplateLinkElementId,
      @_$editTemplateModalDialogPageContainer,
      @_$hiddenTemplateField,
      )

    @_$templateDivField.mousemove(@_mouseMoveOverTemplateEvt)

  _exchangeFormFieldContainerContent: () ->
    # Replace 'template' div form field widget container
    # childrens with childrens from the 'template_textarea' textarea
    # form field widget container

    # Set initial template form field textarea widget value
    @_$templateTextareaField.html(@_templateTextareaFieldValue)

    @_$templateNameField.attr('disabled', true)

    # Exchange form field container childrens
    @_exchangeContent()

    attr =
      id: @_templateTextareaFieldId
      name: @_templateTextareaFieldId.slice(3)
      
    @_$templateDivField.attr attr

    # Replace template div form field widget label
    @_$templateDivFieldContainer.find('label').attr('for', @_templateDivFieldId)
    @_$templateDivFieldContainer.find('label').text(@_$templateTextareaFieldContainer.find('label').text())

    # Replace template textarea form field widget id
    attr =
      id: @_templateDivFieldId
      name: @_templateDivFieldId.slice(3)

    @_$templateTextareaField.attr attr

    # Enable tinymce form field widget editor
    @_enableFormFieldWysiwygEditor()

    @_$templateTextAreaFormFieldContainer.addClass('hidden')

    # Erase hidden template form field
    @_$hiddenTemplateField.val('')

  _enableFormFieldWysiwygEditor: () ->
    django_wysiwyg.enable(@_templateDivFieldId.slice(3))

  _disableFormFieldWysiwygEditor: () ->
    django_wysiwyg.disable(@_templateDivFieldId.slice(3))

  _exchangeContent: () ->
    @_getTemplateFieldContainer()

    # Replace form field container content
    $templateDivFieldContainerChildren = @_$templateDivFieldContainer.children()
    $templateTextareaFieldContainerChildren = @_$templateTextareaFieldContainer.children()

    @_$templateDivFieldContainer .html($templateTextareaFieldContainerChildren)
    @_$templateTextareaFieldContainer.html($templateDivFieldContainerChildren)

    return

  _showEditTemplateModalDialog: (evt) =>
    sessionStorage.removeItem('newEmptyTemplateName')

    targetElementId = "#{ @getIdFormat evt.target.id }"
    templateName = $("#{ targetElementId } option:selected").text()

    if $("#{ targetElementId }").val().length > 0

      if templateName is 'new_empty_template'

        # Init get template name dialog
        @_getTemplateNameDialog = new GetTemplateNameDialog(
          @_getTemplateNameDialogShowDelay,
          @_$templateDivField,
          @_templateNameFieldId,
          @_editTemplateModalDialogId,
          @_popoverModalDialogEditTemplateLinkElementId,
          templateName,
          @_$editTemplateModalDialogPageContainer,
          @_$hiddenTemplateField,
          )

        @_getTemplateNameDialog.mount()

      else
        templateType = @_$templateNameField.find('option:selected').val().split ':'

        dialog = new EditTemplateModalDialog(
          @_editTemplateModalDialogId,
          @_popoverModalDialogEditTemplateLinkElementId,
          @_$editTemplateModalDialogPageContainer,
          @_$hiddenTemplateField,
          @_$templateDivField
          )

        dialog.mount templateName, 'openViaSelectBox', templateType

  _loadTemplateContent: (evt) =>
    @_newEmptyTemplateName = @_getTemplateNameDialog?.getNeEmptyTemplateName()
    if @_newEmptyTemplateName?
      # Insert new template name into select template name options
      @_addEditTemplateConfirmEvent()

  _addEditTemplateConfirmEvent: () ->
    confirmEditBtnClass = 'ct-ignition__button--confirm'

    templatePage = document.querySelector @getIdFormat @_editTemplateModalDialogPageContainerId
    htmlDocument = templatePage.contentDocument

    confirmEditBtn = $(htmlDocument).find @getClassFormat confirmEditBtnClass
    confirmEditBtn.unbind('click')
    confirmEditBtn.bind('click', @_confirmTemplateEdit)

  _confirmTemplateEdit: () =>
    if @_newEmptyTemplateName?
      # Insert new template name into select template name options
      @_addNewSelectOpt(@_newEmptyTemplateName, @_$templateNameField)

      # Erase template name
      @_eraseNewTemplateName()

  _eraseNewTemplateName: () ->
    @_newEmptyTemplateName = null

  _addNewSelectOpt: (text, element) ->
    options = $("#{ @getIdFormat @_templateNameFieldId } option")
    values = $.map options, (option) -> option.value

    value = "new_empty_template:#{ text }"

    if values.indexOf(value) == -1
      opt = new Option(text, value)
      element.append(opt)
      element.val(value)

  getIdFormat: (id) ->
    "##{ id }"

  getClassFormat: (className) ->
    ".#{ className }"
