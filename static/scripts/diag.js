$(document).ready(function() {
	var requestDiagInfoTimer;
	function requestDiagInfo() {
		$.ajax({
			type : "GET",
			url : "/diag/action",
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(response) {
				$( "#child-table tbody" ).empty();
				$( "#neighbour-table tbody" ).empty();
				$( "#route-table tbody" ).empty();
				//$.each(response, function(key, value) {
				//	alert(key + " : " + value);
				//});
				if (response.status == 0) {
					// child table
					$.each(response.child, function(index, value) {
						$( "#child-table tbody" ).append( "<tr>" +
						"<td>" + "0x" + value.nodeid.toString(16) + "</td>" +
						"<td>" + value.nodetype + "</td>" +
						"<td>" + value.macaddr + "</td>" +
						"</tr>" );
					});
					$( "#max-num-child-entries" ).text(response.childmaxsize);
					// neighbour table
					$.each(response.neighbour, function(index, value) {
						$( "#neighbour-table tbody" ).append( "<tr>" +
						"<td>" + "0x" + value.nodeid.toString(16) + "</td>" +
						"<td>" + value.macaddr + "</td>" +
						"<td>" + value.lqi.toString(10) + "</td>" +
						"<td>" + value.in.toString(10) + "</td>" +
						"<td>" + value.out.toString(10) + "</td>" +
						"<td>" + value.age.toString(10) + "</td>" +
						"</tr>" );
					});
					$( "#max-num-neighbour-entries" ).text(response.neighbourmaxsize);
					// route table
					$.each(response.route, function(index, value) {
						$( "#route-table tbody" ).append( "<tr>" +
						"<td>" + "0x" + value.nodeid.toString(16) + "</td>" +
						"<td>" + "0x" + value.next.toString(16) + "</td>" +
						"<td>" + value.age.toString(10) + "</td>" +
						"<td>" + value.conc + "</td>" +
						"<td>" + value.status + "</td>" +
						"</tr>" );
					});
					$( "#max-num-route-entries" ).text(response.routemaxsize);
				}
				//else
				//	alert(response['errormsg']);
			},
			error : function(response) {
				//alert(response.errormsg);
				alert("Unable to contact server. Please try again.");
			}
		});
	}
	$( "#refresh-all-tables" )
	.button()
	.click(function() {
		clearTimeout(requestDiagInfoTimer);
		requestDiagInfoTimer = setTimeout(function () { requestDiagInfo(); }, 500);
	});
	requestDiagInfo();
});
