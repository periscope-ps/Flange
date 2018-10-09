
var Button = Button || (() => {
    function build(text, target, cb, classes, toggle) {
	if (typeof slide === 'undefined') slide = 'left';
	let _btndown = false;
	let _color = false;
	let _cb = cb || false;
	let _toggle = toggle || false;
	let _lock = false;
	let _state = 0;
	let _names = ($.isArray(text) ? text : [text]);
	classes = ($.isArray(classes) ? classes.concat(["button"]) : ["button"])
	let _raw = $("<label class='" + classes.join(" ") + "'>" + _names[0] + "</label>");
	let self = false;

	if (target)
	    target.append(_raw);
	
	let set_cb = cb => {
	    _cb = cb;
	};

	let get_ref = () => {
	    return _raw;
	};
	let state = (v) => {
	    if (typeof v != 'undefined' && v != _state && !_lock) {
		_state = v;
		for (i in _names) _raw.removeClass("toggle" + i);
		_raw.addClass("toggle" + _state);
		_raw.html(_names[_state]);
		if (cb) {
		    _lock = true;
		    _cb(self);
		    _lock = false;
		}
	    }
	    else return _state;
	};

	self = { setCallback: set_cb, getRef: get_ref, state: state };
	
	let reset = event => {
	    if (_color && !_toggle)
		_raw.css("background-color", "rgb(" + _color[0] + "," + _color[1] + "," + _color[2] + ")");
	    _color = false, _btndown = false;
	};
	let down = event => {
	    var match = _raw.css("background-color").match(/rgba?\((\d{1,3}), ?(\d{1,3}), ?(\d{1,3})\)?(?:, ?(\d(?:\.\d?))\))?/);
	    _color = match ? [match[1], match[2], match[3]] : [255,255,255];
	    if (!_toggle)
		_raw.css("background-color", "rgb(" + (_color[0] - 30) + "," + (_color[1] - 30) + "," + (_color[2] - 30) + ")");
	    _btndown = true;
	};
	let up = event => {
	    if (!_btndown) return;
	    _state = (_state + 1) % _names.length;
	    for (i in _names) _raw.removeClass("toggle" + i);
	    _raw.addClass("toggle" + _state);
	    _raw.html(_names[_state]);
	    reset(event);
	    if (_cb) {
		_lock = true;
		_cb(self);
		_lock = false;
	    }
	};

	_raw.mousedown(down);
	_raw.mouseleave(reset);
	_raw.mouseup(up);

	return self;
    }
    
    return { build: build }
})();
