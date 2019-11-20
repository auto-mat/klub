$(document).ready ->

  getTemplateNameDialogShowDelay = 500
  showPopoverDialog = 750
  showPopoverDialogDelay = 3000
  popoverDialogBackdrop = true
  
  htmlTemplateFieldOpts = new HtmlTemplateFormFieldWidget(
    'edit_template_dialog',
    'edit_template',
    getTemplateNameDialogShowDelay,
    'id_template_name',
    'id_template_type',
    'id_hidden_template',
    'field-template',
    'field-template_textarea',
    'id_template_textarea',
    'template_page',
    'id_template',
    showPopoverDialog,
    popoverDialogBackdrop,
    showPopoverDialogDelay
  )

  htmlTemplateEnFieldWidget = new HtmlTemplateFormFieldWidget(
    'edit_template_dialog',
    'edit_template',
     getTemplateNameDialogShowDelay,
    'id_template_en_name',
    'id_template_en_type',
    'id_hidden_template_en',
    'field-template_en',
    'field-template_en_textarea',
    'id_template_en_textarea',
    'template_page',
    'id_template_en',
    showPopoverDialog,
    popoverDialogBackdrop,
    showPopoverDialogDelay
  )