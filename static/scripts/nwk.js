$(document).ready(function() {
	var radiochannel = $( "#radiochannel" ),
	radiopower = $( "#radiopower" ),
	panid = $( "#panid" ),
	pjoinduration = $( "#pjoinduration" ),
	bcastpjoin = $( "#bcastpjoin" ),
	expanid = $( "#expanid" ),
	allFields = $( [] ).add( radiochannel ).add( radiopower ).add( panid ).add( pjoinduration ).add( expanid ),
	nwk_form_join_form_tips = $( "#nwk-form-join-form-tips" );
	permit_join_form_tips = $( "#permit-join-form-tips" );
	update_expan_id_form_tips = $( "#update-expan-id-form-tips" );
	var requestNwkInfoTimer;
	function resetAllTips() {
		nwk_form_join_form_tips.text("Leave fields empty for automatic configuration.");
		permit_join_form_tips.text("All form fields are required.");
		update_expan_id_form_tips.text("All form fields are required.");
	}
	function updateTips( o, t ) {
		o.text( t ).addClass( "ui-state-highlight" );
		setTimeout(function() {
			o.removeClass( "ui-state-highlight", 1500 );
		}, 500 );
	}
	function checkLength( tip, o, n, len ) {
		if ( o.val().length != len ) {
			o.addClass( "ui-state-error" );
			updateTips( tip, "Length of " + n + " must be " + len + " characters." );
			return false;
		} else {
			return true;
		}
	}
	function checkRange( tip, o, n, min, max ) {
		if ( (isNaN(parseInt(o.val()))) || (parseInt(o.val()) < min) || (parseInt(o.val()) > max) ) {
			o.addClass( "ui-state-error" );
			updateTips( tip, "Input " + n + " must be between " + min + " and " + max + "." );
			return false;
		} else {
			return true;
		}
	}
	function checkRegexp( tip, o, regexp, n ) {
		if ( !( regexp.test( o.val() ) ) ) {
			o.addClass( "ui-state-error" );
			updateTips( tip, n );
			return false;
		} else {
			return true;
		}
	}
	function requestNwkInfo() {
		$.ajax({
			type : "GET",
			url : "/nwk/getinfo",
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(response) {
				//$.each(response, function(key, value) {
				//	alert(key + " : " + value);
				//});
				if (response.status == 0) {
					// Clear old text
					$( "#mynwkstatus" ).text("");
					$( "#mymacaddr" ).text("");
					$( "#mynodeid" ).text("");
					$( "#myendpoint" ).text("");
					$( "#mypanid" ).text("");
					$( "#myexpanid" ).text("");
					$( "#myradiochannel" ).text("");
					$( "#myradiopower" ).text("");
					// Set new text
					var nwk_is_up_str = "DOWN";
					if (response.nwk_is_up)
						nwk_is_up_str = "OK";
					var nodeidint = parseInt(response.node_id);
					var nodeidhexstring = "";
					if (!isNaN(nodeidint))
						nodeidhexstring = " (0x" + nodeidint.toString(16) + ")";
					var panidint = parseInt(response.pan_id);
					var panidhexstring = "";
					if (!isNaN(panidint))
						panidhexstring = " (0x" + panidint.toString(16) + ")";
					$( "#mynwkstatus" ).text(nwk_is_up_str);
					$( "#mymacaddr" ).text(response.mac);
					$( "#mynodeid" ).text(response.node_id + nodeidhexstring);
					$( "#myendpoint" ).text(response.end_point);
					$( "#mypanid" ).text(response.pan_id + panidhexstring);
					$( "#myexpanid" ).text(response.expan_id);
					$( "#myradiochannel" ).text(response.radio_channel);
					$( "#myradiopower" ).text(response.radio_power);
					// TODO: get network status, and prevent forming or joining network if network is already up
					// similarly for permit join
				}
			},
			error : function(response) {
				//alert(response.errormsg);
				alert("Unable to contact server. Please try again.");
			}
		});
	}
	function sendFormJoinNetwork(action, o) {
		var bValid = true;
		allFields.removeClass( "ui-state-error" );
		bValid = bValid && checkRegexp( nwk_form_join_form_tips, radiochannel, /^(0x){0,1}([0-9a-fA-F])*$/, "Radio channel must be a number." );
		if ( radiochannel.val().length != 0 )
			bValid = bValid && checkRange( nwk_form_join_form_tips, radiochannel, "radio channel", 11, 26 );
		bValid = bValid && checkRegexp( nwk_form_join_form_tips, radiopower, /^(0x){0,1}([0-9a-fA-F])*$/, "Radio power must be a number." );
		if ( radiopower.val().length != 0 )
			bValid = bValid && checkRange( nwk_form_join_form_tips, radiopower, "radio power", 0, 3 );
		bValid = bValid && checkRegexp( nwk_form_join_form_tips, panid, /^(0x){0,1}([0-9a-fA-F])*$/, "PAN ID must be a number." );
		if ( bValid ) {
			var jsonData = {};
			jsonData["action"] = action;
			if ( radiochannel.val().length != 0 )
				jsonData["channel"] = parseInt(radiochannel.val());
			if ( radiopower.val().length != 0 )
				jsonData["power"] = parseInt(radiopower.val());
			if ( panid.val().length != 0 )
				jsonData["panid"] = parseInt(panid.val());
			var args = JSON.stringify(jsonData);
			//alert(args);
			o.dialog( "close" );
			$.ajax({
				type : "POST",
				url : "/nwk/action",
				data : args,
				contentType : "application/json; charset=utf-8",
				dataType : "json",
				success : function(response) {
					if (response['status'] == 0) {
						clearTimeout(requestNwkInfoTimer);
						requestNwkInfoTimer = setTimeout(function () { requestNwkInfo(); }, 2000);
					}
				},
				error : function(response) {
					//alert(response.errormsg);
					alert("Unable to contact server. Please try again.");
				}
			});
		}
	}
	$( "#nwk-form-join-form" ).dialog({
		autoOpen: false,
		height: 260,
		width: 500,
		modal: true,
		buttons: {
			"Form network": function() {
				sendFormJoinNetwork("form", $(this));
			},
			"Join network": function() {
				sendFormJoinNetwork("join", $(this));
			},
			Cancel: function() {
				$( this ).dialog( "close" );
			}
		},
		close: function() {
			allFields.val( "" ).removeClass( "ui-state-error" );
			resetAllTips();
		}
	});
	$( "#permit-join-form" ).dialog({
		autoOpen: false,
		height: 260,
		width: 500,
		modal: true,
		buttons: {
			"Permit join": function() {
				var bValid = true;
				allFields.removeClass( "ui-state-error" );
				bValid = bValid && checkRegexp( permit_join_form_tips, pjoinduration, /^(0x){0,1}([0-9a-fA-F])+$/, "Permit join duration must be a number." );
				bValid = bValid && checkRange( permit_join_form_tips, pjoinduration, "permit join duration", 0, 255 );
				if ( bValid ) {
					var bcast = 0;
					if ($('#bcastpjoin').is(':checked') == true)
						bcast = 1;
					var jsonData = {};
					jsonData["action"] = "pjoin";
					jsonData["duration"] = parseInt(pjoinduration.val());
					jsonData["broadcast"] = bcast;
					var args = JSON.stringify(jsonData);
					//alert(args);
					$( this ).dialog( "close" );
					$.ajax({
						type : "POST",
						url : "/nwk/action",
						data : args,
						contentType : "application/json; charset=utf-8",
						dataType : "json",
						success : function(response) {
							if (response['status'] == 0) {
								clearTimeout(requestNwkInfoTimer);
								requestNwkInfoTimer = setTimeout(function () { requestNwkInfo(); }, 1000);
							}
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
			resetAllTips();
		}
	});
	$( "#update-expan-id-form" ).dialog({
		autoOpen: false,
		height: 210,
		width: 500,
		modal: true,
		buttons: {
			"Apply": function() {
				var bValid = true;
				allFields.removeClass( "ui-state-error" );
				bValid = bValid && checkLength( update_expan_id_form_tips, expanid, "extended PAN ID", 16 );
				bValid = bValid && checkRegexp( update_expan_id_form_tips, expanid, /^([0-9a-fA-F])+$/, "Extended PAN ID must be in hex." );
				if ( bValid ) {
					var jsonData = {};
					jsonData["action"] = "setexpanid";
					jsonData["expanid"] = expanid.val();
					var args = JSON.stringify(jsonData);
					//alert(args);
					$( this ).dialog( "close" );
					$.ajax({
						type : "POST",
						url : "/nwk/action",
						data : args,
						contentType : "application/json; charset=utf-8",
						dataType : "json",
						success : function(response) {
							if (response['status'] == 0) {
								clearTimeout(requestNwkInfoTimer);
								requestNwkInfoTimer = setTimeout(function () { requestNwkInfo(); }, 1000);
							}
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
			resetAllTips();
		}
	});
	$( "#nwk-leave-confirm" ).dialog({
		autoOpen: false,
		height: 180,
		width: 300,
		modal: true,
		buttons: {
			"Leave network": function() {
				var jsonData = {};
				jsonData["action"] = "leave";
				var args = JSON.stringify(jsonData);
				//alert(args);
				$( this ).dialog( "close" );
				$.ajax({
					type : "POST",
					url : "/nwk/action",
					data : args,
					contentType : "application/json; charset=utf-8",
					dataType : "json",
					success : function(response) {
						if (response['status'] == 0) {
							clearTimeout(requestNwkInfoTimer);
							requestNwkInfoTimer = setTimeout(function () { requestNwkInfo(); }, 2000);
						}
					},
					error : function(response) {
						//alert(response.errormsg);
						alert("Unable to contact server. Please try again.");
					}
				});
			},
			Cancel: function() {
				$( this ).dialog( "close" );
			}
		},
		close: function() {
			allFields.val( "" ).removeClass( "ui-state-error" );
			resetAllTips();
		}
	});
	$( "#nwk-form-join" )
	.button()
	.click(function() {
		$( "#nwk-form-join-form" ).dialog( "open" );
	});
	$( "#permit-join" )
	.button()
	.click(function() {
		$('#bcastpjoin').prop('checked', true);
		$( "#permit-join-form" ).dialog( "open" );
	});
	$( "#update-expan-id" )
	.button()
	.click(function() {
		$( "#update-expan-id-form" ).dialog( "open" );
	});
	$( "#nwk-leave" )
	.button()
	.click(function() {
		$( "#nwk-leave-confirm" ).dialog( "open" );
	});
	$( document ).tooltip();
	resetAllTips();
	requestNwkInfo();
});
