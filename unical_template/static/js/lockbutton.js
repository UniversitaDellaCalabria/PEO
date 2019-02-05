// Blocca il pulsante se il trigger arriva dal pannello modal
$(function(){
	$(".lockbutton_trigger").one("click", function(){
		parent.jQuery(".lockbutton")
            .replaceWith('<div class="ui right floated labeled icon button">'+
                         '<i class="loading spinner icon" style="background:none"></i>'+
                         ' Attendi la fine del processo</div>');
    });
});

// Blocca il pulsante se il trigger arriva dal pulsante stesso
$(function(){
	$(".lockbutton_single").click(function(){
        $(this).replaceWith('<div class="ui button">'+
                            '<i class="loading spinner icon" style="background:none"></i>'+
                            ' Attendi la fine del processo</div>');
    });
});
