/*
 * masscommunication_init.js
 *
 * MassCommunication form fields (html template widget) initialization
 */

(function ($, HtmlTemplateFormFieldWidget) {
  $(document).ready(function () {
    var formOpts = {
      editDialogPageContainer: 'template_page',
      popoverDelay: 3000,
      popoverBackdrop: true
    }
    var htmlTemplateFieldOpts = {
      templateNameFieldId: '#id_template_name',
      templateTypeFieldId: '#id_template_type',
      templateDivFieldId: '#id_template',
      hiddenTemplateFieldId: '#id_hidden_template',
      templateTextareaFieldId: '#id_template_textarea',
      templateDivFormFieldContainer: '.field-template',
      templateTextAreaFormFieldContainer: '.field-template_textarea',
    }
    Object.assign(htmlTemplateFieldOpts, formOpts)
    var htmlTemplateFieldWidget = new HtmlTemplateFormFieldWidget(htmlTemplateFieldOpts)

    var htmlTemplateEnFieldOpts = {
      templateNameFieldId: '#id_template_en_name',
      templateTypeFieldId: '#id_template_en_type',
      templateDivFieldId: '#id_template_en',
      hiddenTemplateFieldId: '#id_hidden_template_en',
      templateTextareaFieldId: '#id_template_en_textarea',
      templateDivFormFieldContainer: '.field-template_en',
      templateTextAreaFormFieldContainer: '.field-template_en_textarea',
    }
    Object.assign(htmlTemplateEnFieldOpts, formOpts)
    var htmlTemplateEnFieldWidget = new HtmlTemplateFormFieldWidget(htmlTemplateEnFieldOpts)
  })
}(jQuery, HtmlTemplateFormFieldWidget))
