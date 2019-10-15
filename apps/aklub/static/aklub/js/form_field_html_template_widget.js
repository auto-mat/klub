/*
 * html_template_form_field_widget.js
 *
 * HtmlTemplateFormFieldWidget object class
 */

var HtmlTemplateFormFieldWidget = (function ($) {
  
  var privateData = {}; var privateId = 0
  
  function formFieldWidget (opts) {
    /*
    * Form field widget (load html template)
    */
    Object.defineProperty(this, '_id', { value: privateId++ })
    privateData[this._id] = {
      editDialogPageContainer: opts.editDialogPageContainer,
      popoverDelay: opts.popoverDelay,
      templateDivFieldId: opts.templateDivFieldId,
      hiddenTemplateFieldId: opts.hiddenTemplateFieldId,
      templateNameFieldId: opts.templateNameFieldId,
      templateTypeFieldId: opts.templateTypeFieldId,
      templateTextareaFieldId: opts.templateTextareaFieldId,
      templateDivFormFieldContainer: opts.templateDivFormFieldContainer,
      templateTextAreaFormFieldContainer: opts.templateTextAreaFormFieldContainer,
      templateDivFieldContainer: null,
      templateTextareaFieldContainer: null,
      templateTextareaFieldValue: '',
      popoveBackdrop: opts.popoverBackdrop,
      get editDialogContainerHtmlString () {
        return "<div><object id='" + this.editDialogPageContainer + "' type='text/html' data=''></object></div>"
      },
      init: function () {
        this.cacheDom()
        this.bindEvents()
        this.editTemplatePopOverDialog()
        this.templateFormFieldWidgetInit()
      },
      bindEvents: function () {
        this.$templateNameField.bind('change', this.showEditTemplateDialog.bind(this))
        this.$templateTypeField.bind('change', this.replaceTemplateFieldContent.bind(this))
      },
      cacheDom: function () {
        this.$templateDivField = $(this.templateDivFieldId)
        this.$hiddenTemplateField = $(this.hiddenTemplateFieldId)
        this.$templateNameField = $(this.templateNameFieldId)
        this.$templateTypeField = $(this.templateTypeFieldId)
        this.$templateDivFormFieldContainer = $(this.templateDivFormFieldContainer)
        this.$templateTextAreaFormFieldContainer = $(this.templateTextAreaFormFieldContainer)
        this.$templateTextareaField = $(this.templateTextareaFieldId)
      },
      openEditTemplateDialog: function (e, ui, $dialog, templateName) {
        // Hide close X icon
        $('.ui-dialog-titlebar-close').hide()
        $dialog.find('#' + this.editDialogPageContainer).attr(
          {
            data: window.reverse('aklub:get_email_template', { template_name: templateName }),
            width: $(window).width() - 40,
            height: $(window).height() - 250
          }
        )
      },
      inlineStyler: function (element) {
        element.inlineStyler()
      },
      confirmEditTemplateDialog: function ($dialog) {
        var templatePage, htmlDocument, article
        templatePage = document.querySelector('#' + this.editDialogPageContainer)
        htmlDocument = templatePage.contentDocument
        article = $(htmlDocument).find('article')
        // Convert email template external css into inline
        this.inlineStyler(article)
        this.$templateDivField.html(article)
        this.$hiddenTemplateField.val(article.html())
        $dialog.dialog('destroy')
      },
      editTemplateDialog: function (templateName) {
        var that = this; var btnNames = {}; var title
        btnNames[gettext('Ok')] = function () {that.confirmEditTemplateDialog($(this))}
        title = gettext('Edit') + ' \'' + templateName + '\' ' + gettext('template')
        $(this.editDialogContainerHtmlString).dialog({
          modal: true,
          title: title,
          width: $(window).width() - 20,
          heigth: $(window).height() - 115,
          position: { my: 'top', at: 'top+112' },
          open: function (e, ui) {
            that.openEditTemplateDialog(e, ui, $(this), templateName)
          },
          buttons: btnNames
        })
      },
      destroyPopover: function () {
        this.$templateDivField.webuiPopover('hide')
        this.$templateDivField.webuiPopover('destroy')
      },
      showPopover: function (element) {
        var that = this
        element.click(function (e) {
          e.preventDefault()
          var templateName = that.$templateNameField.find('option:selected').text()
          that.editTemplateDialog(templateName)
          that.destroyPopover()
        })
        setTimeout(function () {
          that.destroyPopover()
        }, that.popoverDelay)
      },
      getPopoverOpts: function () {
        var that = this; var content
        content = '<a id="edit_template" href=""><b>' + gettext('Edit template') + '</b></a>'
        return {
          placement: 'top-right',
          trigger: 'manual',
          title: 'Edit',
          content: content,
          offsetTop: 0,
          offsetLeft: 0,
          backdrop: that.popoveBackdrop,
          onShow: function (element) {
            that.showPopover(element)
          }
        }
      },
      editTemplatePopOverDialog: function () {
        var opts = this.getPopoverOpts()
        var that = this
        this.$templateDivField.mousemove(function (e) {
          var offset = $(this).offset()
          var relX = e.pageX - offset.left
          var relY = e.pageY - offset.top
          opts.offsetTop = relY
          opts.offsetLeft = relX
          WebuiPopovers.show('#' + that.$templateDivField.attr('id'), opts)
        })
      },
      showEditTemplateDialog: function (e) {
        var templateName = $(e.target).val()
        if (templateName !== '') {
          this.editTemplateDialog(templateName)
        }
      },
      getTemplateFieldContainer: function () {
        this.templateDivFieldContainer = this.$templateDivFormFieldContainer
        this.templateTextareaFieldContainer = this.$templateTextAreaFormFieldContainer
      },
      exchangeContent: function () {
        this.getTemplateFieldContainer()
        // Replace form field container content
        var templateDivFieldContainerChildren = this.templateDivFieldContainer.children()
        var templateTextareaFieldContainerChildren = this.templateTextareaFieldContainer.children()
        this.templateDivFieldContainer.html(templateTextareaFieldContainerChildren)
        this.templateTextareaFieldContainer.html(templateDivFieldContainerChildren)
      },
      exchangeFormFieldContainerContent: function () {
        /* Replace 'template' div form field widget container
         * childrens with childrens from the 'template_textarea' textarea
         * form field widget container
         */

        // Set initial template form field textarea widget value
        this.$templateTextareaField.html(this.templateTextareaFieldValue)

        this.$templateNameField.attr('disabled', true)
        // Exchange form field container childrens
        this.exchangeContent()

        // Replace template div form field widget id
        $(this.templateDivFieldId).attr(
          {
            name: this.templateTextareaFieldId.slice(4),
            id: this.templateTextareaFieldId.slice(1)
          }
        )
        // Replace template div form field widget label
        this.templateDivFieldContainer.find('label').attr('for', this.templateDivFieldId.slice(1))
        this.templateDivFieldContainer.find('label').text(this.templateTextareaFieldContainer.find('label').text())
        // Replace template textarea form field widget id
        $(this.templateTextareaFieldId).attr(
          {
            name: this.templateDivFieldId.slice(4),
            id: this.templateDivFieldId.slice(1)
          }
        )
        // Enable tinymce form field widget editor
        django_wysiwyg.enable(this.templateDivFieldId.slice(4))

        this.$templateTextAreaFormFieldContainer.addClass('hidden')
        // Erase hidden template form field
        this.$hiddenTemplateField.val(null)
      },
      exchangeFormFieldContainerContentBack: function () {
        /* Replace 'template' textarea form field widget container
         * childrens with childrens from the 'template_textarea' div
         * form field widget container
         */

        // Disable tinymce form field widget editor
        django_wysiwyg.disable(this.templateDivFieldId.slice(4))

        this.$templateNameField.attr('disabled', false)

        // Exchange form field container childrens
        this.exchangeContent()

        // Replace template div form field widget id
        $(this.templateDivFieldId).attr(
          {
            name: this.templateTextareaFieldId.slice(4),
            id: this.templateTextareaFieldId.slice(1)
          }
        )
        // Replace template textarea form field widget id
        $(this.templateTextareaFieldId).attr(
          {
            name: this.templateDivFieldId.slice(4),
            id: this.templateDivFieldId.slice(1)
          }
        )

        this.editTemplatePopOverDialog()
      },
      checkTemplateFieldWidget: function () {
        this.getTemplateFieldContainer()
        var textareaWidget = this.templateDivFieldContainer.find('textarea')
        if (textareaWidget.length) {
          return 'textarea'
        } else {
          return 'div'
        }
      },
      replaceTemplateFieldContent: function (e) {
        var templateType = $(e.target).val()
        if (templateType === 'new') {
          if (this.checkTemplateFieldWidget() !== 'textarea') {
            this.exchangeFormFieldContainerContent()
          }
        } else if (templateType === 'existed') {
          if (this.checkTemplateFieldWidget() !== 'div') {
            this.exchangeFormFieldContainerContentBack()
          }
        }
      },
      templateFormFieldWidgetInit: function () {
        this.$templateTextAreaFormFieldContainer.addClass('hidden')
        if (this.$templateTypeField.val() === 'new') {
          this.exchangeFormFieldContainerContent()
          // Copy value from template form field div widget to textarea and save as global value
          var textareaValue = this.$templateDivField.html()
          this.$templateTextareaField.html(textareaValue)
          this.templateTextareaFieldValue = textareaValue
          this.$templateDivField.html(null)
        } else if (this.$templateTypeField.val() === 'existed') {
          // Copy value from template form field div widget into hidden field after form page loaded
          this.$hiddenTemplateField.val(this.$templateDivField.html())
        }
      }
    }
    // Initialize
    privateData[this._id].init()
  }
  return formFieldWidget
}(jQuery))

