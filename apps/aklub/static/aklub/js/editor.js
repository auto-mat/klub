(function() {
  window.onload = function() {
    var editor;
    ContentTools.StylePalette.add([
      new ContentTools.Style("By-line", "article__by-line", ["p"]),
      new ContentTools.Style("Caption", "article__caption", ["p"]),
      new ContentTools.Style("Example", "example", ["pre"]),
      new ContentTools.Style("Example + Good", "example--good", ["pre"]),
      new ContentTools.Style("Example + Bad", "example--bad", ["pre"]),
      new ContentTools.Style(
        "AutoMat-Poppins-Light-Font",
        "article__automat-poppins-light-font",
        ["p"]
      ),
      new ContentTools.Style(
        "AutoMat-Poppins-Thin-Font",
        "article__automat-poppins-thin-font",
        ["p"]
      ),
      new ContentTools.Style(
        "AutoMat-Poppins-ExtraLight-Font",
        "article__automat-poppins-extralight-font",
        ["p"]
      ),
      new ContentTools.Style(
        "AutoMat-Poppins-Bold-Font",
        "article__automat-poppins-bold-font",
        ["p"]
      ),
      new ContentTools.Style(
        "AutoMat-Poppins-Regular-Font",
        "article__automat-poppins-regular-font",
        ["p"]
      ),
      new ContentTools.Style(
        "AutoMat-FormulaCondensed-AutoMat-Font",
        "article__automat-formulacondesed-font",
        ["p"]
      ),
      new ContentTools.Style(
        "AutoMat-Poppins-SemiBold-Font",
        "article__automat-poppins-semibold-font",
        ["p"]
      ),
      new ContentTools.Style(
        "AutoMat-Poppins-Medium-Font",
        "article__automat-poppins-medium-font",
        ["p"]
      )
    ]);

    editor = ContentTools.EditorApp.get();
    editor.init(".editable", "data-name");

    function getImages() {
      // Return an object containing image URLs and widths for all regions
      var descendants, i, images;

      images = {};
      for (name in editor.regions) {
        // Search each region for images
        descendants = editor.regions[name].descendants();
        for (i = 0; i < descendants.length; i++) {
          // Filter out elements that are not images
          if (descendants[i].constructor.name !== "Image") {
            continue;
          }
          images[descendants[i].attr("src")] = descendants[i].size()[0];
        }
      }

      return images;
    }
    editor.addEventListener("saved", function(ev) {
      var onStateChange,
        payload,
        regions,
        element,
        pageId,
        successSaveFlash,
        failSaveFlash,
        styles;
      // Collect the contents of each region into a FormData instance
      payload = new FormData();
      // Check that something changed
      regions = ev.detail().regions;
      if (Object.keys(regions).length == 0) {
        return;
      }
      styles = ev.detail().styles;
      payload.append("page", getTemplatePageUrl());
      payload.append("images", JSON.stringify(getImages()));
      payload.append("regions", JSON.stringify(regions));
      payload.append("styles", JSON.stringify(styles));
      // Send the updated content to the server to be saved
      onStateChange = function(ev) {
        // Check if the request is finished
        if (ev.target.readyState == 4) {
          editor.busy(false);
          if (ev.target.status == "201") {
            // Save was successful, notify the user with a flash
            successSaveFlash = new ContentTools.FlashUI("ok");
          } else {
            // Save failed, notify the user with a flash
            failSaveFlash = new ContentTools.FlashUI("no");
          }
        }
      };
      element = document.querySelector('meta[name="page-id"]');
      if (element != null) {
        pageId = element.getAttribute("content");
      }
      editHtmlTemplate.call(
        "post",
        window.reverse("html_template_editor:add"),
        payload,
        true,
        onStateChange
      );
    });
  };
}.call(this, editHtmlTemplate));
