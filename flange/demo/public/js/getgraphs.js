
$('document').ready(init)

var scale = 1;
var translateX = 0;
var translateY = 0;
var doMove = false;
var eMove = false;
var startX = 0;
var startY = 0;

var _submitDown = false;
var _hideDown = false;
var rule_opacity = 0.6;
var _rulesShown = true;

function setgraph(data) {
    if ($("#f-svg").length) {
	var transform = $("#f-svg")[0].getAttribute('transform');
	var translate = /translate\(\s*([^\s,)]+)[ ,]([^\s,)]+)/.exec(transform);
	var s = /scale\(\s*([^\s,)]+)/.exec(transform);
	translateX = Number(translate[1]);
	translateY = Number(translate[2]);
	scale = Number(s[1]);
    }
    $("#divGraph").html(data);
    var svg = $("#f-svg");
    var g = $("g.rules");
    g.mouseover(highlightRule);
    g.mouseout(dimRule);
    g.mousedown(startMove);
    g.mouseup(stopMove);
    svg.mousedown(startMove);
    svg.mouseup(stopMove);
    svg.mousemove(moveSVG);
    $("circle").mouseover(highlightNode);
    $("circle").mouseout(dimNode);
    eMove = $("#f-svg")[0];
    drawElement();
    stopMove(null);
}

function dimRule(event) {
    $(this).attr('opacity', rule_opacity);
}

function dimNode(event) {
    $("." + $(this).data('rules')).attr('opacity', rule_opacity);
    $(this).attr('r', 5);
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
    data = { "program": $("#flange").val() };
    $.post('f', data, setgraph);
}

function scrollSVG(event) {
    eMove = $("#f-svg")[0];
    var transform = eMove.getAttribute('transform');
    var s = /scale\(\s*([^\s,)]+)/.exec(transform);
    var translate = /translate\(\s*([^\s,)]+)[ ,]([^\s,)]+)/.exec(transform);
    translateX = Number(translate[1]);
    translateY = Number(translate[2]);
    scale = Number(s[1]);
    scale += 0.01 * (0 - event.deltaY);
    drawElement();
    eMove = false;
}

function moveSVG(event) {
    if (eMove) {
	if (eMove == $("#f-svg")[0]) {
	    translateX += event.clientX - startX;
	    translateY += event.clientY - startY;
	}
	else {
	    var line = $("#f-svg").find("#" + eMove.id + "-line")[0];
	    var diffY = Math.abs(translateY - Number(line.getAttribute("y2")));
	    translateX += (event.clientX - startX) / scale;
	    translateY += (event.clientY - startY) / scale;
	    line.setAttribute("x2", translateX + 26)
	    line.setAttribute("y2", translateY + diffY)
	}
	startX = event.clientX;
	startY = event.clientY;
	drawElement();
    }
}

function startMove(event) {
    eMove = event.currentTarget;
    var transform = eMove.getAttribute('transform');
    var translate = /translate\(\s*([^\s,)]+)[ ,]([^\s,)]+)/.exec(transform);
    translateX = Number(translate[1]);
    translateY = Number(translate[2]);
    startX = event.clientX;
    startY = event.clientY;
    return false;
}

function stopMove(event) {
    eMove = false;
}

function drawElement() {
    var transform = 'translate(' + translateX + ' ' + translateY + ')';
    if (eMove == $("#f-svg")[0]) {
	transform += ' scale(' + scale + ')';
    }
    eMove.setAttribute('transform', transform);
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
	}
	else {
	    _rulesShown = true;
	    $(".rules").attr("display", "inline");
	    $(this).find("text").text("Hide Rules");
	    $(this).find("text").attr("font-size", "13");
	}
    }
    hideReset(event);
    return false;
}

function hideReset(event) {
    $(event.currentTarget).find("rect").attr("fill", "rgb(255,120,120)");
    _hideDown = false;
}

function init() {
    var graph = document.getElementById("divGraph");
    $.get('f', setgraph);
    $("#btnPostFlangelet").mousedown(submitDown);
    $("#btnPostFlangelet").mouseleave(submitReset);
    $("#btnPostFlangelet").mouseup(submitUp);
    $("#btnHideRules").mousedown(hideDown);
    $("#btnHideRules").mouseleave(hideReset);
    $("#btnHideRules").mouseup(hideUp);
    $("#flange").keypress(function (event) {
	if ((event.which == 13 || event.which == 10) && event.ctrlKey) {
	    postFlangelet();
	    return false;
	}
    });
    graph.addEventListener("mousewheel", scrollSVG);
}

