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
      editTemplateModalDialogId: opts.editTemplateModalDialogId,
      editDialogPageContainer: opts.editDialogPageContainer,
      showPopoverDelay: opts.showPopoverDelay,
      destroyPopoverDelay: opts.destroyPopoverDelay,
      templateDivFieldId: opts.templateDivFieldId,
      hiddenTemplateFieldId: opts.hiddenTemplateFieldId,
      templateNameFieldId: opts.templateNameFieldId,
      templateTypeFieldId: opts.templateTypeFieldId,
      templateTextareaFieldId: opts.templateTextareaFieldId,
      templateDivFormFieldContainer: opts.templateDivFormFieldContainer,
      templateTextAreaFormFieldContainer: opts.templateTextAreaFormFieldContainer,
      setTemplateNameDialogDelay: opts.setTemplateNameDialogDelay,
      templateDivFieldContainer: null,
      templateTextareaFieldContainer: null,
      templateTextareaFieldValue: '',
      popoveBackdrop: opts.popoverBackdrop,
      editTemplateDialogPageContainerId: '#edit_template',
      templateNameInputId: 'template_name',
      newEmptyTemplateName: null,
      setTemplateNameDialogId: 'set_template_name',
      setTemplateNameDialogConfirmBtnId: 'confirm_btn',
      errorListClassName: 'errorlist',
      editTemplateModalDialogAttr: this.getEditTemplateModalDialogAttr,
      get getEditTemplateModalDialogAttr () {
        var data = {}
        data['data-type'] = 'modal'
        data['data-target'] = this.editTemplateModalDialogId
        data['data-fullscreen'] = 'true'
        data['data-overlayClick'] = 'true'
        return data
      },
      get editTemplateHrefElement () {
        var element = $('<a id="' + this.editTemplateDialogPageContainerId.slice(1) + '" href=""></a>')
        element.attr(this.getEditTemplateModalDialogAttr)
        element.html('<b>' + gettext('Edit template') + '</b>')
        return element
      },
      get setTemplateNameDialogContainer () {
        var divContainer = $('<div id="' + this.setTemplateNameDialogId + '"></div>')
        var form = $('<form id="template_name_form"></fom>')
        var formContentContainer = $('<div></div>')
        var formErrorListContainer = $('<ul class="' + this.errorListClassName + '"></ul>')
        var formContentLabel = $('<label for="' + this.templateNameInputId + '">' + gettext('Template name') + ':</label>')
        var formContentInput = $('<input name="' + this.templateNameInputId + '" id="' + this.templateNameInputId + '">')
        formContentContainer.append(formContentLabel)
        formContentContainer.append(formContentInput)
        formContentContainer.append(formErrorListContainer)
        return divContainer.append(form.append(formContentContainer))
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
        this.$editDialogPageContainer.bind('load', this.loadTemplateContent.bind(this))
      },
      cacheDom: function () {
        this.$templateDivField = $(this.templateDivFieldId)
        this.$hiddenTemplateField = $(this.hiddenTemplateFieldId)
        this.$templateNameField = $(this.templateNameFieldId)
        this.$templateTypeField = $(this.templateTypeFieldId)
        this.$templateDivFormFieldContainer = $(this.templateDivFormFieldContainer)
        this.$templateTextAreaFormFieldContainer = $(this.templateTextAreaFormFieldContainer)
        this.$templateTextareaField = $(this.templateTextareaFieldId)
        this.$editDialogPageContainer = $('#' + this.editDialogPageContainer)
      },
      loadTemplateContent: function (e) {
        if (this.newEmptyTemplateName) {
          this.addEditTemplateConfirmEvent()
        }
        // var htmlDocument = this.getIframeTemplateContent()
        // this.convertVideoImgThumbnailToIframe(htmlDocument)
      },
      adjustListCssProperties: function (element) {
        if (element.is('ul') || element.is('ol')) {
          element.css({
            margin: '10px',
            padding: '15px'
          })
        }
      },
      convertTextCssPositionToTable: function (editContainer) {
        var elementCssClass, tableWrapper, that
        that = this
        editContainer.find('p, ul, ol, h1, h2, h3, h4, h5, h6').each(function () {
          elementCssClass = $(this).attr('class') ? $(this).attr('class').split(' ') : []
          switch (elementCssClass) {
            case elementCssClass.indexOf('text-left') > -1:
              tableWrapper = that.setElementPosition('left', '', '')
              break
            case elementCssClass.indexOf('text-right') > -1:
              tableWrapper = that.setElementPosition('right', '', '')
              break
            case elementCssClass.indexOf('text-center') > -1:
              tableWrapper = that.setElementPosition('center', '', '')
              break
            default:
              tableWrapper = that.setElementPosition('center', '', '')
          }
          that.adjustListCssProperties($(this))
          tableWrapper.find('td').append($(this).clone())
          $(this).after(tableWrapper)
          $(this).remove()
        })
      },
      setElementPosition: function (align, width, heigth) {
        var table = $('<table></table>')
        table.attr({
          cellspacing: 0,
          cellpadding: 0,
          border: 0,
          width: '100%'
        })
        var tableBody = $('<tbody></tbody>')
        var tableRow = $('<tr></tr>')
        var tableCell = $('<td></td>')
        tableCell.css({
          border: 'none',
          padding: 0,
          margin: 0
        })
        tableCell.attr({
          align: align,
          width: width,
          heigth: heigth
        })
        return table.append(tableBody.append(tableRow.append(tableCell)))
      },
      convertImgFloatCssPositionToTable: function (img, editContainer, position) {
        var padding = 15
        var paddingValues = position === 'left' ? '0 0 0 ' + padding + 'px' : '0 ' + padding + 'px' + ' 0 0'
        var tableCell = $('<td></td>')
        tableCell.css({
          border: 'none',
          padding: paddingValues,
          margin: '0'
        })
        var contextElement = img.closest('.video').length > 0 ? img.closest('.video').next().clone() : img.next().clone()
        var contextWidth = parseFloat(editContainer.find('#content_table').width() - parseFloat(img.attr('width')) - padding)
        contextElement.css('width', contextWidth)
        tableCell.attr('width', contextWidth)
        tableCell.append(contextElement)
        img.closest('.video').length > 0 ? img.closest('.video').next().remove() : img.next().remove()
        return tableCell
      },
      convertImageCssPostionToTable: function (img, editContainer) {
        var tableWrapper, marginLeft, marginRight, floatPosition, tableCell
        img = img.find('img').length > 0 ? img.find('img') : img
        marginLeft = img.css('margin-left').split('.')[0]
        marginRight = img.css('margin-right').split('.')[0]
        floatPosition = img.css('float')
        img.css('display', '')
        if ((marginLeft === marginRight) && (floatPosition === 'none')) {
          tableWrapper = this.setElementPosition('center', '', '')
        } else if (marginLeft > marginRight) {
          tableWrapper = this.setElementPosition(floatPosition, img.attr('width'), img.attr('height'))
          tableCell = this.convertImgFloatCssPositionToTable(img, editContainer, floatPosition)
        } else if (marginRight > marginLeft) {
          tableWrapper = this.setElementPosition(floatPosition, img.attr('width'), img.attr('height'))
          tableCell = this.convertImgFloatCssPositionToTable(img, editContainer, floatPosition)
        } else if ((floatPosition === 'left') || (floatPosition === 'right')) {
          tableWrapper = this.setElementPosition(floatPosition, img.attr('width'), img.attr('height'))
          tableCell = this.convertImgFloatCssPositionToTable(img, editContainer, floatPosition)
        }
        tableWrapper.find('td').append(img.closest('.video').length > 0 ? img.closest('.video').clone() : img.clone())
        floatPosition === 'left' ? tableWrapper.find('tr').append(tableCell) : tableWrapper.find('tr').prepend(tableCell)
        img.closest('.video').length > 0 ? img.closest('.video').after(tableWrapper) : img.after(tableWrapper)
        img.closest('.video').lnegth > 0 ? img.closest('.video').remove() : img.remove()
      },
      replaceImgSrc: function (editContainer) {
        var that = this
        var imgs = editContainer.find('img')
        imgs.each(function () {
          var clickableVideoThumbnail = $(this).closest('.video')
          var img = clickableVideoThumbnail.length > 0 ? clickableVideoThumbnail : $(this)
          if (clickableVideoThumbnail.length === 0) {
            var src = $(this).attr('src')
            var regexPattern = new RegExp(window.origin)
            if (!(src.match(regexPattern))) {
              var imgSrc = window.origin + $(this).attr('src')
              $(this).attr('src', imgSrc)
            }
          }
          that.convertImageCssPostionToTable(img, editContainer)
        })
      },
      eraseNewTemplateName: function () {
        this.newEmptyTemplateName = null
      },
      addNewSelectOpt: function (text, element) {
        var value = 'new_empty_template:' + text
        var opt = new Option(text, value)
        element.append(opt)
        element.val(value)
      },
      confirmTemplateEdit: function (e) {
        if (this.newEmptyTemplateName) {
          this.addNewSelectOpt(this.newEmptyTemplateName, this.$templateNameField)
          this.eraseNewTemplateName()
        }
      },
      addEditTemplateConfirmEvent: function () {
        var templatePage, htmlDocument, confirmEditBtn
        confirmEditBtn = '.ct-ignition__button--confirm'
        templatePage = document.querySelector('#' + this.editDialogPageContainer)
        htmlDocument = templatePage.contentDocument
        confirmEditBtn = $(htmlDocument).find(confirmEditBtn)
        confirmEditBtn.unbind('click')
        confirmEditBtn.bind('click', this.confirmTemplateEdit.bind(this))
      },
      convertVideoImgThumbnailToIframe: function (htmlDocument) {
        $(htmlDocument).find('.video').each(function () {
          var img = $(this).find('img')
          var iFrame = $('<iframe></iframe>')
          iFrame.attr({
            width: img.attr('width'),
            height: img.attr('height'),
            src: img.attr('src')
          })
          $(this).after(iFrame)
          $(this).remove()
        })
      },
      convertVideoIframeToImgThumbnail: function (htmlDocument) {
        var youtubeRegex, vimeoRegex, clickableVideoThumbnail, videoThumbnail, videoId, videoThumbnailSrc
        youtubeRegex = new RegExp('youtube.com.*(v=|/embed/)(.{11})')
        vimeoRegex = new RegExp('vimeo.com.*(.{8})')
        $(htmlDocument).find('iframe').each(function () {
          var iframeSrc = $(this).attr('src')
          var iframeCssFloatProperty = $(this).css('float')
          var iframeWidth = $(this).attr('width')
          var iframeHeight = $(this).attr('height')
          clickableVideoThumbnail = $('<a href="" class="video"></a>')
          clickableVideoThumbnail.attr('href', iframeSrc)
          videoThumbnail = $('<img src="">')
          videoThumbnail.attr({
            width: iframeWidth,
            height: iframeHeight
          })
          if (iframeSrc.match(youtubeRegex)) {
            videoId = iframeSrc.match(youtubeRegex).pop()
            clickableVideoThumbnail.attr('id', videoId)
            clickableVideoThumbnail.addClass('youtube')
            videoThumbnailSrc = '//img.youtube.com/vi/' + videoId + '/0.jpg'
            videoThumbnail.attr('src', videoThumbnailSrc)
          } else if (iframeSrc.match(vimeoRegex)) {
            videoId = iframeSrc.match(vimeoRegex).pop()
            clickableVideoThumbnail.attr('id', videoId)
            clickableVideoThumbnail.addClass('vimeo')
            $.ajax({
              type: 'GET',
              url: 'http://vimeo.com/api/v2/video/' + videoId + '.json',
              jsonp: 'callback',
              dataType: 'jsonp',
              context: { videoThumbnail: videoThumbnail },
              success: function (data) {
                videoThumbnailSrc = data[0].thumbnail_large
                this.videoThumbnail.attr('src', videoThumbnailSrc)
              }
            })
          }
          if (videoThumbnail) {
            videoThumbnail.css('float', iframeCssFloatProperty)
            // Add video thumbnail
            clickableVideoThumbnail.append(videoThumbnail)
            $(this).after(clickableVideoThumbnail)
            // Remove video iframe
            $(this).remove()
          }
        })
      },
      convertCssToInlineStyle: function (htmlDocument) {
        var editContainer = $(htmlDocument).find('article')
        // Convert email template external css into inline
        this.inlineStyler(editContainer)
        this.replaceImgSrc(editContainer)
        this.convertTextCssPositionToTable(editContainer)
        this.$templateDivField.html(editContainer)
        this.$hiddenTemplateField.val(editContainer.html())
      },
      getIframeTemplateContent: function () {
        var templatePage, htmlDocument
        templatePage = document.querySelector('#' + this.editDialogPageContainer)
        htmlDocument = templatePage.contentDocument
        return htmlDocument
      },
      closeEditTemplateDialog: function (e) {
        var htmlDocument = this.getIframeTemplateContent()
        this.convertVideoIframeToImgThumbnail(htmlDocument)
        this.convertCssToInlineStyle(htmlDocument)
      },
      setLoadTemplateParam: function (templateName, urlName) {
        var url
        if (arguments.length === 1) {
          urlName = 'get_email_template'
        }
        url = window.reverse(urlName, { template_name: templateName })
        this.$editDialogPageContainer.attr(
          {
            data: url,
            width: $(window).width(),
            height: $(window).height()
          }
        )
        return url
      },
      openEditTemplateDialog: function (templateName, openType, templateType) {
        sessionStorage.removeItem('dbTemplateName')
        if (openType) {
          $('body').append(this.editTemplateHrefElement)
        }
        // Initialize jQuery modal dialog
        $('#edit_template').mdl()
        // Load template from db
        if (templateType) {
          var params = { template_name: templateName }
          if (arguments[2].length > 1) {
            var url = this.setLoadTemplateParam(templateName, 'aklub:get_email_template_from_db', params)
            sessionStorage.setItem('dbTemplateName', url)
          } else {
            this.setLoadTemplateParam(templateName, 'aklub:get_email_template', params)
          }
        }
        // Open jQuery modal dialog
        mdl_open(this.editTemplateModalDialogId)
        $(this.editTemplateModalDialogId + ' ' + '.mdl-close').unbind('click')
        $(this.editTemplateModalDialogId + ' ' + '.mdl-close').bind('click', this.closeEditTemplateDialog.bind(this))
        if (openType) {
          $(this.editTemplateDialogPageContainerId).remove()
        }
      },
      inlineStyler: function (element) {
        element.inlineStyler()
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
          var templateType = that.$templateNameField.find('option:selected').val().split(':')
          that.openEditTemplateDialog(templateName, '', templateType)
          that.destroyPopover()
        })
        setTimeout(function () {
          that.destroyPopover()
        }, that.destroyPopoverDelay)
      },
      getPopoverOpts: function () {
        var that = this; var content
        content = this.editTemplateHrefElement
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
          setTimeout(function () {
            WebuiPopovers.show('#' + that.$templateDivField.attr('id'), opts)
          }, that.showPopoverDelay)
        })
      },
      checkTemplateName: function (o, name, m) {
        var opts = []
        $(this.templateNameFieldId + ' > option').each(function () {
          opts.push($(this).text())
        })
        if (opts.indexOf(name) > -1) {
          var errorlist = o.closest('form').find('.' + this.errorListClassName)
          errorlist.append('<li>' + m + '</li>')
          return false
        } else {
          return true
        }
      },
      setTemplateNameDialogValidation: function () {
        var valid = true
        var templateName = $('#' + this.templateNameInputId)
        $('.' + this.errorListClassName).html('')
        var message = gettext('Template name may consist of a-z, 0-9, ' +
                              'underscores, not spaces and must begin with a letter,' +
                              'and be lowercase.')
        valid = valid && this.checkRegexp(templateName, /^[a-z]([0-9a-z_])+$/, message)
        message = gettext('Template name exist.')
        valid = valid && this.checkTemplateName($('#' + this.templateNameInputId), templateName.val(), message)
        return valid
      },
      confirmSetTemplateNameDialog: function ($dialog, templateName) {
        var valid = this.setTemplateNameDialogValidation()
        if (valid) {
          this.newEmptyTemplateName = $('#' + this.templateNameInputId).val()
          $dialog.dialog('destroy')
          this.setNewTemplatePageName()
          var templateType = [this.newEmptyTemplateName]
          this.openEditTemplateDialog(templateName, 'openViaSelectBox', templateType)
        }
      },
      setNewTemplatePageName: function () {
        if (this.newEmptyTemplateName) {
          sessionStorage.setItem('newEmptyTemplateName', this.newEmptyTemplateName)
        }
      },
      openSetTemplateNameDialog: function (e, ui, $dialog) {
        // Hide close X icon
        // $('.ui-dialog-titlebar-close').hide()
      },
      checkRegexp: function (o, regexp, m) {
        if (!(regexp.test(o.val()))) {
          var errorlist = o.closest('form').find('.' + this.errorListClassName)
          errorlist.append('<li>' + m + '</li>')
          return false
        } else {
          return true
        }
      },
      triggerConfirmBtn: function () {
        var that = this
        $('#' + this.setTemplateNameDialogId).keypress(function (e) {
          if (e.keyCode === $.ui.keyCode.ENTER) {
            $('#' + that.setTemplateNameDialogConfirmBtnId).click()
          }
        })
      },
      setTemplateNameDialog: function (templateName) {
        var that = this; var btnNames = {}; var title
        btnNames.ok = {
          text: gettext('Ok'),
          id: this.setTemplateNameDialogConfirmBtnId,
          click: function () { that.confirmSetTemplateNameDialog($(this), templateName) }
        }
        title = gettext('Set template name')
        $(this.setTemplateNameDialogContainer).dialog({
          modal: true,
          title: title,
          show: {
            effect: 'fade',
            delay: this.setTemplateNameDialogDelay
          },
          resizable: false,
          open: function (e, ui) {
            that.triggerConfirmBtn()
            that.openSetTemplateNameDialog(e, ui, $(this))
          },
          beforeClose: function (e, ui) {
            $(this).dialog('destroy')
            that.$templateDivField.html('')
          },
          buttons: btnNames
        })
      },
      showEditTemplateDialog: function (e) {
        sessionStorage.removeItem('newEmptyTemplateName')
        var templateName = $('#' + e.target.id + ' option:selected').text()
        if ($('#' + e.target.id).val() !== '') {
          if (templateName === 'new_empty_template') {
            // New empty template
            this.setTemplateNameDialog(templateName, 'openViaSelect')
          } else {
            var templateType = this.$templateNameField.find('option:selected').val().split(':')
            this.openEditTemplateDialog(templateName, 'openViaSelect', templateType)
          }
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
      enableFormFieldWysiwygEditor: function () {
        django_wysiwyg.enable(this.templateDivFieldId.slice(4))
      },
      disableFormFieldWysiwygEditor: function () {
        django_wysiwyg.disable(this.templateDivFieldId.slice(4))
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
        this.enableFormFieldWysiwygEditor()

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
        this.disableFormFieldWysiwygEditor()

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
