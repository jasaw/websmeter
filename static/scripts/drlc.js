$(document).ready(function() {
	var addueg = $( "#addueg" ),
	addstartdate = $( "#addstartdate" ),
	addstarttime = $( "#addstarttime" ),
	addduration = $( "#addduration" ),
	addcrit_utility_level = $( "#addcrit_utility_level" ),
	addavgload = $( "#addavgload" ),
	adddutycycle = $( "#adddutycycle" ),
	addctsp = $( "#addctsp" ),
	addhtsp = $( "#addhtsp" ),
	addctos = $( "#addctos" ),
	addhtos = $( "#addhtos" ),
	allFields = $( [] ).add( addueg ).add( addstartdate ).add( addstarttime ).add( addduration ).add( addcrit_utility_level ).add( addavgload ).add( adddutycycle ).add( addctsp ).add( addhtsp ).add( addctos ).add( addhtos ),
	tips = $( ".validateTips" );
	$( "#addstartdate" ).datepicker({ minDate: new Date(2000, 1 - 1, 1), maxDate: new Date(2030, 1 - 1, 1) });
	$( "#addstarttime" ).timepicker();
	add_drlc_event_form_tips = $( "#add-drlc-event-form-tips" );
	rm_drlc_event_form_tips = $( "#rm-drlc-event-form-tips" );
	var requestDrlcEventsTimer;
	function resetAllTips() {
		add_drlc_event_form_tips.text("Leave unused optional fields empty.");
		rm_drlc_event_form_tips.text("All form fields are required.");
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
	function requestDrlcEvents() {
		alert("Get DRLC events not implemented yet");
		/*
		$.ajax({
			type : "GET",
			url : "/drlc/event",
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
		*/
	}
	$( "#add-drlc-event-form" ).dialog({
		autoOpen: false,
		height: 700,
		width: 550,
		modal: true,
		buttons: {
			"Add DRLC Event": function() {
				alert("Add DRLC event not implemented yet");
				/*
				var bValid = true;
				allFields.removeClass( "ui-state-error" );
				bValid = bValid && checkRegexp( nwk_form_join_form_tips, radiochannel, /^(0x)*([0-9a-fA-F])*$/, "Radio channel must be a number." );
				if ( radiochannel.val().length != 0 )
					bValid = bValid && checkRange( nwk_form_join_form_tips, radiochannel, "radio channel", 11, 26 );
				bValid = bValid && checkRegexp( nwk_form_join_form_tips, radiopower, /^(0x)*([0-9a-fA-F])*$/, "Radio power must be a number." );
				if ( radiopower.val().length != 0 )
					bValid = bValid && checkRange( nwk_form_join_form_tips, radiopower, "radio power", 0, 3 );
				bValid = bValid && checkRegexp( nwk_form_join_form_tips, panid, /^(0x)*([0-9a-fA-F])*$/, "PAN ID must be a number." );
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
						url : "/drlc/event",
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
				*/
			},
			Cancel: function() {
				$( this ).dialog( "close" );
			}
		},
		close: function() {
			allFields.val( "" ).removeClass( "ui-state-error" );
		}
	});
	$( "#rm-drlc-event-form" ).dialog({
		autoOpen: false,
		height: 180,
		width: 300,
		modal: true,
		buttons: {
			"Remove DRLC event": function() {
				alert("Remove DRLC event not implemented yet");
			},
			Cancel: function() {
				$( this ).dialog( "close" );
			}
		},
		close: function() {
			allFields.val( "" ).removeClass( "ui-state-error" );
		}
	});
	$( "#add-drlc-event" )
	.button()
	.click(function() {
		$( "#add-drlc-event-form" ).dialog( "open" );
	});
	$( "#rm-drlc-event" )
	.button()
	.click(function() {
		$( "#rm-drlc-event-form" ).dialog( "open" );
	});
	$( "#rm-all-drlc-events" )
	.button()
	.click(function() {
		alert("Not implemented yet.");
	});
	$( "#refresh-drlc-events" )
	.button()
	.click(function() {
		clearTimeout(requestDrlcEventsTimer);
		requestDrlcEventsTimer = setTimeout(function () { requestDrlcEvents(); }, 750);
	});
	requestDrlcEvents();
});
