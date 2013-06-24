$(document).ready(function() {
	var setstartdate = $( "#setstartdate" ),
	setstarttime = $( "#setstarttime" ),
	setduration = $( "#setduration" ),
	setmsgstring = $( "#setmsgstring" ),
	sendnodeid = $( "#sendnodeid" ),
	senddstep = $( "#senddstep" ),
	cancelnodeid = $( "#cancelnodeid" ),
	canceldstep = $( "#canceldstep" ),
	allFields = $( [] ).add(setstartdate).add(setstarttime).add(setduration).add(setmsgstring).add(sendnodeid).add(senddstep).add(cancelnodeid).add(canceldstep),
	tips = $( ".validateTips" );
	$( "#setstartdate" ).datepicker({ minDate: new Date(2000, 1 - 1, 1), maxDate: new Date(2030, 1 - 1, 1), dateFormat: "yy-mm-dd" }).val();
	$( "#setstarttime" ).timepicker();
	set_msg_form_tips = $( "#set-msg-form-tips" );
	send_msg_form_tips = $( "#send-msg-form-tips" );
	cancel_msg_form_tips = $( "#cancel-msg-form-tips" );
	var requestMessageTimer;
	function resetAllTips() {
		set_msg_form_tips.text("All form fields are required.");
		send_msg_form_tips.text("All form fields are required.");
		cancel_msg_form_tips.text("All form fields are required.");
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
	function checkLengthRange( tip, o, n, minlen, maxlen ) {
		if (( o.val().length < minlen ) || ( o.val().length > maxlen )) {
			o.addClass( "ui-state-error" );
			updateTips( tip, "Length of " + n + " must be between " + minlen + " and " + maxlen + " characters." );
			return false;
		} else {
			return true;
		}
	}
	function checkRangeVal( tip, parse_fptr, o, o_value, n, min, max ) {
		if ( (isNaN(parse_fptr(o_value))) || (parse_fptr(o_value) < min) || (parse_fptr(o_value) > max) ) {
			o.addClass( "ui-state-error" );
			updateTips( tip, "Input " + n + " must be between " + min + " and " + max + "." );
			return false;
		} else {
			return true;
		}
	}
	function checkRange( tip, parse_fptr, o, n, min, max ) {
		return checkRangeVal(tip, parse_fptr, o, o.val(), n, min, max);
	}
	function checkDateRange( tip, dui, tui, o_value, n, min, max ) {
		if (isNaN(o_value)) {
			dui.addClass( "ui-state-error" );
			tui.addClass( "ui-state-error" );
			updateTips( tip, "Input " + n + " is invalid." );
			return false;
		} else if (o_value < min) {
			dui.addClass( "ui-state-error" );
			tui.addClass( "ui-state-error" );
			updateTips( tip, "Input " + n + " must be later than " + new Date(min).toLocaleString() + "." );
			return false;
		} else if (o_value > max) {
			dui.addClass( "ui-state-error" );
			tui.addClass( "ui-state-error" );
			updateTips( tip, "Input " + n + " must be earlier than " + new Date(max).toLocaleString() + "." );
			return false;
		} else {
			return true;
		}
	}
	function checkRegexpVal( tip, o, o_value, regexp, n ) {
		if ( !( regexp.test( o_value ) ) ) {
			o.addClass( "ui-state-error" );
			updateTips( tip, n );
			return false;
		} else {
			return true;
		}
	}
	function checkRegexp( tip, o, regexp, n ) {
		return checkRegexpVal(tip, o, o.val(), regexp, n);
	}
	function checkRadioGroup( tip, o_name, n ) {
		var radio = $("input:radio[name=\"" + o_name + "\"]:checked");
		if (radio.length == 0) {
			updateTips( tip, n );
			return false;
		} else {
			return true;
		}
	}
	function messageTransmissionTypeToString(value) {
		var transmissionTypeStringMap = {
			0x00 : "Normal",
			0x01 : "Normal & Interpan",
			0x02 : "Interpan",
		};
		var transmission_string = "";
		if (transmissionTypeStringMap[value & 0x03])
			transmission_string = transmissionTypeStringMap[value & 0x03];
		return transmission_string;
	}
	function messageImportanceToString(value) {
		var importanceStringMap = {
			0x00 : "Low",
			0x04 : "Medium",
			0x08 : "High",
			0x0C : "Critical",
		};
		var importance_string = "";
		if (importanceStringMap[value & 0x0C])
			importance_string = importanceStringMap[value & 0x0C];
		return importance_string;
	}
	function messageConfirmationToString(value) {
		var confirmation_string = "Not required";
		if (value & 0x80)
			confirmation_string = "Required";
		return confirmation_string;
	}
	function messageStartTimeToString(value) {
		var time_string = "";
		var intvalue = parseInt(value);
		if (!isNaN(intvalue)) {
			var zigbee_time_offset = Date.UTC(2000,1-1,1);
			var zigbee_time = intvalue;
			var pc_time = new Date(zigbee_time * 1000 + zigbee_time_offset);
			time_string = pc_time.toLocaleString();
		}
		return time_string;
	}
	function booleanToString(value) {
		var bool_string = "";
		if (value == true)
			bool_string = "Yes";
		else if (value == false)
			bool_string = "No";
		return bool_string;
	}
	function requestMessage() {
		$.ajax({
			type : "GET",
			url : "/msg/action",
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(response) {
				// Clear old text
				$( "#current-msg-valid" ).text("");
				$( "#current-msg-active" ).text("");
				$( "#current-msg-id" ).text("");
				$( "#current-msg-tx" ).text("");
				$( "#current-msg-importance" ).text("");
				$( "#current-msg-confirmation" ).text("");
				$( "#current-msg-start" ).text("");
				$( "#current-msg-duration" ).text("");
				$( "#current-msg-message" ).text("");
				// Set new text
				if (response.status == 0) {
					$( "#current-msg-valid" ).text(booleanToString(response.valid));
					$( "#current-msg-active" ).text(booleanToString(response.active));
					$( "#current-msg-id" ).text("0x" + response.id.toString(16));
					$( "#current-msg-tx" ).text(messageTransmissionTypeToString(response.ctrl));
					$( "#current-msg-importance" ).text(messageImportanceToString(response.ctrl));
					$( "#current-msg-confirmation" ).text(messageConfirmationToString(response.ctrl));
					$( "#current-msg-start" ).text(messageStartTimeToString(response.start));
					$( "#current-msg-duration" ).text(response.duration.toString(10) + " minutes");
					$( "#current-msg-message" ).text("\"" + response.message + "\"");
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
	$( "#set-msg-form" ).dialog({
		autoOpen: false,
		height: 500,
		width: 550,
		modal: true,
		buttons: {
			"Set Message": function() {
				var bValid = true;
				allFields.removeClass( "ui-state-error" );
				bValid = bValid && checkRegexp( set_msg_form_tips, setstartdate, /^\d{4}-\d{1,2}-\d{1,2}$/, "Start date format must be yyyy-mm-dd." );
				bValid = bValid && checkRegexp( set_msg_form_tips, setstarttime, /^\d{1,2}:\d{2}$/, "Start time format must be hh:mm." );
				// check date range
				var start_date_time = new Date(setstartdate.val() + "T" + setstarttime.val() + ":00");
				var start_date_time_utc_ms = Date.UTC(start_date_time.getUTCFullYear(), start_date_time.getUTCMonth(), start_date_time.getUTCDate(), start_date_time.getUTCHours(), start_date_time.getUTCMinutes());
				bValid = bValid && checkDateRange( set_msg_form_tips, setstartdate, setstarttime, start_date_time_utc_ms, "start date", Date.UTC(2000,1-1,1), Date.UTC(2030,1-1,1) );
				start_date_time_utc_ms = start_date_time_utc_ms - Date.UTC(2000,1-1,1);
				// duration
				bValid = bValid && checkRegexp( set_msg_form_tips, setduration, /^(0x){0,1}([0-9a-fA-F])+$/, "Duration must be a number." );
				bValid = bValid && checkRange( set_msg_form_tips, parseInt, setduration, "duration", 0, 0xFFFF );
				// transmission type must be selected
				bValid = bValid && checkRadioGroup( set_msg_form_tips, "settx", "Transmission must be selected" );
				var txradio = $("input:radio[name=\"settx\"]:checked");
				var tx_value = 0
				if (bValid) {
					tx_value = parseInt(txradio.val());
				}
				// importance must be selected
				bValid = bValid && checkRadioGroup( set_msg_form_tips, "setimportance", "Importance must be selected" );
				var importanceradio = $("input:radio[name=\"setimportance\"]:checked");
				var importance_value = 0
				if (bValid) {
					importance_value = parseInt(importanceradio.val());
				}
				// confirmation
				var setconfirmation_cbox = $("input:checkbox[name=\"setconfirmation\"]:checked");
				var setconfirmation_value = 0;
				setconfirmation_cbox.each(function () {
					setconfirmation_value = setconfirmation_value | parseInt($(this).val());
				});
				// message string
				bValid = bValid && checkLengthRange( set_msg_form_tips, setmsgstring, "message", 1, 254 );
				if ( bValid ) {
					var jsonData = {};
					jsonData["action"] = "set";
					jsonData["start"] = parseInt(start_date_time_utc_ms/1000);
					var duration_value = parseInt(setduration.val());
					if (duration_value == 0)
						duration_value = 0xFFFF;
					jsonData["duration"] = duration_value;
					jsonData["ctrl"] = tx_value | importance_value | setconfirmation_value;
					jsonData["message"] = setmsgstring.val();
					var args = JSON.stringify(jsonData);
					//alert(args);
					$( this ).dialog( "close" );
					$.ajax({
						type : "POST",
						url : "/msg/action",
						data : args,
						contentType : "application/json; charset=utf-8",
						dataType : "json",
						success : function(response) {
							if (response['status'] == 0) {
								clearTimeout(requestMessageTimer);
								requestMessageTimer = setTimeout(function () { requestMessage(); }, 1250);
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
	$( "#send-msg-form" ).dialog({
		autoOpen: false,
		height: 200,
		width: 300,
		modal: true,
		buttons: {
			"Send Message": function() {
				var bValid = true;
				allFields.removeClass( "ui-state-error" );
				var allnodes = sendnodeid.val().split(",");
				var allnodes_array = new Array();
				$.each(allnodes, function(index, value) {
					bValid = bValid && checkRegexpVal( send_msg_form_tips, sendnodeid, value.trim(), /^(0x){0,1}([0-9a-fA-F])+$/, "Node ID must be a number." );
					bValid = bValid && checkRangeVal( send_msg_form_tips, parseInt, sendnodeid, value.trim(), "node ID", 0, 0xFFFFFFFF );
					if (bValid)
						allnodes_array.push(parseInt(value.trim()))
				});
				var alleps = senddstep.val().split(",");
				var alleps_array = new Array();
				$.each(alleps, function(index, value) {
					bValid = bValid && checkRegexpVal( send_msg_form_tips, senddstep, value.trim(), /^(0x){0,1}([0-9a-fA-F])+$/, "End point must be a number." );
					bValid = bValid && checkRangeVal( send_msg_form_tips, parseInt, senddstep, value.trim(), "end point", 1, 240 );
					if (bValid)
						alleps_array.push(parseInt(value.trim()))
				});
				if ((bValid) && (allnodes_array.length != alleps_array.length)) {
					updateTips( send_msg_form_tips, "Node IDs and End Points do not match." );
					bValid = false;
				}
				if ( bValid ) {
					var jsonData = {};
					jsonData["action"] = "send";
					jsonData["nodes"] = allnodes_array;
					jsonData["eps"] = alleps_array;
					var args = JSON.stringify(jsonData);
					//alert(args);
					$( this ).dialog( "close" );
					$.ajax({
						type : "POST",
						url : "/msg/action",
						data : args,
						contentType : "application/json; charset=utf-8",
						dataType : "json",
						success : function(response) {
							if (response['status'] == 0) {
								clearTimeout(requestMessageTimer);
								requestMessageTimer = setTimeout(function () { requestMessage(); }, 1250);
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
	$( "#cancel-msg-form" ).dialog({
		autoOpen: false,
		height: 200,
		width: 300,
		modal: true,
		buttons: {
			"Cancel Message": function() {
				var bValid = true;
				allFields.removeClass( "ui-state-error" );
				var allnodes = cancelnodeid.val().split(",");
				var allnodes_array = new Array();
				$.each(allnodes, function(index, value) {
					bValid = bValid && checkRegexpVal( cancel_msg_form_tips, cancelnodeid, value.trim(), /^(0x){0,1}([0-9a-fA-F])+$/, "Node ID must be a number." );
					bValid = bValid && checkRangeVal( cancel_msg_form_tips, parseInt, cancelnodeid, value.trim(), "node ID", 0, 0xFFFFFFFF );
					if (bValid)
						allnodes_array.push(parseInt(value.trim()))
				});
				var alleps = canceldstep.val().split(",");
				var alleps_array = new Array();
				$.each(alleps, function(index, value) {
					bValid = bValid && checkRegexpVal( cancel_msg_form_tips, canceldstep, value.trim(), /^(0x){0,1}([0-9a-fA-F])+$/, "End point must be a number." );
					bValid = bValid && checkRangeVal( cancel_msg_form_tips, parseInt, canceldstep, value.trim(), "end point", 1, 240 );
					if (bValid)
						alleps_array.push(parseInt(value.trim()))
				});
				if ((bValid) && (allnodes_array.length != alleps_array.length)) {
					updateTips( cancel_msg_form_tips, "Node IDs and End Points do not match." );
					bValid = false;
				}
				if ( bValid ) {
					var jsonData = {};
					jsonData["action"] = "cancel";
					jsonData["nodes"] = allnodes_array;
					jsonData["eps"] = alleps_array;
					var args = JSON.stringify(jsonData);
					//alert(args);
					$( this ).dialog( "close" );
					$.ajax({
						type : "POST",
						url : "/msg/action",
						data : args,
						contentType : "application/json; charset=utf-8",
						dataType : "json",
						success : function(response) {
							if (response['status'] == 0) {
								clearTimeout(requestMessageTimer);
								requestMessageTimer = setTimeout(function () { requestMessage(); }, 1250);
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
	$( "#set-msg" )
	.button()
	.click(function() {
		var setconfirmation_cbox = $("input:checkbox[name=\"setconfirmation\"]:checked");
		setconfirmation_cbox.each(function () {
			$(this).prop('checked', false);
		});
		$("input:radio[name=\"setimportance\"]:checked").prop('checked', false);
		$("#setimportance_low").prop('checked', true);
		$("input:radio[name=\"settx\"]:checked").prop('checked', false);
		$("#settx_normal").prop('checked', true);
		$( "#set-msg-form" ).dialog( "open" );
	});
	$( "#send-msg" )
	.button()
	.click(function() {
		$( "#send-msg-form" ).dialog( "open" );
	});
	$( "#cancel-msg" )
	.button()
	.click(function() {
		$( "#cancel-msg-form" ).dialog( "open" );
	});
	$( "#clear-msg" )
	.button()
	.click(function() {
		var jsonData = {};
		jsonData["action"] = "clear";
		var args = JSON.stringify(jsonData);
		//alert(args);
		$.ajax({
			type : "POST",
			url : "/msg/action",
			data : args,
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(response) {
				if (response['status'] == 0) {
					clearTimeout(requestMessageTimer);
					requestMessageTimer = setTimeout(function () { requestMessage(); }, 1250);
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
	$( "#refresh-msg" )
	.button()
	.click(function() {
		clearTimeout(requestMessageTimer);
		requestMessageTimer = setTimeout(function () { requestMessage(); }, 1250);
	});
	requestMessage();
});
