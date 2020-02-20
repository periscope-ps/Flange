
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

var livesketch = false;
var sketch_listener = false;

var _modifySource = true;

var rule_opacity = 0.6;

function getCoords(path) {
    var d = path.attr('d').substring(1).split('L');
    var s = d[0].split(',');
    var e = d[1].split(',');
    return {
	x1: s[0],
	y1: s[1],
	x2: e[0],
	y2: e[1]
    }
}
function setCoords(path, pairs) {
    path.attr('d', "M" + pairs.x1 + "," + pairs.y1 + "L" + pairs.x2 + "," + pairs.y2);
}

function setgraph(data) {
    data = JSON.parse(data);
    console.log(data)
    if (data.hasOwnProperty('error')) {
	$("#divGraph").html(data["error"]);
	return;
    }
    livesketch = (data.hasOwnProperty("fid") ? data['fid'] : false);
    $("#cnt-code").empty()
    if (livesketch) {
	var submit_btn = Button.build(["Resubmit"], $("#cnt-code"), putFlange, ["emph"]);
    }
    else {
	var submit_btn = Button.build(["Submit"], $("#cnt-code"), postFlange, ["emph"]);
    }
    $("#flange").text((data.hasOwnProperty("text") ? data['text'] : ""));
    $("#divGraph").html(data["svg"]);

    if (data.hasOwnProperty('live') && data['live']) {
	$("#liveid").html(data['fid']);
	$("#divLive").removeClass("hidden");
    }
    else 
	$("#divLive").addClass("hidden");
    
    if (data.hasOwnProperty('netpath')) {
	for (var i=0; i < data["netpath"].length; i++) {
	    if (typeof data["netpath"][i] === "string") {
		data["netpath"][i] = JSON.parse(data["netpath"][i]);
	    }
	}
	$("#divNetpath pre").html(JSON.stringify(data["netpath"], null, 2));
    }
    else
	$("#divNetpath pre").html("");
    if (data.hasOwnProperty('ryu')) {
	for (var i=0; i < data['ryu'].length; i++) {
	    if (typeof data['ryu'][i] === "string") {
		data['ryu'][i] = JSON.parse(data['ryu'][i]);
	    }
	}
	$("#divRyu pre").html(JSON.stringify(data["ryu"], null, 2));
    }
    else
	$("#divRyu pre").html("");
    
    for (var key in locStore) {
	var target = $("#" + key);
	var transform = target.attr("transform");
	var matrix = /matrix\(\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,]+)[ ,]\s*([^\s,)]+)/.exec(transform);
	var cx = Number(matrix[5]), cy = Number(matrix[6]);
	var nx = locStore[key][0], ny = locStore[key][1];
	target.attr("transform", "matrix(1 0 0 1 " + nx + " " + ny + ")");
	$("path").each(function(index) {
	    var coords = getCoords($(this));
	    if (coords.x1 == cx && coords.y1 == cy) {
		coords.x1 = nx, coords.y1 = ny;
		setCoords($(this), coords)
	    }
	    else if (coords.x2 == cx && coords.y2 == cy) {
		coords.x2 = nx, coords.y2 = ny;
		setCoords($(this), coords)
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
		$("path").each(function(index) {
		    var coords = getCoords($(this));
		    if (coords.x1 == cx && coords.y1 == cy) {
			coords.x1 = translateX;
			coords.y1 = translateY;
			setCoords($(this), coords);
		    }
		    if (coords.x2 == cx && coords.y2 == cy) {
			coords.x2 = translateX;
			coords.y2 = translateY;
			setCoords($(this), coords);
		    }
		});
		locStore[eMove.id] = [cx, cy];
		target.attr("transform", "matrix(1 0 0 1 " + cx + " " + cy + ")");
	    }
	    else {
		var matrix = 'matrix(1 0 0 1 ' + translateX + ' ' + translateY + ')';
		var line = $("#f-svg").find("#" + eMove.id + "-line");
		var coords = getCoords(line);
		coords.x2 = translateX + 26;
		coords.y2 = translateY + 17;
		setCoords(line, coords);
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
    $("#btnSource").html("Source: " + source.length);
    $("#btnSink").html("Sink: " + sink.length);
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

function postFlange(btn) {
    if ($("#flange").val()) {
	tys = $("#txtbackends").val() || "svg,netpath";
	mods = $("#txtmods").val();
	data = { "program": $("#flange").val(), "type": tys, "mods": mods };
	$.post('f', data, setgraph);
    }
    else {
	$.get('f', setgraph);
    }
}

function putFlange(btn) {
    if ($("#flange").val()) {
	tys = $("#txtbackends").val() || "svg,netpath";
	mods = $("txtmods").val();
	data = { "program": $("#flange").val(), "type": tys, "mods": mods };
	$.ajax({
	    url: 'f/' + livesketch,
	    data: data,
	    method: 'PUT'}).done(setgraph);
    }
}

function load_livesketch(uid) {
    if (uid) {
	if (sketch_listener) clearInterval(sketch_listener);
    
	sketch_listener = setInterval(() => {
	    $.get('q/' + uid, setgraph).fail(() => {
		if (sketch_listener) clearInterval(sketch_listener);
	    });
	}, 500);
    }
    else {
	clearInterval(sketch_listener);
	$.get('f', setgraph);
    }
}

function ryu_push(btn) {
    $.post('p/' + livesketch);
    load_livesketch(livesketch);
}

function toggle_rules(btn) {
    if (btn.state()) {
	$(".rules").attr("display", "none");
    }
    else {
	$(".rules").attr("display", "inline");
    }
}

function change_display_mode() {
    let show = toggle($("#routebox"));
    function _f(btn) {
	if (btn.state()) {
	    source = [], sink = [];
	    var circle = $("circle");
	    circle.click(buildQuery);
	    circle.off("mousedown");
	    circle.off("mouseup");
	    $("#btnSource").html("Source: 0");
	    $("#btnSink").html("Sink: 0");
	    $(".active").removeClass("active").addClass("activeOff");
	}
	else {
	    $(".activeOff").removeClass("activeOff source sink").addClass("active");
	    var circle = $("circle");
	    circle.off("click");
	    circle.mousedown(startNode);
	    circle.mouseup(stopNode);
	}
	show(btn);
    }
    return _f;
}

function toggle_flangelet_list() {
    let show = toggle($("#flangelet-list"));
    let clear_data = () => {
	$("#flangelet-list .button").off();
	$("#flangelet-list > div").remove();
    };
    let header = $("<div class='header'><label></label><label>ID</label><label>Created</label><label>Modified</label><label>Live</label></div>");
    function _f(btn) {
	let select = k => {
	    let _f = b => {
		load_livesketch((k == livesketch ? false : k));
		btn.state(0);
	    };
	    return _f;
	};
	
	let flangelet_item = (k, d) => {
	    let line = $("<div></div>");
	    let cls = (k == livesketch ? ['active'] : []);
	    let btn = Button.build(["Track"], line, select(k), cls);
	    
	    line.append("<label>" + k + "</label>");
	    line.append("<label>" + d['created'] + "</label>");
	    line.append("<label>" + d['modified'] + "</label>");
	    if (d['live'])
		line.append("<label></label>")
	    return line;
	};
	
	if (btn.state()) {
	    clear_data();
	    $.get('l', function(data) {
		data = JSON.parse(data);
		$("#flangelet-list").append(header);
		for (key in data) {
		    $("#flangelet-list").append(flangelet_item(key, data[key]));
		}
	    });
	}
	show(btn);
    }
    return _f;
}

function toggle_config_list() {
    let show = toggle($("#config-list"));
    function _f(btn) {
	show(btn);
    }
    return _f;
}

function toggle(target, others) {
    let _f = (btn) => {
	if (btn.state()) target.fadeIn(200);
	else target.fadeOut(200);
	if (others)
	    for (i in others)
		others[i].state(0);
    };
    return _f;
}

function init() {
    $.get('f', setgraph);

    var show_sketches = Button.build(["Sketches", "Sketches"], $("#menu"), toggle_flangelet_list(), "", true);
    var show_config = Button.build(["Compiler Options", "Compiler Options"], $("#menu"), toggle_config_list(), "", true);
    
    var submit_btn = Button.build(["Submit"], $("#cnt-code"), postFlange, ["emph"]);
    var netpath_btn = Button.build(["Show Netpath", "Hide Netpath"], $("#sidebar"), toggle($("#divNetpath")));
    netpath_btn.getRef().css({"width": "100px"})
    var ryu_btn = Button.build(["Show Ryu", "Hide Ryu"], $("#divDisplay + .controls"), toggle($("#divRyu")));
    ryu_btn.getRef().css({"width": "90px"});
    var svg_mode_btn = Button.build(["Display Mode", "Query Builder"], $("#svg-btns"), change_display_mode(), ["emph"]);
    var hide_btn = Button.build(["Hide Rules", "Show Rules"], $("#svg-btns"), toggle_rules, ["small"]);
    var accept_ryu = Button.build(["Accept Changes"], $("#cnt-ryu"), ryu_push, ["emph"]);
    
    $("#btnSource").click(function() {
	_modifySource = true;
	$("#btnSource").addClass("selected");
	$("#btnSink").removeClass("selected");
    });
    $("#btnSink").click(function() {
	_modifySource = false;
	$("#btnSource").removeClass("selected");
	$("#btnSink").addClass("selected");
    });
    $("#flange").keypress(function (event) {
	if ((event.which == 13 || event.which == 10) && event.ctrlKey) {
	    postFlange();
	    return false;
	}
    });
}
