/*
 * This script will be loaded on every page, since it's referenced by the base.html template.
 */
$(document).ready(function() {
	// bind a handler to the logo, so clicking will return home
	$("#app_header_logo").click(function() {
		location.href = "/";
	})
	// bind more handlers if needed
});
