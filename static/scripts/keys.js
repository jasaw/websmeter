$(document).ready(function() {
	var addmacaddr = $( "#addmacaddr" ),
	addpreconfkey = $( "#addpreconfkey" ),
	rmmacaddr = $( "#rmmacaddr" ),
	allFields = $( [] ).add( addmacaddr ).add( addpreconfkey ).add( rmmacaddr ),
	tips = $( ".validateTips" );
	var requestAllKeysTimer;
	function updateTips( t ) {
		tips.text( t ).addClass( "ui-state-highlight" );
		setTimeout(function() {
			tips.removeClass( "ui-state-highlight", 1500 );
		}, 500 );
	}
	function checkLength( o, n, len ) {
		if ( o.val().length != len ) {
			o.addClass( "ui-state-error" );
			updateTips( "Length of " + n + " must be " + len + " characters." );
			return false;
		} else {
			return true;
		}
	}
	function checkRegexp( o, regexp, n ) {
		if ( !( regexp.test( o.val() ) ) ) {
			o.addClass( "ui-state-error" );
			updateTips( n );
			return false;
		} else {
			return true;
		}
	}
	function requestAllKeys() {
		$.ajax({
			type : "GET",
			url : "/keys/getkeys",
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(response) {
				//$.each(response, function(key, value) {
				//	alert(key + " : " + value);
				//});
				if (response.status == 0) {
					$( "#link-keys tbody" ).empty();
					//alert(response.nwkkey.key + "(" + response.nwkkey.seq + ")");
					$( "#nwk-key" ).text(response.nwkkey.key);
					$( "#nwk-key-seq" ).text(response.nwkkey.seq);
					$.each(response.linkkey, function(key, value) {
						//alert(value.mac + ", " + value.key + ", " + value.used);
						var used = "Yes";
						if (value.used == 0) {
							used = "No";
						}
						$( "#link-keys tbody" ).append( "<tr>" +
						"<td>" + value.mac + "</td>" +
						"<td>" + value.key + "</td>" +
						"<td>" + used + "</td>" +
						"</tr>" );
					});
				}
			},
			error : function(response) {
				alert(response.errormsg);
			}
		});
	}
	$( "#add-link-key-form" ).dialog({
		autoOpen: false,
		height: 230,
		width: 500,
		modal: true,
		buttons: {
			"Add/Update link key": function() {
				var bValid = true;
				allFields.removeClass( "ui-state-error" );
				bValid = bValid && checkLength( addmacaddr, "MAC address", 16 );
				bValid = bValid && checkRegexp( addmacaddr, /^([0-9a-fA-F])+$/, "MAC address must be in hex." );
				bValid = bValid && checkLength( addpreconfkey, "pre-configured link key", 32 );
				bValid = bValid && checkRegexp( addpreconfkey, /^([0-9a-fA-F])+$/, "Link key must be in hex." );
				if ( bValid ) {
					var jsonData = {};
					jsonData["mac"] = addmacaddr.val();
					jsonData["key"] = addpreconfkey.val();
					var args = JSON.stringify(jsonData);
					//alert(args);
					$( this ).dialog( "close" );
					$.ajax({
						type : "POST",
						url : "/keys/addkey",
						data : args,
						contentType : "application/json; charset=utf-8",
						dataType : "json",
						success : function(response) {
							if (response['status'] == 0) {
								clearTimeout(requestAllKeysTimer);
								requestAllKeysTimer = setTimeout(function () { requestAllKeys(); }, 750);
							}
						},
						error : function(response) {
							alert(response.errormsg);
						}
					});
				}
			},
			Cancel: function() {
				$( this ).dialog( "close" );
			}
		},
		close: function() {
			allFields.val( "" ).removeClass( "ui-state-error" );
		}
	});
	$( "#rm-link-key-form" ).dialog({
		autoOpen: false,
		height: 210,
		width: 500,
		modal: true,
		buttons: {
			"Remove link key": function() {
				var bValid = true;
				allFields.removeClass( "ui-state-error" );
				bValid = bValid && checkLength( rmmacaddr, "MAC address", 16 );
				bValid = bValid && checkRegexp( rmmacaddr, /^([0-9a-fA-F])+$/, "MAC address must be in hex." );
				if ( bValid ) {
					var jsonData = {};
					jsonData["mac"] = rmmacaddr.val();
					var args = JSON.stringify(jsonData);
					//alert(args);
					$( this ).dialog( "close" );
					$.ajax({
						type : "POST",
						url : "/keys/rmkey",
						data : args,
						contentType : "application/json; charset=utf-8",
						dataType : "json",
						success : function(response) {
							if (response['status'] == 0) {
								clearTimeout(requestAllKeysTimer);
								requestAllKeysTimer = setTimeout(function () { requestAllKeys(); }, 750);
							}
						},
						error : function(response) {
							alert(response.errormsg);
						}
					});
				}
			},
			Cancel: function() {
				$( this ).dialog( "close" );
			}
		},
		close: function() {
			allFields.val( "" ).removeClass( "ui-state-error" );
		}
	});
	$( "#add-link-key" )
	.button()
	.click(function() {
		$( "#add-link-key-form" ).dialog( "open" );
	});
	$( "#rm-link-key" )
	.button()
	.click(function() {
		$( "#rm-link-key-form" ).dialog( "open" );
	});
	$( "#refresh-link-keys" )
	.button()
	.click(function() {
		clearTimeout(requestAllKeysTimer);
		requestAllKeysTimer = setTimeout(function () { requestAllKeys(); }, 750);
	});
	requestAllKeys();
});
