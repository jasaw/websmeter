$(document).ready(function() {
	var addmacaddr = $( "#addmacaddr" ),
	addinstallcode = $( "#addinstallcode" ),
	addpreconfkey = $( "#addpreconfkey" ),
	rmmacaddr = $( "#rmmacaddr" ),
	allFields = $( [] ).add( addmacaddr ).add( addinstallcode ).add( addpreconfkey ).add( rmmacaddr ),
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
	function installCodeIsValid( installcode ) {
		if (installcode.length <= 4)
			return false;
		var s = installcode.slice(0,installcode.length-4);
		var s_crc = installcode.slice(installcode.length-4, installcode.length);
		if ((s.length > 1) && (!(s.length & 1)) && (s_crc.length == 4)) {
			var crc = 0xFFFF;
			var s_crc_value = 0;
			var i, j, data, ch, cl;
			for (i = s_crc.length/2-1; i >= 0; i--) {
				ch = parseInt(s_crc[i*2], 16);
				cl = parseInt(s_crc[i*2+1], 16);
				if ((isNaN(ch)) || (isNaN(cl))) {
					return false;
				}
				s_crc_value = (s_crc_value << 8) | (((ch << 4) | cl) & 0xFF);
			}
			for (i = 0; i < s.length/2; i++) {
				ch = parseInt(s[i*2], 16);
				cl = parseInt(s[i*2+1], 16);
				if ((isNaN(ch)) || (isNaN(cl))) {
					return false;
				}
				data = ((ch << 4) | cl) & 0xFF;
				for (j = 0; j < 8; j++, data >>= 1) {
					if ((crc & 0x0001) ^ (data & 0x0001))
						crc = ((crc >> 1) ^ 0x8408) & 0xFFFF;
					else
						crc >>= 1;
				}
			}
			crc = (~crc) & 0xFFFF;
			if (crc == s_crc_value)
				return true;
		}
		return false;
	}
	function requestAllKeys() {
		$.ajax({
			type : "GET",
			url : "/keys/action",
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
					$( "#max-link-keys" ).text(response.maxlinkkeys);
					if (response.hasOwnProperty('tclinkkey')) {
						$( "#tc-link-key tbody" ).empty();
						var used = "Yes";
						if (response.tclinkkey.used == 0) {
							used = "No";
						}
						$( "#tc-link-key tbody" ).append( "<tr>" +
						"<td>" + response.tclinkkey.mac + "</td>" +
						"<td>" + response.tclinkkey.key + "</td>" +
						"<td>" + used + "</td>" +
						"</tr>" );
						$( "#tc-link-key-info" ).show();
					} else {
						$( "#tc-link-key-info" ).hide();
					}
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
	$( "#add-link-key-form" ).dialog({
		autoOpen: false,
		height: 260,
		width: 580,
		modal: true,
		buttons: {
			"Add/Update link key": function() {
				var bValid = true;
				var hasKeyInput = false;
				allFields.removeClass( "ui-state-error" );
				bValid = bValid && checkLength( addmacaddr, "MAC address", 16 );
				bValid = bValid && checkRegexp( addmacaddr, /^([0-9a-fA-F])+$/, "MAC address must be in hex." );
				if ( addinstallcode.val().length != 0 ) {
					hasKeyInput = true;
					if (( addinstallcode.val().length != 6*2 ) &&
					    ( addinstallcode.val().length != 8*2 ) &&
					    ( addinstallcode.val().length != 12*2 ) &&
					    ( addinstallcode.val().length != 16*2 )) {
						addinstallcode.addClass( "ui-state-error" );
						updateTips( "Length of installation code must be 12, 16, 24, 32 characters." );
						bValid = false;
					}
					bValid = bValid && checkRegexp( addinstallcode, /^([0-9a-fA-F])+$/, "Installation code must be in hex." );
					if (!installCodeIsValid(addinstallcode.val())) {
						addinstallcode.addClass( "ui-state-error" );
						updateTips( "Installation code CRC error." );
						bValid = false;
					}
				}
				if ( addpreconfkey.val().length != 0 ) {
					hasKeyInput = true;
					bValid = bValid && checkLength( addpreconfkey, "pre-configured link key", 32 );
					bValid = bValid && checkRegexp( addpreconfkey, /^([0-9a-fA-F])+$/, "Link key must be in hex." );
				}
				if (( bValid ) && ( hasKeyInput )) {
					var jsonData = {};
					jsonData["action"] = "addlinkkey";
					jsonData["mac"] = addmacaddr.val();
					if ( addinstallcode.val().length != 0 ) {
						jsonData["icode"] = addinstallcode.val();
					}
					if ( addpreconfkey.val().length != 0 ) {
						jsonData["pckey"] = addpreconfkey.val();
					}
					var args = JSON.stringify(jsonData);
					//alert(args);
					$( this ).dialog( "close" );
					$.ajax({
						type : "POST",
						url : "/keys/action",
						data : args,
						contentType : "application/json; charset=utf-8",
						dataType : "json",
						success : function(response) {
							if (response['status'] == 0) {
								clearTimeout(requestAllKeysTimer);
								requestAllKeysTimer = setTimeout(function () { requestAllKeys(); }, 750);
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
					jsonData["action"] = "rmlinkkey";
					jsonData["mac"] = rmmacaddr.val();
					var args = JSON.stringify(jsonData);
					//alert(args);
					$( this ).dialog( "close" );
					$.ajax({
						type : "POST",
						url : "/keys/action",
						data : args,
						contentType : "application/json; charset=utf-8",
						dataType : "json",
						success : function(response) {
							if (response['status'] == 0) {
								clearTimeout(requestAllKeysTimer);
								requestAllKeysTimer = setTimeout(function () { requestAllKeys(); }, 750);
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
	$( "#change-network-key" )
	.button()
	.click(function() {
		// Broadcast new network key now
		var jsonData = {};
		jsonData["action"] = "updatenwkkey";
		var args = JSON.stringify(jsonData);
		//alert(args);
		$.ajax({
			type : "POST",
			url : "/keys/action",
			data : args,
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(response) {
				if (response['status'] == 0) {
					clearTimeout(requestAllKeysTimer);
					requestAllKeysTimer = setTimeout(function () { requestAllKeys(); }, 750);
				}
				//else
				//	alert(response['errormsg']);
			},
			error : function(response) {
				//alert(response.errormsg);
				alert("Unable to contact server. Please try again.");
			}
		});
	});
	$( "#refresh-link-keys" )
	.button()
	.click(function() {
		clearTimeout(requestAllKeysTimer);
		requestAllKeysTimer = setTimeout(function () { requestAllKeys(); }, 750);
	});
	$( "#tc-link-key-info" ).hide();
	requestAllKeys();
});
