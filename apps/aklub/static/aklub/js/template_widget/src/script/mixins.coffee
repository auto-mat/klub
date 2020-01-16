###
  FormatSelectorMixin class
###

class FormatSelectorMixin

  getIdFormat: (id) ->
    "##{ id }"

  getClassFormat: (className) ->
    ".#{ className }"

  getNameFormat: (element, name) ->
    "#{ element }[name='#{ name }']"