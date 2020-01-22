###
  PostProcessHtmlTemplate class
###

class PostProcessHtmlTemplate extends FormatSelectorMixin

  constructor: (htmlDoc, $editTemplatePageContainer, $templateDivField, $hiddenTemplateField) ->

    @_htmlDoc = htmlDoc

    @_$editTemplatePageContainer = $editTemplatePageContainer

    @_$templateDivField = $templateDivField

    @_$hiddenTemplateField = $hiddenTemplateField
    
    @_videoClass = 'video'

    @_textContainerTags = ['p', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']

    # Methods
    @convertVideoIframeToImgThumbnail()

  convertVideoIframeToImgThumbnail: () ->

    promises = []
    hasVideo = false

    youtubeRegex = new RegExp 'youtube.com.*(v=|/embed/)(.{11})'

    vimeoRegex = new RegExp 'vimeo.com.*./(.*)'

    addThumbnail = ($videoThumbnail, $clickableVideoThumbnail, $videoCaption, element, iframeCssFloatProperty) ->

      $videoThumbnail.css 'float', iframeCssFloatProperty

      # Add video thumbnail
      $clickableVideoThumbnail.append $videoThumbnail

      # Add video thumbnail figcaption
      $clickableVideoThumbnail.append $videoCaption

      $(element).after $clickableVideoThumbnail

      # Remove video iframe
      $(element).remove()

    success = (data) ->
      # videoThumbnailSrc = data[0].thumbnail_large
      # attr = 
      #  'src': videoThumbnailSrc

      if @videoType is 'vimeo'

        attr =
          src: data['thumbnail_url'],
          width: data['thumbnail_width'],
          height: data['thumbnail_height']

        @$videoThumbnail.attr attr

      @$videoCaption.text data['title']

      addThumbnail(
        @$videoThumbnail,
        @$clickableVideoThumbnail,
        @$videoCaption,
        @element,
        @iframeCssFloatProperty
      )

    $(@_htmlDoc).find('iframe').each (i, element) =>

      iframeSrc = $(element).attr 'src'
      iframeCssFloatProperty = $(element).css 'float'
      iframeWidth = $(element).attr 'width'
      iframeHeight = $(element).attr 'height'
      
      $clickableVideoThumbnail = $ '<a href="" class="video"></a>'
      $clickableVideoThumbnail.attr 'href', iframeSrc

      $videoThumbnail = $ '<img src="">'
      $videoThumbnail.attr({
        width: iframeWidth,
        height: iframeHeight
        })

      $videoCaption = $ '<figcaption></figcaption>'
      css =
        'text-align': 'center',
        'font-size': '12px'
      $videoCaption.css css

      if iframeSrc.match(youtubeRegex)

        hasVideo = true

        videoId = iframeSrc.match(youtubeRegex).pop()
        $clickableVideoThumbnail.attr 'id', videoId
        $clickableVideoThumbnail.addClass 'youtube'

        videoThumbnailSrc = "//img.youtube.com/vi/#{ videoId }/0.jpg"
        $videoThumbnail.attr 'src', videoThumbnailSrc

        subUrl = "http://www.youtube.com/watch?v=#{ videoId }&"
        url = "https://noembed.com/embed?url=#{ subUrl }"

        context = 
          $videoThumbnail: $videoThumbnail,
          $clickableVideoThumbnail: $clickableVideoThumbnail,
          $videoCaption: $videoCaption,
          element: element,
          iframeCssFloatProperty: iframeCssFloatProperty,
          videoType: 'youtube'

        promises.push $.ajax @getAjaxData context, url, success, type='GET', dataType='jsonp'

      else if iframeSrc.match(vimeoRegex)

        hasVideo = true

        videoId = iframeSrc.match(vimeoRegex).pop()

        $clickableVideoThumbnail.attr 'id', videoId
        $clickableVideoThumbnail.addClass 'vimeo'

        ###
          Get embed player info
          Player video thumbnail size != iFrame size
          Use embed player video thumbnail size
          https://developer.vimeo.com/api/oembed/videos
        ###

        subUrl = "https://vimeo.com/#{ videoId }&width=#{ iframeWidth }&height=#{ iframeHeight }"
        url = "https://vimeo.com/api/oembed.json?url=#{ subUrl }"

        context = 
          $videoThumbnail: $videoThumbnail,
          $clickableVideoThumbnail: $clickableVideoThumbnail,
          $videoCaption: $videoCaption,
          element: element,
          iframeCssFloatProperty: iframeCssFloatProperty,
          videoType: 'vimeo'

        promises.push $.ajax @getAjaxData context, url, success, type='GET', dataType='jsonp'

    # Wait for an all ajax request done
    $.when.apply(null, promises).done () =>
      @convertCssToInlineStyle()

  getAjaxData: (context, url, success, type='GET', dataType='json') ->
    ajaxData =
      type: type,
      url: url
      jsonp: 'callback',
      dataType: dataType,
      context: context,
      success: success

  convertCssToInlineStyle: () ->

    @inlineStyler $(@_htmlDoc)
    @_fixContentWidth()
    @_fixMargin()
    @replaceImgSrc()
    @convertTextCssPositionToTable()
    @_$templateDivField.html @_$editTemplatePageContainer
    @_$hiddenTemplateField.val @_$editTemplatePageContainer.html()

  inlineStyler: ($element) ->
    $element.inlineStyler()

  getElementPosition: (align, width='', heigth='') ->

    $table = $('<table></table>')

    $table.attr({
      cellspacing: 0,
      cellpadding: 0,
      border: 0,
      width: '100%'
      })

    $tableBody = $('<tbody></tbody>')
    $tableRow = $('<tr></tr>')
    $tableCell = $('<td></td>')

    $tableCell.css({
      border: 'none',
      padding: 0,
      margin: 0
      })

    $tableCell.attr({
      align: align,
      width: width,
      heigth: heigth
    })

    $table.append $tableBody.append $tableRow.append $tableCell

  replaceImgSrc: () ->

    $imgs = @_$editTemplatePageContainer.find 'img'

    $imgs.each (i, element) =>

      $clickableVideoThumbnail = $(element).closest @getClassFormat @_videoClass
      $img = if $clickableVideoThumbnail.length > 0 then $clickableVideoThumbnail else $(element)

      if $clickableVideoThumbnail.length == 0
        src = $(element).attr('src')

        regexPattern = new RegExp(window.origin)

        if not src.match(regexPattern)
          imgSrc = "#{ window.origin }#{ $(element).attr('src') }"
          $(element).attr('src', imgSrc)

      @convertImageCssPositionToTable $img

  convertImageCssPositionToTable: ($img) ->

    $img =  if $img.find('img').length > 0 then $img.find 'img' else $img

    marginLeft = parseInt($img.css('margin-left').split('.')[0].replace('px', ''))
    marginRight = parseInt($img.css('margin-right').split('.')[0].replace('px', ''))
    floatPosition = $img.css 'float'
    $img.css 'display', ''

    if (marginLeft is marginRight) and (floatPosition is 'none')
      $tableWrapper = @getElementPosition('center', '', '')

    else if marginLeft > marginRight

        $tableWrapper = @getElementPosition(
          floatPosition,
          $img.attr('width'),
          $img.attr('height')
          )
        $tableCell = @convertImgFloatCssPositionToTable(
          $img, 
          @_$editTemplatePageContainer, 
          floatPosition
          )

    else if marginRight > marginLeft

        $tableWrapper = @getElementPosition(
          floatPosition, 
          $img.attr('width'), 
          $img.attr('height')
          )
        $tableCell = @convertImgFloatCssPositionToTable(
          $img, 
          @_$editTemplatePageContainer, 
          floatPosition
          )

    else if (floatPosition is'left') or (floatPosition is'right')

        $tableWrapper = @getElementPosition(
          floatPosition,
          $img.attr('width'),
          $img.attr('height')
          )
        $tableCell = @convertImgFloatCssPositionToTable(
          $img, 
          @_$editTemplatePageContainer, 
          floatPosition
          ) 

    videoClassSelector = @getClassFormat @_videoClass
    $videoIframe = $img.closest(videoClassSelector)

    $tableWrapper.find('td').append(
      if $videoIframe.length > 0
        $videoIframe.clone() 
      else $img.clone()
    )

    if floatPosition is 'left'
      $tableWrapper.find('tr').append $tableCell 
    else 
      $tableWrapper.find('tr').prepend $tableCell

    if $videoIframe.length > 0
      $videoIframe.after $tableWrapper 
    else 
      $img.after $tableWrapper

    if $videoIframe.length > 0
      $videoIframe.remove() 
    else
      $img.remove()

    return

  convertImgFloatCssPositionToTable: ($img, $editContainer, position) ->
    padding = 15
    paddingValues = if position is 'left' then "0 0 0 #{ padding }px" else "0 #{ padding }px 0 0"

    $tableCell = $('<td></td>')
    $tableCell.css({
      border: 'none',
      padding: paddingValues,
      margin: '0'
      })

    $videoIframe = $img.closest(@getClassFormat @_videoClass)
    if $videoIframe.length > 0
      $contextElement = $videoIframe.next().clone() 
    else
      $contextElement = $img.next().clone()

    editContainerWidth = parseFloat($editContainer.find('#content_table').width())
    contextWidth = editContainerWidth - parseFloat($img.attr('width')) - padding
    $contextElement.css 'width', contextWidth 

    $tableCell.attr 'width', contextWidth
    $tableCell.append $contextElement

    if $videoIframe.length > 0 
      $videoIframe.next().remove() 
    else 
      $img.next().remove()

    return $tableCell

  convertTextCssPositionToTable: () ->

    @_$editTemplatePageContainer.find(@_textContainerTags.join(', ')).each (i, element) =>
      elementCssClass = if $(element).attr('class') then $(element).attr('class').split(' ') else []

      switch elementCssClass
        when elementCssClass.indexOf('text-left') > -1 
          $tableWrapper = @getElementPosition('left', '', '')
        when elementCssClass.indexOf('text-right') > -1
          $tableWrapper = @getElementPosition('right', '', '')
        when elementCssClass.indexOf('text-center') > -1
          $tableWrapper = @getElementPosition('center', '', '')
        else
          $tableWrapper = @getElementPosition('center', '', '')

      @adjustListCssProperties($(element))
      $tableWrapper.find('td').append($(element).clone())
      $(element).after($tableWrapper)
      $(element).remove()

  adjustListCssProperties: ($element) ->

    if $element.is('ul') or $element.is('ol')
      $element.css({
        margin: '10px'
        padding: '15px'
        })

  _fixMargin: () ->
    # Fix render margin (chromium render margin wrong)
    $(@_htmlDoc).find('article').css('margin', '')

  _getNumberValue: (value, unitPosition=-2) ->
    parseInt(value.slice(0, value.length - unitPosition))

  _getPaddingValue: (horizontalValue=true) ->

    if horizontalValue is true
      position = 'padding--left'
    else
      position = 'padding--top'

    paddingValue = $(@_htmlDoc).find('.article__content p').first().css(position)

    @_getNumberValue(paddingValue)

  _fixContentWidth: () ->

    paddingValue = @_getPaddingValue()

    $(@_htmlDoc).find('article').find(@_textContainerTags.join(', ')).each (index, value) =>
      origWidth = @_getNumberValue($(value).css('width'))
      
      # Set correct width (orig width - 2 * padding value)
      $(value).css
        width: origWidth - paddingValue * 2
 