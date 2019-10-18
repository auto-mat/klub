var csrftoken = getCookie('csrftoken')

var editHtmlTemplate = {}

editHtmlTemplate.domain = window.origin

editHtmlTemplate.call = function (type, url, data, auth, onSuccess, onError) {
  xhr = new XMLHttpRequest()
  xhr.addEventListener('readystatechange', onSuccess)

  if (type == null) {
    type = 'get'
  }
  if (url == null) {
    url = '/'
  }
  if (data == null) {
    data = null
  }
  if (auth == null) {
    auth = true
  }
  if (onSuccess == null) {
    onSuccess = null
  }
  if (onError == null) {
    onError = null
  }
  url = '' + this.domain + url
  switch (type) {
    case 'get':
      xhr.open('GET', url)
      break
    case 'post':
      xhr.open('POST', url)
      break
    case 'put':
      xhr.open('PUT', url)
      break
    case 'patch':
      xhr.open('PATH', url)
      break
    case 'delete':
      xhr.open('DELETE', url)
      break
    default:
        console.log("Request type " + type + " is not supported");
  }
  xhr.setRequestHeader('X-CSRFToken', csrftoken)

  if (data) {
    xhr.send(data)
  }
}
