
$('document').ready(init)

var scale = 1;
var svgX = -50;
var svgY = -160;
var svgMatrix = [[1, 0, svgX], [0, 1, svgY], [0, 0, 1]];
var translateX = 0;
var translateY = 0;
var doMove = false;
var eMove = false;
var startX = 0;
var startY = 0;

var source = [];
var sink   = [];
var locStore = {};

var _editMode = false;
var _modifySource = true;

var _modeDown = false;
var _submitDown = false;
var _hideDown = false;
var _netpathDown = false;
var _netpathShown = false;
var _rulesShown = true;
var rule_opacity = 0.6;

function setgraph(data) {
    data = JSON.parse(data);
    if (data.hasOwnProperty('error')) {
	$("#divGraph").html(data["error"]);
	return;
    }
    $("#divGraph").html(data["svg"]);
    if (data.hasOwnProperty('netpath')) {
	for (var i=0; i < data["netpath"].length; i++) {
	    if (typeof data["netpath"][i] === "string") {
		data["netpath"][i] = JSON.parse(data["netpath"][i]);
	    }
	}
	$("#divNetpath").html("<pre>" + JSON.stringify(data["netpath"], null, 2) + "</pre>");
    }
    for (var key in locStore) {
	var target = $("#" + key);
	var transform = target.attr("transform");
	var matrix = /matrix\(\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,)]+)/.exec(transform);
	var cx = Number(matrix[5]);
	var cy = Number(matrix[6]);
	var nx = locStore[key][0];
	var ny = locStore[key][1];
	target.attr("transform", "matrix(1 0 0 1 " + nx + " " + ny + ")");
	$("line").each(function(index) {
	    if ($(this).attr("x1") == cx && $(this).attr("y1") == cy) {
		$(this).attr("x1", nx);
		$(this).attr("y1", ny);
	    }
	    else if ($(this).attr("x2") == cx && $(this).attr("y2") == cy) {
		$(this).attr("x2", nx);
		$(this).attr("y2", ny);
	    }
	});
    }
    var svg = $("#f-svg");
    var g = $("g.rules");
    var circle = $("circle");
    circle.mousedown(startNode);
    circle.mouseup(stopNode);
    g.mouseover(highlightRule);
    g.mouseout(dimRule);
    g.mousedown(startMove);
    g.mouseup(stopMove);
    svg.mousedown(startMove);
    svg.mouseup(stopMove);
    svg.mousemove(moveSVG);
    svg[0].addEventListener('mousewheel', scrollSVG);
    $("circle").mouseover(highlightNode);
    $("circle").mouseout(dimNode);
    eMove = $("#f-svg")[0];
    drawElement();
    stopMove(null);
    
    _editMode = false;
    _modifySource = true;
    $("#btnGraphMode").find("text").text("Display Mode");
    $("#gBuilderConfig").attr("display", "none");
    source = [];
    sink = [];
    
    
}

function dimRule(event) {
    $(this).attr('opacity', rule_opacity);
}

function dimNode(event) {
    $("." + $(this).data('rules')).attr('opacity', rule_opacity);
    $(this).attr('r', 6);
}

function highlightRule(event) {
    $(this).parent().append($(this));
    $(this).attr('opacity', 1);
}

function highlightNode(event) {
    var children = $("." + $(this).data('rules'));
    children.attr('opacity', 1);
    children.parent().append(children);
    $(this).parent().append($(this));
    $(this).attr('r', 8);
}

function postFlangelet() {
    if ($("#flange").val()) {
	data = { "program": $("#flange").val(), "type": "svg,netpath" };
	$.post('f', data, setgraph);
    }
    else {
	$.get('f', setgraph);
    }
}

function matmult(m1, m2) {
    var result = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
    for (i = 0; i < 3; i++) {
	for (j = 0; j < 3; j++) {
	    result[i][j] = (m1[i][0] * m2[0][j]) + (m1[i][1] * m2[1][j]) + (m1[i][2] * m2[2][j]);
	}
    }
    return result;
}

function matrix2mouse(ds, mx, my) {
    var Tin = [[1, 0, -mx], [0, 1, -my], [0, 0, 1]];
    var Tout = [[1, 0, mx], [0, 1, my],  [0, 0, 1]];
    var simulation = matmult(Tout, matmult([[scale,0,0],[0,scale,0],[0,0,1]], Tin));
    svgX += svgMatrix[0][2] - simulation[0][2];
    svgY += svgMatrix[1][2] - simulation[1][2];
    scale = Math.max(0.7, scale + ds);
    var scale_mat = [
	[scale,  0,   0],
	[ 0,  scale,  0],
	[ 0,  0,      1]
    ];
    return matmult(Tout, matmult(scale_mat, Tin));
}

function scrollSVG(event) {
    eMove = $("#f-svg")[0];
    var x = event.offsetX - (eMove.clientWidth / 2);
    var y = event.offsetY - (eMove.clientHeight / 2);
    svgMatrix = matrix2mouse(0.01 * (0 - event.deltaY), x, y);
    drawElement();
    eMove = false;
}

function moveSVG(event) {
    if (eMove) {
	if (eMove == $("#f-svg")[0]) {
	    svgX += event.clientX - startX;
	    svgY += event.clientY - startY;
	}
	else {
	    translateX += (event.clientX - startX) / scale;
	    translateY += (event.clientY - startY) / scale;
	    var target = $(eMove);
	    if (target.is("circle")) {
		var transform = eMove.getAttribute('transform');
		var matrix = /matrix\(\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,)]+)/.exec(transform);
		var cx = Number(matrix[5]);
		var cy = Number(matrix[6]);
		$("line").each(function(index) {
		    if ($(this).attr("x1") == cx && $(this).attr("y1") == cy) {
			$(this).attr("x1", translateX);
			$(this).attr("y1", translateY);
		    }
		    if ($(this).attr("x2") == cx && $(this).attr("y2") == cy) {
			$(this).attr("x2", translateX);
			$(this).attr("y2", translateY);
		    }
		});
		locStore[eMove.id] = [cx, cy];
		target.attr("transform", "matrix(1 0 0 1 " + cx + " " + cy + ")");
	    }
	    else {
		var matrix = 'matrix(1 0 0 1 ' + translateX + ' ' + translateY + ')';
		var line = $("#f-svg").find("#" + eMove.id + "-line")[0];
		line.setAttribute("x2", translateX + 26);
		line.setAttribute("y2", translateY + 17);
		$("#mask-" + eMove.id).attr("transform", matrix);
	    }
	}
	startX = event.clientX;
	startY = event.clientY;
	drawElement();
    }
}

function startNode(event) {
    eMove = event.currentTarget;
    var transform = eMove.getAttribute('transform');
    var matrix = /matrix\(\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,)]+)/.exec(transform);
    translateX = Number(matrix[5]);
    translateY = Number(matrix[6]);
    startX = event.clientX;
    startY = event.clientY;
    return false;
}

function stopNode(event) {
    eMove = false;
}

function startMove(event) {
    eMove = event.currentTarget;
    var transform = eMove.getAttribute('transform');
    var matrix = /matrix\(\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,)]+)/.exec(transform);
    translateX = Number(matrix[5]);
    translateY = Number(matrix[6]);
    startX = event.clientX;
    startY = event.clientY;
    return false;
}

function stopMove(event) {
    eMove = false;
}

function drawElement() {
    var matrix;
    if (eMove == $("#f-svg")[0]) {
	var translate = [
	    [1, 0, svgX],
	    [0, 1, svgY],
	    [0, 0,  1  ]
	];
	matrix = matmult(translate, svgMatrix);
	matrix = 'matrix(' + matrix[0][0] + ' 0 0 ' + matrix[0][0] + ' ' + matrix[0][2] + ' ' + matrix[1][2] + ')';
    }
    else {
	matrix = 'matrix(1 0 0 1 ' + translateX + ' ' + translateY + ')';
    }
    eMove.setAttribute('transform', matrix);
}

function submitDown(event) {
    _submitDown = true;
    $(this).find("rect").attr("fill", "rgb(40,40,255)")
    return false;
}

function submitUp(event) {
    if (_submitDown) {
	postFlangelet();
    }
    submitReset(event);
    return false;
}

function submitReset(event) {
    $(event.currentTarget).find("rect").attr("fill", "rgb(80,80,255)");
    _submitDown = false;
}

function modeDown(event) {
    _modeDown = true;
    $(this).find("rect").attr("fill", "rgb(40,40,255");
}

function buildQuery(event) {
    var name = $(event.currentTarget).find("title").html();
    if (_modifySource) {
	if (source.includes(name)) {
	    var index = source.indexOf(name);
	    source.splice(index, 1);
	    $(event.currentTarget).removeClass("source");
	}
	else {
	    source.push(name);
	    $(event.currentTarget).addClass("source");
	}
    }
    else {
	if (sink.includes(name)) {
	    var index = sink.indexOf(name);
	    sink.splice(index, 1);
	    $(event.currentTarget).removeClass("sink");
	}
	else {
	    sink.push(name);
	    $(event.currentTarget).addClass("sink");
	}
    }
    $("#btnSource").find("text").html("Source: " + source.length);
    $("#btnSink").find("text").html("Sink: " + sink.length);
    setProgram();
}

function setProgram() {
    var program = "";
    if (source.length > 0 || sink.length > 0) {
	program += "exists";
    }
    if (sink.length > 0 && source.length == 0) {
	program += " { x | True }";
    }
    else {
	if (source.length) {
	program += " { x | ";
	    for (var i = 0; i < source.length; i++) {
		program += " x.name == '" + source[i] + "'";
		if (i < source.length - 1) {
		    program += " or";
		}
	    }
	}
	program += " }";
    }
    
    if (sink.length > 0) {
	program += " ~> { x | ";
	for (var i = 0; i < sink.length; i++) {
	    program += " x.name == '" + sink[i] + "'";
	    if (i < sink.length - 1) {
		program += " or";
	    }
	}
	program += " }";
    }
    $("#flange").val(program);
}

function modeUp(event) {
    if (_modeDown) {
	_modeDown = false;
	if (_editMode) {
	    $(this).find("text").text("Display Mode");
	    $("#gBuilderConfig").attr("display", "none");
	    $(".activeOff").removeClass("activeOff source sink").addClass("active");
	    var circle = $("circle");
	    circle.off("click");
	    circle.mousedown(startNode);
	    circle.mouseup(stopNode);
	    _editMode = false;
	}
	else {
	    source = [];
	    sink = [];
	    $(this).find("text").text("Query Builder");
	    var circle = $("circle");
	    circle.click(buildQuery);
	    circle.off("mousedown");
	    circle.off("mouseup");
	    $("#btnSource").find("text").html("Source: 0");
	    $("#btnSink").find("text").html("Sink: 0");
	    $(".active").removeClass("active").addClass("activeOff");
	    $("#gBuilderConfig").attr("display", "inline");
	    _editMode = true;
	}
	modeReset(event);
	return false;
    }
}

function modeReset(event) {
    $(event.currentTarget).find("rect").attr("fill", "rgb(80,80,255)");
    _modeDown = false;
}

function hideDown(event) {
    _hideDown = true;
    $(this).find("rect").attr("fill", "rgb(255,80,80)");
}

function hideUp(event) {
    if (_hideDown) {
	if (_rulesShown) {
	    _rulesShown = false;
	    $(".rules").attr("display", "none");
	    $(this).find("text").text("Show Rules");
	    $(this).find("text").attr("font-size", "12");
	    $(this).find("text").attr("y", "16");
	}
	else {
	    _rulesShown = true;
	    $(".rules").attr("display", "inline");
	    $(this).find("text").text("Hide Rules");
	    $(this).find("text").attr("font-size", "13");
	    $(this).find("text").attr("y", "17");
	}
    }
    hideReset(event);
    return false;
}

function hideReset(event) {
    $(event.currentTarget).find("rect").attr("fill", "rgb(255,120,120)");
    _hideDown = false;
}

function netpathDown(event) {
    $(event.currentTarget).find("rect").attr("fill", "rgb(255,80,80)");
    _netpathDown = true;
}

function netpathUp(event) {
    if (_netpathShown) {
	_netpathShown = false;
	$(event.currentTarget).find("text").html("Show Netpath");
	$(event.currentTarget).find("text").attr("x", "6");
	$("#divNetpath").fadeOut(200, function() { 
	    $("#divGraph").removeClass("hidden") 
	});
    }
    else {
	_netpathShown = true;
	$(event.currentTarget).find("text").html("Hide Netpath");
	$(event.currentTarget).find("text").attr("x", "9");
	$("#divGraph").addClass("hidden");
	$("#divNetpath").fadeIn(200);
    }
    netpathReset(event);
    return false;
}

function netpathReset(event) {
    $(event.currentTarget).find("rect").attr("fill", "rgb(255,120,120)");
    _netpathDown = false;
}

function init() {
    $.get('f', setgraph);
    $("#btnPostFlangelet").mousedown(submitDown);
    $("#btnPostFlangelet").mouseleave(submitReset);
    $("#btnPostFlangelet").mouseup(submitUp);
    $("#btnHideRules").mousedown(hideDown);
    $("#btnHideRules").mouseleave(hideReset);
    $("#btnHideRules").mouseup(hideUp);
    $("#btnShowNetpath").mousedown(netpathDown);
    $("#btnShowNetpath").mouseup(netpathUp);
    $("#btnShowNetpath").mouseleave(netpathReset);
    $("#btnGraphMode").mousedown(modeDown);
    $("#btnGraphMode").mouseup(modeUp);
    $("#btnGraphMode").mouseleave(modeReset);
    $("#btnSource").click(function() { 
	_modifySource = true; 
	$("#btnSource").find("rect").attr("stroke", "rgb(220,100,100)"); 
	$("#btnSink").find("rect").attr("stroke", "rgb(200,200,200)");
    });
    $("#btnSink").click(function() { 
	_modifySource = false;
	$("#btnSource").find("rect").attr("stroke", "rgb(200,200,200)");
	$("#btnSink").find("rect").attr("stroke", "rgb(220,100,100)");
    });
    $("#flange").keypress(function (event) {
	if ((event.which == 13 || event.which == 10) && event.ctrlKey) {
	    postFlangelet();
	    return false;
	}
    });
}

