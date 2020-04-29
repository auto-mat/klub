(function() {
  var editor, xhr;

  // Get the editor
  editor = new ContentTools.EditorApp.get();

  // Define our request for the French translation file
  xhr = new XMLHttpRequest();
  xhr.open(
    'GET',
    window.reverse('aklub:get_contenttools_translation', djangoLang),
    true);

  function onStateChange (ev) {
    var translations;
    if (ev.target.readyState == 4) {
      // Convert the JSON data to a native Object
      translations = JSON.parse(ev.target.responseText);

      // Add the translations for the French language
      ContentEdit.addTranslations(djangoLang, translations);

      // Set French as the editors current language
      ContentEdit.LANGUAGE = djangoLang;
    }
  }

  if (djangoLang != "en") {
    xhr.addEventListener('readystatechange', onStateChange);
  }

  // Load the language
  xhr.send(null);
}());
