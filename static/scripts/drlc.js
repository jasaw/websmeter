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
	sendeventid = $( "#sendeventid" ),
	sendnodeid = $( "#sendnodeid" ),
	senddstep = $( "#senddstep" ),
	rmeventid = $( "#rmeventid" ),
	allFields = $( [] ).add(addueg).add(addstartdate).add(addstarttime).add(addduration).add(addcrit_utility_level).add(addavgload).add(adddutycycle).add(addctsp).add(addhtsp).add(addctos).add(addhtos).add(sendeventid).add(sendnodeid).add(senddstep).add(rmeventid),
	tips = $( ".validateTips" );
	$( "#addstartdate" ).datepicker({ minDate: new Date(2000, 1 - 1, 1), maxDate: new Date(2030, 1 - 1, 1), dateFormat: "yy-mm-dd" }).val();
	$( "#addstarttime" ).timepicker();
	add_drlc_event_form_tips = $( "#add-drlc-event-form-tips" );
	send_drlc_event_form_tips = $( "#send-drlc-event-form-tips" );
	rm_drlc_event_form_tips = $( "#rm-drlc-event-form-tips" );
	var requestDrlcEventsTimer;
	function resetAllTips() {
		add_drlc_event_form_tips.text("Leave unused optional fields empty.");
		send_drlc_event_form_tips.text("All form fields are required.");
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
	function drlcDeviceClassToString(value) {
		var deviceClassStringMap = {
			0x0001 : "HVAC compressor or furnace",
			0x0002 : "Strip or baseboard heaters",
			0x0004 : "Water heater",
			0x0008 : "Pool pump or spa",
			0x0010 : "Smart appliances",
			0x0020 : "Irrigation pump",
			0x0040 : "Managed commercial & industrial loads",
			0x0080 : "Simple misc or residential loads",
			0x0100 : "Exterior lighting",
			0x0200 : "Interior lighting",
			0x0400 : "Electric vehicle",
			0x0800 : "Generation systems",
		};
		var device_class_string = "<ul>";
		for (var i=0; i < 12; i++) {
			if ((value & (1 << i)) && (deviceClassStringMap[value & (1 << i)])) {
				device_class_string = device_class_string + "<li>" + deviceClassStringMap[value & (1 << i)] + "</li>";
			}
		}
		device_class_string = device_class_string + "</ul>";
		return device_class_string;
	}
	function drlcUegToString(value) {
		var ueg_string = "";
		if (value == 0) {
			ueg_string = "All";
		} else {
			var intvalue = parseInt(value);
			if (!isNaN(intvalue))
				ueg_string = "0x" + intvalue.toString(16);
		}
		return ueg_string;
	}
	function drlcStartTimeToString(value) {
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
	function drlcCriticalityToString(value) {
		var criticalityStringMap = {
			0x01 : "Green",
			0x02 : "Level 1",
			0x03 : "Level 2",
			0x04 : "Level 3",
			0x05 : "Level 4",
			0x06 : "Level 5",
			0x07 : "Emergency",
			0x08 : "Planned Outage",
			0x09 : "Service Disconnect",
			0x0A : "Utility Defined 1",
			0x0B : "Utility Defined 2",
			0x0C : "Utility Defined 3",
			0x0D : "Utility Defined 4",
			0x0E : "Utility Defined 5",
			0x0F : "Utility Defined 6",
		};
		var criticality_string = "";
		if (criticalityStringMap[value])
			criticality_string = criticalityStringMap[value];
		return criticality_string;
	}
	function drlcEventControlToString(value) {
		var eventControlStringMap = {
			0x00 : "No randomisation",
			0x01 : "Randomise start time",
			0x02 : "Randomise end time",
			0x03 : "Randomise start & end time",
		};
		var event_control_string = "";
		if (eventControlStringMap[value])
			event_control_string = eventControlStringMap[value];
		return event_control_string;
	}
	function drlcPercentLoadToString(value) {
		var percentload_string = "";
		var intvalue = parseInt(value);
		if (!isNaN(intvalue))
			percentload_string = intvalue.toString(10) + "%";
		return percentload_string;
	}
	function requestDrlcEvents() {
		$.ajax({
			type : "GET",
			url : "/drlc/event",
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(response) {
				$( "#drlc-events tbody" ).empty();
				//$.each(response, function(key, value) {
				//	alert(key + " : " + value);
				//});
				if (response.status == 0) {
					$.each(response.events, function(key, value) {
						var avgload_str = "";
						if (value.hasOwnProperty("avgload"))
							avgload_str = drlcPercentLoadToString(value.avgload);
						var dutycycle_str = "";
						if (value.hasOwnProperty("dutycycle"))
							dutycycle_str = drlcPercentLoadToString(value.dutycycle);
						var ctsp_str = "";
						if (value.hasOwnProperty("ctsp"))
							ctsp_str = (value.ctsp/100).toString(10) + "\u2103";
						var htsp_str = "";
						if (value.hasOwnProperty("htsp"))
							htsp_str = (value.htsp/100).toString(10) + "\u2103";
						var cto_str = "";
						if (value.hasOwnProperty("cto"))
							cto_str = (value.cto/10).toString(10) + "\u2103";
						var hto_str = "";
						if (value.hasOwnProperty("hto"))
							hto_str = (value.hto/10).toString(10) + "\u2103";
						$( "#drlc-events tbody" ).append( "<tr>" +
						"<td>" + "0x" + value.eid.toString(16) + "</td>" +
						"<td>" + drlcDeviceClassToString(value.dev) + "</td>" +
						"<td>" + drlcUegToString(value.ueg) + "</td>" +
						"<td>" + drlcStartTimeToString(value.start) + "</td>" +
						"<td>" + value.duration.toString(10) + "</td>" +
						"<td>" + drlcCriticalityToString(value.criticality) + "</td>" +
						"<td>" + drlcEventControlToString(value.ectrl) + "</td>" +
						"<td>" + avgload_str + "</td>" +
						"<td>" + dutycycle_str + "</td>" +
						"<td>" + ctsp_str + "</td>" +
						"<td>" + htsp_str + "</td>" +
						"<td>" + cto_str + "</td>" +
						"<td>" + hto_str + "</td>" +
						"</tr>" );
					});
					$( "#max-num-drlc-events" ).text(response.maxnumevents);
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
	$( "#add-drlc-event-form" ).dialog({
		autoOpen: false,
		height: 730,
		width: 550,
		modal: true,
		buttons: {
			"Add DRLC Event": function() {
				var bValid = true;
				allFields.removeClass( "ui-state-error" );
				// at least one device class must be selected
				var adddevcls_cbox = $("input:checkbox[name=\"adddevcls\"]:checked");
				var devcls_value = 0;
				adddevcls_cbox.each(function () {
					devcls_value = devcls_value | parseInt($(this).val());
				});
				if ((bValid) && (devcls_value == 0)) {
					updateTips( add_drlc_event_form_tips, "Please select at least one device class." );
					bValid = false;
				}
				var ueg_value = 0;
				bValid = bValid && checkRegexp( add_drlc_event_form_tips, addueg, /^(0x){0,1}([0-9a-fA-F])*$/, "Utility enrolment group must be a number." );
				if ( addueg.val().length != 0 ) {
					bValid = bValid && checkRange( add_drlc_event_form_tips, parseInt, addueg, "utility enrolment group", 0x00, 0xFF );
					if (bValid)
						ueg_value = parseInt(addueg.val());
				}
				bValid = bValid && checkRegexp( add_drlc_event_form_tips, addstartdate, /^\d{4}-\d{1,2}-\d{1,2}$/, "Start date format must be yyyy-mm-dd." );
				bValid = bValid && checkRegexp( add_drlc_event_form_tips, addstarttime, /^\d{1,2}:\d{2}$/, "Start time format must be hh:mm." );
				// check date range
				var start_date_time = new Date(addstartdate.val() + "T" + addstarttime.val() + ":00");
				var start_date_time_utc_ms = Date.UTC(start_date_time.getUTCFullYear(), start_date_time.getUTCMonth(), start_date_time.getUTCDate(), start_date_time.getUTCHours(), start_date_time.getUTCMinutes());
				bValid = bValid && checkDateRange( add_drlc_event_form_tips, addstartdate, addstarttime, start_date_time_utc_ms, "start date", Date.UTC(2000,1-1,1), Date.UTC(2030,1-1,1) );
				start_date_time_utc_ms = start_date_time_utc_ms - Date.UTC(2000,1-1,1);
				// duration
				bValid = bValid && checkRegexp( add_drlc_event_form_tips, addduration, /^(0x){0,1}([0-9a-fA-F])+$/, "Duration must be a number." );
				bValid = bValid && checkRange( add_drlc_event_form_tips, parseInt, addduration, "duration", 1, 1440 );
				// criticality must be selected
				bValid = bValid && checkRadioGroup( add_drlc_event_form_tips, "addcrit", "Criticality must be selected" );
				var critradio = $("input:radio[name=\"addcrit\"]:checked");
				var crit_value = 0
				if (bValid) {
					if (parseInt(critradio.val()) == -1) {
						bValid = bValid && checkRegexp( add_drlc_event_form_tips, addcrit_utility_level, /^(0x){0,1}([0-9a-fA-F])$/, "Utility defined criticality must be a number." );
						bValid = bValid && checkRange( add_drlc_event_form_tips, parseInt, addcrit_utility_level, "utility defined criticality", 1, 6 );
						crit_value = parseInt(addcrit_utility_level.val()) + 9;
					} else {
						crit_value = parseInt(critradio.val());
					}
				}
				// event control
				var addectrl_cbox = $("input:checkbox[name=\"addectrl\"]:checked");
				var ectrl_value = 0;
				addectrl_cbox.each(function () {
					ectrl_value = ectrl_value | parseInt($(this).val());
				});
				// optional inputs
				var num_optionals = 0;
				bValid = bValid && checkRegexp( add_drlc_event_form_tips, addavgload, /^(-){0,1}(0x){0,1}([0-9a-fA-F])*$/, "Average load must be a number." );
				if ( addavgload.val().length != 0 ) {
					bValid = bValid && checkRange( add_drlc_event_form_tips, parseInt, addavgload, "average load", -100, 100 );
					num_optionals = num_optionals + 1;
				}
				bValid = bValid && checkRegexp( add_drlc_event_form_tips, adddutycycle, /^(0x){0,1}([0-9a-fA-F])*$/, "Duty cycle must be a number." );
				if ( adddutycycle.val().length != 0 ) {
					bValid = bValid && checkRange( add_drlc_event_form_tips, parseInt, adddutycycle, "duty cycle", 0, 100 );
					num_optionals = num_optionals + 1;
				}
				bValid = bValid && checkRegexp( add_drlc_event_form_tips, addctsp, /^(-){0,1}([0-9])*(\.){0,1}([0-9])*$/, "Cooling temperature set point must be a number." );
				if ( addctsp.val().length != 0 ) {
					bValid = bValid && checkRange( add_drlc_event_form_tips, parseFloat, addctsp, "cooling temperature set point", -273.15, 327.67 );
					num_optionals = num_optionals + 1;
				}
				bValid = bValid && checkRegexp( add_drlc_event_form_tips, addhtsp, /^(-){0,1}([0-9])*(\.){0,1}([0-9])*$/, "Heating temperature set point must be a number." );
				if ( addhtsp.val().length != 0 ) {
					bValid = bValid && checkRange( add_drlc_event_form_tips, parseFloat, addhtsp, "heating temperature set point", -273.15, 327.67 );
					num_optionals = num_optionals + 1;
				}
				bValid = bValid && checkRegexp( add_drlc_event_form_tips, addctos, /^([0-9])*(\.){0,1}([0-9])*$/, "Cooling temperature offset must be a number." );
				if ( addctos.val().length != 0 ) {
					bValid = bValid && checkRange( add_drlc_event_form_tips, parseFloat, addctos, "cooling temperature offset", 0, 25.4 );
					num_optionals = num_optionals + 1;
				}
				bValid = bValid && checkRegexp( add_drlc_event_form_tips, addhtos, /^([0-9])*(\.){0,1}([0-9])*$/, "Heating temperature offset must be a number." );
				if ( addhtos.val().length != 0 ) {
					bValid = bValid && checkRange( add_drlc_event_form_tips, parseFloat, addhtos, "heating temperature offset", 0, 25.4 );
					num_optionals = num_optionals + 1;
				}
				if ((bValid) && (num_optionals == 0)) {
					updateTips( add_drlc_event_form_tips, "Please fill at least one optional input." );
					bValid = false;
				}
				if ( bValid ) {
					var jsonData = {};
					jsonData["action"] = "add";
					jsonData["dev"] = devcls_value;
					jsonData["ueg"] = ueg_value;
					jsonData["start"] = parseInt(start_date_time_utc_ms/1000);
					jsonData["duration"] = parseInt(addduration.val());
					jsonData["criticality"] = crit_value;
					jsonData["ectrl"] = ectrl_value;
					if (addavgload.val().length != 0)
						jsonData["avgload"] = parseInt(addavgload.val());
					if (adddutycycle.val().length != 0)
						jsonData["dutycycle"] = parseInt(adddutycycle.val());
					if (addctos.val().length != 0)
						jsonData["cto"] = parseInt(parseFloat(addctos.val())*10);
					if (addhtos.val().length != 0)
						jsonData["hto"] = parseInt(parseFloat(addhtos.val())*10);
					if (addctsp.val().length != 0)
						jsonData["ctsp"] = parseInt(parseFloat(addctsp.val())*100);
					if (addhtsp.val().length != 0)
						jsonData["htsp"] = parseInt(parseFloat(addhtsp.val())*100);
					var args = JSON.stringify(jsonData);
					//alert(args);
					$( this ).dialog( "close" );
					$.ajax({
						type : "POST",
						url : "/drlc/event",
						data : args,
						contentType : "application/json; charset=utf-8",
						dataType : "json",
						success : function(response) {
							if (response['status'] == 0) {
								clearTimeout(requestDrlcEventsTimer);
								requestDrlcEventsTimer = setTimeout(function () { requestDrlcEvents(); }, 750);
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
	$( "#send-drlc-event-form" ).dialog({
		autoOpen: false,
		height: 250,
		width: 300,
		modal: true,
		buttons: {
			"Send DRLC event": function() {
				var bValid = true;
				allFields.removeClass( "ui-state-error" );
				var allids = sendeventid.val().split(",");
				var allids_array = new Array();
				$.each(allids, function(index, value) {
					bValid = bValid && checkRegexpVal( send_drlc_event_form_tips, sendeventid, value.trim(), /^(0x){0,1}([0-9a-fA-F])+$/, "Event ID must be a number." );
					bValid = bValid && checkRangeVal( send_drlc_event_form_tips, parseInt, sendeventid, value.trim(), "event ID", 0, 0xFFFFFFFF );
					if (bValid)
						allids_array.push(parseInt(value.trim()))
				});
				var allnodes = sendnodeid.val().split(",");
				var allnodes_array = new Array();
				$.each(allnodes, function(index, value) {
					bValid = bValid && checkRegexpVal( send_drlc_event_form_tips, sendnodeid, value.trim(), /^(0x){0,1}([0-9a-fA-F])+$/, "Node ID must be a number." );
					bValid = bValid && checkRangeVal( send_drlc_event_form_tips, parseInt, sendnodeid, value.trim(), "node ID", 0, 0xFFFFFFFF );
					if (bValid)
						allnodes_array.push(parseInt(value.trim()))
				});
				var alleps = senddstep.val().split(",");
				var alleps_array = new Array();
				$.each(alleps, function(index, value) {
					bValid = bValid && checkRegexpVal( send_drlc_event_form_tips, senddstep, value.trim(), /^(0x){0,1}([0-9a-fA-F])+$/, "End point must be a number." );
					bValid = bValid && checkRangeVal( send_drlc_event_form_tips, parseInt, senddstep, value.trim(), "end point", 1, 240 );
					if (bValid)
						alleps_array.push(parseInt(value.trim()))
				});
				if ((bValid) && (allnodes_array.length != alleps_array.length)) {
					updateTips( send_drlc_event_form_tips, "Node IDs and End Points do not match." );
					bValid = false;
				}
				if ( bValid ) {
					var jsonData = {};
					jsonData["action"] = "send";
					jsonData["eids"] = allids_array;
					jsonData["nodes"] = allnodes_array;
					jsonData["eps"] = alleps_array;
					var args = JSON.stringify(jsonData);
					//alert(args);
					$( this ).dialog( "close" );
					$.ajax({
						type : "POST",
						url : "/drlc/event",
						data : args,
						contentType : "application/json; charset=utf-8",
						dataType : "json",
						success : function(response) {
							if (response['status'] == 0) {
								clearTimeout(requestDrlcEventsTimer);
								requestDrlcEventsTimer = setTimeout(function () { requestDrlcEvents(); }, 750);
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
	$( "#rm-drlc-event-form" ).dialog({
		autoOpen: false,
		height: 210,
		width: 300,
		modal: true,
		buttons: {
			"Remove DRLC event": function() {
				var bValid = true;
				allFields.removeClass( "ui-state-error" );
				var allids = rmeventid.val().split(",");
				var allids_array = new Array();
				$.each(allids, function(index, value) {
					bValid = bValid && checkRegexpVal( rm_drlc_event_form_tips, rmeventid, value.trim(), /^(0x){0,1}([0-9a-fA-F])+$/, "Event ID must be a number." );
					bValid = bValid && checkRangeVal( rm_drlc_event_form_tips, parseInt, rmeventid, value.trim(), "event ID", 0, 0xFFFFFFFF );
					if (bValid)
						allids_array.push(parseInt(value.trim()))
				});
				if ( bValid ) {
					var jsonData = {};
					jsonData["action"] = "rm";
					jsonData["eids"] = allids_array;
					var args = JSON.stringify(jsonData);
					//alert(args);
					$( this ).dialog( "close" );
					$.ajax({
						type : "POST",
						url : "/drlc/event",
						data : args,
						contentType : "application/json; charset=utf-8",
						dataType : "json",
						success : function(response) {
							if (response['status'] == 0) {
								clearTimeout(requestDrlcEventsTimer);
								requestDrlcEventsTimer = setTimeout(function () { requestDrlcEvents(); }, 750);
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
	$( "#add-drlc-event" )
	.button()
	.click(function() {
		var adddevcls_cbox = $("input:checkbox[name=\"adddevcls\"]:checked");
		adddevcls_cbox.each(function () {
			$(this).prop('checked', false);
		});
		$("input:radio[name=\"addcrit\"]:checked").prop('checked', false);
		var addectrl_cbox = $("input:checkbox[name=\"addectrl\"]:checked");
		addectrl_cbox.each(function () {
			$(this).prop('checked', false);
		});
		$( "#add-drlc-event-form" ).dialog( "open" );
	});
	$( "#send-drlc-event" )
	.button()
	.click(function() {
		$( "#send-drlc-event-form" ).dialog( "open" );
	});
	$( "#rm-drlc-event" )
	.button()
	.click(function() {
		$( "#rm-drlc-event-form" ).dialog( "open" );
	});
	$( "#rm-all-drlc-events" )
	.button()
	.click(function() {
		// remove all DRLC events
		var jsonData = {};
		jsonData["action"] = "clear";
		var args = JSON.stringify(jsonData);
		//alert(args);
		$.ajax({
			type : "POST",
			url : "/drlc/event",
			data : args,
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(response) {
				if (response['status'] == 0) {
					clearTimeout(requestDrlcEventsTimer);
					requestDrlcEventsTimer = setTimeout(function () { requestDrlcEvents(); }, 750);
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
	$( "#refresh-drlc-events" )
	.button()
	.click(function() {
		clearTimeout(requestDrlcEventsTimer);
		requestDrlcEventsTimer = setTimeout(function () { requestDrlcEvents(); }, 750);
	});
	requestDrlcEvents();
});
