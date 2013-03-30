$(document).ready(function() {
	$("input#mkevent").click(function() {
		// prepare user inputs in json format
		var args = '{"avgload":"' + $("input#avgload").val() + '"}';
		//alert(args);
		$.ajax({
			type : "POST",
			url : "/drlc/mkdrlc",
			data : args,
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(response) {
				// TODO: handle error response
				$.each(response, function(key, value) {
					alert(key + " : " + value);
				});
			},
			error : function(response) {
				alert(response.responseText);
			}
		});
	});
});

