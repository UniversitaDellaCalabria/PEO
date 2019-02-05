/*jslint browser:true */
$(function ($) {
    'use strict';
    var textarea_selector = "textarea";
    function adaptiveheight(a) {
        $(a).height(0);

        var scrollval = $(a)[0].scrollHeight;
        $(a).height(scrollval);
        if (parseInt(a.style.height, 10) > $(window).height()) {
            var i = a.selectionEnd;
            if (i >= 0) {
                $(document).scrollTop(parseInt(a.style.height, 10));
            } else {
                $(document).scrollTop(0);
            }
        }
    }
    $(textarea_selector).click(function (e) {
        adaptiveheight(this);
    });
    $(textarea_selector).keyup(function (e) {
        adaptiveheight(this);
    });
    // init
    $(textarea_selector).each(function () {
        adaptiveheight(this);
    });
});
