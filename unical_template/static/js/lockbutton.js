var text = '<div class="ui labeled icon button">'+
           '<i class="loading spinner icon" style="background:none"></i>'+
           ' Attendi la fine del processo</div>'

$(function(){
    // Blocca il pulsante se il trigger arriva dal pannello modal
	$(".lockbutton_trigger").one("click", function(){
		parent.jQuery(".lockbutton").replaceWith(text);
    });

    // Blocca il pulsante se il trigger arriva dal pulsante stesso
    $(".lockbutton_single").click(function(){
        $(this).replaceWith(text);
    });

    // Blocca il pulsante se il trigger dal submit di un form
    $("#lockbutton_form").submit(function(){
        $(".lockbutton_submit").replaceWith(text);
    });
});
