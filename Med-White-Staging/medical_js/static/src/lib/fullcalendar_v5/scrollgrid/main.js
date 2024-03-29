/*!
FullCalendar Scheduler v5.3.1
Docs & License: https://fullcalendar.io/scheduler
(c) 2020 Adam Shaw
*/
var FullCalendarScrollGrid = (function (exports, common, premiumCommonPlugin) {
    'use strict';

    premiumCommonPlugin = premiumCommonPlugin && Object.prototype.hasOwnProperty.call(premiumCommonPlugin, 'default') ? premiumCommonPlugin['default'] : premiumCommonPlugin;

    /*! *****************************************************************************
    Copyright (c) Microsoft Corporation.

    Permission to use, copy, modify, and/or distribute this software for any
    purpose with or without fee is hereby granted.

    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
    REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
    AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
    INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
    LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
    OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
    PERFORMANCE OF THIS SOFTWARE.
    ***************************************************************************** */
    /* global Reflect, Promise */

    var extendStatics = function(d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };

    function __extends(d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    }

    var __assign = function() {
        __assign = Object.assign || function __assign(t) {
            for (var s, i = 1, n = arguments.length; i < n; i++) {
                s = arguments[i];
                for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p)) t[p] = s[p];
            }
            return t;
        };
        return __assign.apply(this, arguments);
    };

    function __spreadArrays() {
        for (var s = 0, i = 0, il = arguments.length; i < il; i++) s += arguments[i].length;
        for (var r = Array(s), k = 0, i = 0; i < il; i++)
            for (var a = arguments[i], j = 0, jl = a.length; j < jl; j++, k++)
                r[k] = a[j];
        return r;
    }

    var WHEEL_EVENT_NAMES = 'wheel mousewheel DomMouseScroll MozMousePixelScroll'.split(' ');
    /*
    ALSO, with the ability to disable touch
    */
    var ScrollListener = /** @class */ (function () {
        function ScrollListener(el) {
            var _this = this;
            this.el = el;
            this.emitter = new common.Emitter();
            this.isScrolling = false;
            this.isTouching = false; // user currently has finger down?
            this.isRecentlyWheeled = false;
            this.isRecentlyScrolled = false;
            this.wheelWaiter = new common.DelayedRunner(this._handleWheelWaited.bind(this));
            this.scrollWaiter = new common.DelayedRunner(this._handleScrollWaited.bind(this));
            // Handlers
            // ----------------------------------------------------------------------------------------------
            this.handleScroll = function () {
                _this.startScroll();
                _this.emitter.trigger('scroll', _this.isRecentlyWheeled, _this.isTouching);
                _this.isRecentlyScrolled = true;
                _this.scrollWaiter.request(500);
            };
            // will fire *before* the scroll event is fired (might not cause a scroll)
            this.handleWheel = function () {
                _this.isRecentlyWheeled = true;
                _this.wheelWaiter.request(500);
            };
            // will fire *before* the scroll event is fired (might not cause a scroll)
            this.handleTouchStart = function () {
                _this.isTouching = true;
            };
            this.handleTouchEnd = function () {
                _this.isTouching = false;
                // if the user ended their touch, and the scroll area wasn't moving,
                // we consider this to be the end of the scroll.
                if (!_this.isRecentlyScrolled) {
                    _this.endScroll(); // won't fire if already ended
                }
            };
            el.addEventListener('scroll', this.handleScroll);
            el.addEventListener('touchstart', this.handleTouchStart, { passive: true });
            el.addEventListener('touchend', this.handleTouchEnd);
            for (var _i = 0, WHEEL_EVENT_NAMES_1 = WHEEL_EVENT_NAMES; _i < WHEEL_EVENT_NAMES_1.length; _i++) {
                var eventName = WHEEL_EVENT_NAMES_1[_i];
                el.addEventListener(eventName, this.handleWheel);
            }
        }
        ScrollListener.prototype.destroy = function () {
            var el = this.el;
            el.removeEventListener('scroll', this.handleScroll);
            el.removeEventListener('touchstart', this.handleTouchStart, { passive: true });
            el.removeEventListener('touchend', this.handleTouchEnd);
            for (var _i = 0, WHEEL_EVENT_NAMES_2 = WHEEL_EVENT_NAMES; _i < WHEEL_EVENT_NAMES_2.length; _i++) {
                var eventName = WHEEL_EVENT_NAMES_2[_i];
                el.removeEventListener(eventName, this.handleWheel);
            }
        };
        // Start / Stop
        // ----------------------------------------------------------------------------------------------
        ScrollListener.prototype.startScroll = function () {
            if (!this.isScrolling) {
                this.isScrolling = true;
                this.emitter.trigger('scrollStart', this.isRecentlyWheeled, this.isTouching);
            }
        };
        ScrollListener.prototype.endScroll = function () {
            if (this.isScrolling) {
                this.emitter.trigger('scrollEnd');
                this.isScrolling = false;
                this.isRecentlyScrolled = true;
                this.isRecentlyWheeled = false;
                this.scrollWaiter.clear();
                this.wheelWaiter.clear();
            }
        };
        ScrollListener.prototype._handleScrollWaited = function () {
            this.isRecentlyScrolled = false;
            // only end the scroll if not currently touching.
            // if touching, the scrolling will end later, on touchend.
            if (!this.isTouching) {
                this.endScroll(); // won't fire if already ended
            }
        };
        ScrollListener.prototype._handleWheelWaited = function () {
            this.isRecentlyWheeled = false;
        };
        return ScrollListener;
    }());

    // TODO: assume the el has no borders?
    function getScrollCanvasOrigin(scrollEl) {
        var rect = scrollEl.getBoundingClientRect();
        var edges = common.computeEdges(scrollEl); // TODO: pass in isRtl?
        return {
            left: rect.left + edges.borderLeft + edges.scrollbarLeft - getScrollFromLeftEdge(scrollEl),
            top: rect.top + edges.borderTop - scrollEl.scrollTop
        };
    }
    function getScrollFromLeftEdge(el) {
        var val = el.scrollLeft;
        var computedStyles = window.getComputedStyle(el); // TODO: pass in isRtl?
        if (computedStyles.direction === 'rtl') {
            switch (getRtlScrollSystem()) {
                case 'negative':
                    val = el.scrollWidth - el.clientWidth + val; // maxScrollDistance + val
                    break;
                case 'reverse':
                    val = el.scrollWidth - el.clientWidth - val; // maxScrollDistance - val
                    break;
            }
        }
        return val;
    }
    /*
    `val` is in the "negative" scheme
    */
    function setScrollFromStartingEdge(el, val) {
        var computedStyles = window.getComputedStyle(el); // TODO: pass in isRtl?
        if (computedStyles.direction === 'rtl') {
            switch (getRtlScrollSystem()) {
                case 'positive':
                    val = (el.scrollWidth - el.clientWidth) + val; // maxScrollDistance + val
                    break;
                case 'reverse':
                    val = -val;
                    break;
            }
        }
        el.scrollLeft = val;
    }
    // Horizontal Scroll System Detection
    // ----------------------------------------------------------------------------------------------
    var _rtlScrollSystem;
    function getRtlScrollSystem() {
        return _rtlScrollSystem || (_rtlScrollSystem = detectRtlScrollSystem());
    }
    function detectRtlScrollSystem() {
        var el = document.createElement('div');
        el.style.position = 'absolute';
        el.style.top = '-1000px';
        el.style.width = '1px';
        el.style.height = '1px';
        el.style.overflow = 'scroll';
        el.style.direction = 'rtl';
        el.style.fontSize = '100px';
        el.innerHTML = 'A';
        document.body.appendChild(el);
        var system;
        if (el.scrollLeft > 0) {
            system = 'positive'; // scroll is a positive number from the left edge
        }
        else {
            el.scrollLeft = 1;
            if (el.scrollLeft > 0) {
                system = 'reverse'; // scroll is a positive number from the right edge
            }
            else {
                system = 'negative'; // scroll is a negative number from the right edge
            }
        }
        common.removeElement(el);
        return system;
    }

    var IS_MS_EDGE = /Edge/.test(navigator.userAgent); // TODO: what about Chromeum-based Edge?
    var STICKY_SELECTOR = '.fc-sticky';
    /*
    useful beyond the native position:sticky for these reasons:
    - support in IE11
    - nice centering support

    REQUIREMENT: fc-sticky elements, if the fc-sticky className is taken away, should NOT have relative or absolute positioning.
    This is because we attach the coords with JS, and the VDOM might take away the fc-sticky class but doesn't know kill the positioning.

    TODO: don't query text-align:center. isn't compatible with flexbox centering. instead, check natural X coord within parent container
    */
    var StickyScrolling = /** @class */ (function () {
        function StickyScrolling(scrollEl, isRtl) {
            var _this = this;
            this.scrollEl = scrollEl;
            this.isRtl = isRtl;
            this.usingRelative = null;
            this.updateSize = function () {
                var scrollEl = _this.scrollEl;
                var els = common.findElements(scrollEl, STICKY_SELECTOR);
                var elGeoms = _this.queryElGeoms(els);
                var viewportWidth = scrollEl.clientWidth;
                var viewportHeight = scrollEl.clientHeight;
                if (_this.usingRelative) {
                    var elDestinations = _this.computeElDestinations(elGeoms, viewportWidth); // read before prepPositioning
                    assignRelativePositions(els, elGeoms, elDestinations, viewportWidth, viewportHeight);
                }
                else {
                    assignStickyPositions(els, elGeoms, viewportWidth);
                }
            };
            this.usingRelative =
                !computeStickyPropVal() || // IE11
                    (IS_MS_EDGE && isRtl); // https://stackoverflow.com/questions/56835658/in-microsoft-edge-sticky-positioning-doesnt-work-when-combined-with-dir-rtl
            if (this.usingRelative) {
                this.listener = new ScrollListener(scrollEl);
                this.listener.emitter.on('scrollEnd', this.updateSize);
            }
        }
        StickyScrolling.prototype.destroy = function () {
            if (this.listener) {
                this.listener.destroy();
            }
        };
        StickyScrolling.prototype.queryElGeoms = function (els) {
            var _a = this, scrollEl = _a.scrollEl, isRtl = _a.isRtl;
            var canvasOrigin = getScrollCanvasOrigin(scrollEl);
            var elGeoms = [];
            for (var _i = 0, els_1 = els; _i < els_1.length; _i++) {
                var el = els_1[_i];
                var parentBound = common.translateRect(common.computeInnerRect(el.parentNode, true, true), // weird way to call this!!!
                -canvasOrigin.left, -canvasOrigin.top);
                var elRect = el.getBoundingClientRect();
                var computedStyles = window.getComputedStyle(el);
                var textAlign = window.getComputedStyle(el.parentNode).textAlign; // ask the parent
                var naturalBound = null;
                if (textAlign === 'start') {
                    textAlign = isRtl ? 'right' : 'left';
                }
                else if (textAlign === 'end') {
                    textAlign = isRtl ? 'left' : 'right';
                }
                if (computedStyles.position !== 'sticky') {
                    naturalBound = common.translateRect(elRect, -canvasOrigin.left - (parseFloat(computedStyles.left) || 0), // could be 'auto'
                    -canvasOrigin.top - (parseFloat(computedStyles.top) || 0));
                }
                elGeoms.push({
                    parentBound: parentBound,
                    naturalBound: naturalBound,
                    elWidth: elRect.width,
                    elHeight: elRect.height,
                    textAlign: textAlign
                });
            }
            return elGeoms;
        };
        // only for IE
        StickyScrolling.prototype.computeElDestinations = function (elGeoms, viewportWidth) {
            var scrollEl = this.scrollEl;
            var viewportTop = scrollEl.scrollTop;
            var viewportLeft = getScrollFromLeftEdge(scrollEl);
            var viewportRight = viewportLeft + viewportWidth;
            return elGeoms.map(function (elGeom) {
                var elWidth = elGeom.elWidth, elHeight = elGeom.elHeight, parentBound = elGeom.parentBound, naturalBound = elGeom.naturalBound;
                var destLeft; // relative to canvas topleft
                var destTop; // "
                switch (elGeom.textAlign) {
                    case 'left':
                        destLeft = viewportLeft;
                        break;
                    case 'right':
                        destLeft = viewportRight - elWidth;
                        break;
                    case 'center':
                        destLeft = (viewportLeft + viewportRight) / 2 - elWidth / 2; /// noooo, use half-width insteadddddddd
                        break;
                }
                destLeft = Math.min(destLeft, parentBound.right - elWidth);
                destLeft = Math.max(destLeft, parentBound.left);
                destTop = viewportTop;
                destTop = Math.min(destTop, parentBound.bottom - elHeight);
                destTop = Math.max(destTop, naturalBound.top); // better to use natural top for upper bound
                return { left: destLeft, top: destTop };
            });
        };
        return StickyScrolling;
    }());
    function assignRelativePositions(els, elGeoms, elDestinations, viewportWidth, viewportHeight) {
        els.forEach(function (el, i) {
            var _a = elGeoms[i], naturalBound = _a.naturalBound, parentBound = _a.parentBound;
            var parentWidth = parentBound.right - parentBound.left;
            var parentHeight = parentBound.bottom - parentBound.bottom;
            var left;
            var top;
            if (parentWidth > viewportWidth ||
                parentHeight > viewportHeight) {
                left = elDestinations[i].left - naturalBound.left;
                top = elDestinations[i].top - naturalBound.top;
            }
            else { // if parent container can be completely in view, we don't need stickiness
                left = '';
                top = '';
            }
            common.applyStyle(el, {
                position: 'relative',
                left: left,
                right: -left,
                top: top
            });
        });
    }
    function assignStickyPositions(els, elGeoms, viewportWidth) {
        els.forEach(function (el, i) {
            var _a = elGeoms[i], textAlign = _a.textAlign, elWidth = _a.elWidth, parentBound = _a.parentBound;
            var parentWidth = parentBound.right - parentBound.left;
            var left;
            if (textAlign === 'center' &&
                parentWidth > viewportWidth) {
                left = (viewportWidth - elWidth) / 2;
            }
            else { // if parent container can be completely in view, we don't need stickiness
                left = '';
            }
            common.applyStyle(el, {
                left: left,
                right: left,
                top: 0
            });
        });
    }
    // overkill now that we use the stylesheet to set it!
    // just test that the 'position' value of a div with the fc-sticky classname has the word 'sticky' in it
    function computeStickyPropVal() {
        var el = document.createElement('div');
        el.className = 'fc-sticky';
        document.body.appendChild(el);
        var val = window.getComputedStyle(el).position;
        common.removeElement(el);
        if (val.indexOf('sticky') !== -1) {
            return val;
        }
        else {
            return null;
        }
    }

    var ClippedScroller = /** @class */ (function (_super) {
        __extends(ClippedScroller, _super);
        function ClippedScroller() {
            var _this = _super !== null && _super.apply(this, arguments) || this;
            _this.elRef = common.createRef();
            _this.state = {
                xScrollbarWidth: common.getScrollbarWidths().x,
                yScrollbarWidth: common.getScrollbarWidths().y
            };
            _this.handleScroller = function (scroller) {
                _this.scroller = scroller;
                common.setRef(_this.props.scrollerRef, scroller);
            };
            _this.handleSizing = function () {
                var props = _this.props;
                if (props.overflowY === 'scroll-hidden') {
                    _this.setState({ yScrollbarWidth: _this.scroller.getYScrollbarWidth() });
                }
                if (props.overflowX === 'scroll-hidden') {
                    _this.setState({ xScrollbarWidth: _this.scroller.getXScrollbarWidth() });
                }
            };
            return _this;
        }
        ClippedScroller.prototype.render = function () {
            var _a = this, props = _a.props, state = _a.state, context = _a.context;
            var isScrollbarOnLeft = context.isRtl && common.getIsRtlScrollbarOnLeft();
            var overcomeLeft = 0;
            var overcomeRight = 0;
            var overcomeBottom = 0;
            if (props.overflowX === 'scroll-hidden') {
                overcomeBottom = state.xScrollbarWidth;
            }
            if (props.overflowY === 'scroll-hidden') {
                if (state.yScrollbarWidth != null) {
                    if (isScrollbarOnLeft) {
                        overcomeLeft = state.yScrollbarWidth;
                    }
                    else {
                        overcomeRight = state.yScrollbarWidth;
                    }
                }
            }
            return (common.createElement("div", { ref: this.elRef, className: 'fc-scroller-harness' + (props.liquid ? ' fc-scroller-harness-liquid' : '') },
                common.createElement(common.Scroller, { ref: this.handleScroller, elRef: this.props.scrollerElRef, overflowX: props.overflowX === 'scroll-hidden' ? 'scroll' : props.overflowX, overflowY: props.overflowY === 'scroll-hidden' ? 'scroll' : props.overflowY, overcomeLeft: overcomeLeft, overcomeRight: overcomeRight, overcomeBottom: overcomeBottom, maxHeight: typeof props.maxHeight === 'number' ? (props.maxHeight + (props.overflowX === 'scroll-hidden' ? state.xScrollbarWidth : 0)) : '', liquid: props.liquid, liquidIsAbsolute: true }, props.children)));
        };
        ClippedScroller.prototype.componentDidMount = function () {
            this.handleSizing();
            this.context.addResizeHandler(this.handleSizing);
        };
        ClippedScroller.prototype.componentDidUpdate = function (prevProps) {
            if (!common.isPropsEqual(prevProps, this.props)) { // an external change?
                this.handleSizing();
            }
        };
        ClippedScroller.prototype.componentWillUnmount = function () {
            this.context.removeResizeHandler(this.handleSizing);
        };
        ClippedScroller.prototype.needsXScrolling = function () {
            return this.scroller.needsXScrolling();
        };
        ClippedScroller.prototype.needsYScrolling = function () {
            return this.scroller.needsYScrolling();
        };
        return ClippedScroller;
    }(common.BaseComponent));

    var ScrollSyncer = /** @class */ (function () {
        function ScrollSyncer(isVertical, scrollEls) {
            var _this = this;
            this.isVertical = isVertical;
            this.scrollEls = scrollEls;
            this.isPaused = false;
            this.scrollListeners = scrollEls.map(function (el) { return _this.bindScroller(el); });
        }
        ScrollSyncer.prototype.destroy = function () {
            for (var _i = 0, _a = this.scrollListeners; _i < _a.length; _i++) {
                var scrollListener = _a[_i];
                scrollListener.destroy();
            }
        };
        ScrollSyncer.prototype.bindScroller = function (el) {
            var _this = this;
            var _a = this, scrollEls = _a.scrollEls, isVertical = _a.isVertical;
            var scrollListener = new ScrollListener(el);
            var onScroll = function (isWheel, isTouch) {
                if (!_this.isPaused) {
                    if (!_this.masterEl || (_this.masterEl !== el && (isWheel || isTouch))) {
                        _this.assignMaster(el);
                    }
                    if (_this.masterEl === el) { // dealing with current
                        for (var _i = 0, scrollEls_1 = scrollEls; _i < scrollEls_1.length; _i++) {
                            var otherEl = scrollEls_1[_i];
                            if (otherEl !== el) {
                                if (isVertical) {
                                    otherEl.scrollTop = el.scrollTop;
                                }
                                else {
                                    otherEl.scrollLeft = el.scrollLeft;
                                }
                            }
                        }
                    }
                }
            };
            var onScrollEnd = function () {
                if (_this.masterEl === el) {
                    _this.masterEl = null;
                }
            };
            scrollListener.emitter.on('scroll', onScroll);
            scrollListener.emitter.on('scrollEnd', onScrollEnd);
            return scrollListener;
        };
        ScrollSyncer.prototype.assignMaster = function (el) {
            this.masterEl = el;
            for (var _i = 0, _a = this.scrollListeners; _i < _a.length; _i++) {
                var scrollListener = _a[_i];
                if (scrollListener.el !== el) {
                    scrollListener.endScroll(); // to prevent residual scrolls from reclaiming master
                }
            }
        };
        /*
        will normalize the scrollLeft value
        */
        ScrollSyncer.prototype.forceScrollLeft = function (scrollLeft) {
            this.isPaused = true;
            for (var _i = 0, _a = this.scrollListeners; _i < _a.length; _i++) {
                var listener = _a[_i];
                setScrollFromStartingEdge(listener.el, scrollLeft);
            }
            this.isPaused = false;
        };
        ScrollSyncer.prototype.forceScrollTop = function (top) {
            this.isPaused = true;
            for (var _i = 0, _a = this.scrollListeners; _i < _a.length; _i++) {
                var listener = _a[_i];
                listener.el.scrollTop = top;
            }
            this.isPaused = false;
        };
        return ScrollSyncer;
    }());

    var ScrollGrid = /** @class */ (function (_super) {
        __extends(ScrollGrid, _super);
        function ScrollGrid() {
            var _this = _super !== null && _super.apply(this, arguments) || this;
            _this.compileColGroupStats = common.memoizeArraylike(compileColGroupStat, isColGroupStatsEqual);
            _this.renderMicroColGroups = common.memoizeArraylike(common.renderMicroColGroup); // yucky to memoize VNodes, but much more efficient for consumers
            _this.clippedScrollerRefs = new common.RefMap();
            _this.scrollerElRefs = new common.RefMap(_this._handleScrollerEl.bind(_this)); // doesn't hold non-scrolling els used just for padding
            _this.chunkElRefs = new common.RefMap(_this._handleChunkEl.bind(_this));
            _this.getStickyScrolling = common.memoizeArraylike(initStickyScrolling, null, destroyStickyScrolling);
            _this.getScrollSyncersBySection = common.memoizeHashlike(initScrollSyncer.bind(_this, true), null, destroyScrollSyncer);
            _this.getScrollSyncersByColumn = common.memoizeHashlike(initScrollSyncer.bind(_this, false), null, destroyScrollSyncer);
            _this.stickyScrollings = [];
            _this.scrollSyncersBySection = {};
            _this.scrollSyncersByColumn = {};
            // for row-height-syncing
            _this.rowUnstableMap = new Map(); // no need to groom. always self-cancels
            _this.rowInnerMaxHeightMap = new Map();
            _this.anyRowHeightsChanged = false;
            _this.state = {
                shrinkWidths: [],
                forceYScrollbars: false,
                forceXScrollbars: false,
                scrollerClientWidths: {},
                scrollerClientHeights: {},
                sectionRowMaxHeights: []
            };
            _this.handleSizing = function (isForcedResize, sectionRowMaxHeightsChanged) {
                if (!sectionRowMaxHeightsChanged) { // something else changed, probably external
                    _this.anyRowHeightsChanged = true;
                }
                var otherState = {};
                // if reacting to self-change of sectionRowMaxHeightsChanged, or not stable, don't do anything
                if (isForcedResize || (!sectionRowMaxHeightsChanged && !_this.rowUnstableMap.size)) {
                    otherState.sectionRowMaxHeights = _this.computeSectionRowMaxHeights();
                }
                _this.setState(__assign(__assign({ shrinkWidths: _this.computeShrinkWidths() }, _this.computeScrollerDims()), otherState // wtf
                ), function () {
                    if (!_this.rowUnstableMap.size) {
                        _this.updateStickyScrolling(); // needs to happen AFTER final positioning committed to DOM
                    }
                });
            };
            _this.handleRowHeightChange = function (rowEl, isStable) {
                var _a = _this, rowUnstableMap = _a.rowUnstableMap, rowInnerMaxHeightMap = _a.rowInnerMaxHeightMap;
                if (!isStable) {
                    rowUnstableMap.set(rowEl, true);
                }
                else {
                    rowUnstableMap.delete(rowEl);
                    var innerMaxHeight = getRowInnerMaxHeight(rowEl);
                    if (!rowInnerMaxHeightMap.has(rowEl) || rowInnerMaxHeightMap.get(rowEl) !== innerMaxHeight) {
                        rowInnerMaxHeightMap.set(rowEl, innerMaxHeight);
                        _this.anyRowHeightsChanged = true;
                    }
                    if (!rowUnstableMap.size && _this.anyRowHeightsChanged) {
                        _this.anyRowHeightsChanged = false;
                        _this.setState({
                            sectionRowMaxHeights: _this.computeSectionRowMaxHeights()
                        });
                    }
                }
            };
            return _this;
        }
        ScrollGrid.prototype.render = function () {
            var _a = this, props = _a.props, state = _a.state, context = _a.context;
            var shrinkWidths = state.shrinkWidths;
            var colGroupStats = this.compileColGroupStats(props.colGroups.map(function (colGroup) { return [colGroup]; }));
            var microColGroupNodes = this.renderMicroColGroups(colGroupStats.map(function (stat, i) { return [stat.cols, shrinkWidths[i]]; }));
            var classNames = common.getScrollGridClassNames(props.liquid, context);
            var _b = this.getDims(), sectionCnt = _b[0], chunksPerSection = _b[1];
            // TODO: make DRY
            var sectionConfigs = props.sections;
            var configCnt = sectionConfigs.length;
            var configI = 0;
            var currentConfig;
            var headSectionNodes = [];
            var bodySectionNodes = [];
            var footSectionNodes = [];
            while (configI < configCnt && (currentConfig = sectionConfigs[configI]).type === 'header') {
                headSectionNodes.push(this.renderSection(currentConfig, configI, colGroupStats, microColGroupNodes, state.sectionRowMaxHeights));
                configI++;
            }
            while (configI < configCnt && (currentConfig = sectionConfigs[configI]).type === 'body') {
                bodySectionNodes.push(this.renderSection(currentConfig, configI, colGroupStats, microColGroupNodes, state.sectionRowMaxHeights));
                configI++;
            }
            while (configI < configCnt && (currentConfig = sectionConfigs[configI]).type === 'footer') {
                footSectionNodes.push(this.renderSection(currentConfig, configI, colGroupStats, microColGroupNodes, state.sectionRowMaxHeights));
                configI++;
            }
            var isBuggy = !common.getCanVGrowWithinCell(); // see NOTE in SimpleScrollGrid
            return common.createElement('table', {
                ref: props.elRef,
                className: classNames.join(' ')
            }, renderMacroColGroup(colGroupStats, shrinkWidths), Boolean(!isBuggy && headSectionNodes.length) && common.createElement.apply(void 0, __spreadArrays(['thead', {}], headSectionNodes)), Boolean(!isBuggy && bodySectionNodes.length) && common.createElement.apply(void 0, __spreadArrays(['tbody', {}], bodySectionNodes)), Boolean(!isBuggy && footSectionNodes.length) && common.createElement.apply(void 0, __spreadArrays(['tfoot', {}], footSectionNodes)), isBuggy && common.createElement.apply(void 0, __spreadArrays(['tbody', {}], headSectionNodes, bodySectionNodes, footSectionNodes)));
        };
        ScrollGrid.prototype.renderSection = function (sectionConfig, sectionIndex, colGroupStats, microColGroupNodes, sectionRowMaxHeights) {
            var _this = this;
            if ('outerContent' in sectionConfig) {
                return (common.createElement(common.Fragment, { key: sectionConfig.key }, sectionConfig.outerContent));
            }
            return (common.createElement("tr", { key: sectionConfig.key, className: common.getSectionClassNames(sectionConfig, this.props.liquid).join(' ') }, sectionConfig.chunks.map(function (chunkConfig, i) {
                return _this.renderChunk(sectionConfig, sectionIndex, colGroupStats[i], microColGroupNodes[i], chunkConfig, i, (sectionRowMaxHeights[sectionIndex] || [])[i] || []);
            })));
        };
        ScrollGrid.prototype.renderChunk = function (sectionConfig, sectionIndex, colGroupStat, microColGroupNode, chunkConfig, chunkIndex, rowHeights) {
            if ('outerContent' in chunkConfig) {
                return (common.createElement(common.Fragment, { key: chunkConfig.key }, chunkConfig.outerContent));
            }
            var state = this.state;
            var scrollerClientWidths = state.scrollerClientWidths, scrollerClientHeights = state.scrollerClientHeights;
            var _a = this.getDims(), sectionCnt = _a[0], chunksPerSection = _a[1];
            var index = sectionIndex * chunksPerSection + chunkIndex;
            var sideScrollIndex = (!this.context.isRtl || common.getIsRtlScrollbarOnLeft()) ? chunksPerSection - 1 : 0;
            var isVScrollSide = chunkIndex === sideScrollIndex;
            var isLastSection = sectionIndex === sectionCnt - 1;
            var forceXScrollbars = isLastSection && state.forceXScrollbars; // NOOOO can result in `null`
            var forceYScrollbars = isVScrollSide && state.forceYScrollbars; // NOOOO can result in `null`
            var allowXScrolling = colGroupStat && colGroupStat.allowXScrolling; // rename?
            var allowYScrolling = common.getAllowYScrolling(this.props, sectionConfig); // rename? do in section func?
            var chunkVGrow = common.getSectionHasLiquidHeight(this.props, sectionConfig); // do in section func?
            var expandRows = sectionConfig.expandRows && chunkVGrow;
            var tableMinWidth = (colGroupStat && colGroupStat.totalColMinWidth) || '';
            var content = common.renderChunkContent(sectionConfig, chunkConfig, {
                tableColGroupNode: microColGroupNode,
                tableMinWidth: tableMinWidth,
                clientWidth: scrollerClientWidths[index] !== undefined ? scrollerClientWidths[index] : null,
                clientHeight: scrollerClientHeights[index] !== undefined ? scrollerClientHeights[index] : null,
                expandRows: expandRows,
                syncRowHeights: Boolean(sectionConfig.syncRowHeights),
                rowSyncHeights: rowHeights,
                reportRowHeightChange: this.handleRowHeightChange
            });
            var overflowX = forceXScrollbars ? (isLastSection ? 'scroll' : 'scroll-hidden') :
                !allowXScrolling ? 'hidden' :
                    (isLastSection ? 'auto' : 'scroll-hidden');
            var overflowY = forceYScrollbars ? (isVScrollSide ? 'scroll' : 'scroll-hidden') :
                !allowYScrolling ? 'hidden' :
                    (isVScrollSide ? 'auto' : 'scroll-hidden');
            // it *could* be possible to reduce DOM wrappers by only doing a ClippedScroller when allowXScrolling or allowYScrolling,
            // but if these values were to change, the inner components would be unmounted/remounted because of the parent change.
            content = (common.createElement(ClippedScroller, { ref: this.clippedScrollerRefs.createRef(index), scrollerElRef: this.scrollerElRefs.createRef(index), overflowX: overflowX, overflowY: overflowY, liquid: chunkVGrow, maxHeight: sectionConfig.maxHeight }, content));
            return (common.createElement("td", { key: chunkConfig.key, ref: this.chunkElRefs.createRef(index) }, content));
        };
        ScrollGrid.prototype.componentDidMount = function () {
            this.updateScrollSyncers();
            this.handleSizing(false);
            this.context.addResizeHandler(this.handleSizing);
        };
        ScrollGrid.prototype.componentDidUpdate = function (prevProps, prevState) {
            this.updateScrollSyncers();
            // TODO: need better solution when state contains non-sizing things
            this.handleSizing(false, prevState.sectionRowMaxHeights !== this.state.sectionRowMaxHeights);
        };
        ScrollGrid.prototype.componentWillUnmount = function () {
            this.context.removeResizeHandler(this.handleSizing);
            this.destroyStickyScrolling();
            this.destroyScrollSyncers();
        };
        ScrollGrid.prototype.computeShrinkWidths = function () {
            var _this = this;
            var colGroupStats = this.compileColGroupStats(this.props.colGroups.map(function (colGroup) { return [colGroup]; }));
            var _a = this.getDims(), sectionCnt = _a[0], chunksPerSection = _a[1];
            var cnt = sectionCnt * chunksPerSection;
            var shrinkWidths = [];
            colGroupStats.forEach(function (colGroupStat, i) {
                if (colGroupStat.hasShrinkCol) {
                    var chunkEls = _this.chunkElRefs.collect(i, cnt, chunksPerSection); // in one col
                    shrinkWidths[i] = common.computeShrinkWidth(chunkEls);
                }
            });
            return shrinkWidths;
        };
        // has the side effect of grooming rowInnerMaxHeightMap
        // TODO: somehow short-circuit if there are no new height changes
        ScrollGrid.prototype.computeSectionRowMaxHeights = function () {
            var newHeightMap = new Map();
            var _a = this.getDims(), sectionCnt = _a[0], chunksPerSection = _a[1];
            var sectionRowMaxHeights = [];
            for (var sectionI = 0; sectionI < sectionCnt; sectionI++) {
                var sectionConfig = this.props.sections[sectionI];
                var assignableHeights = []; // chunk, row
                if (sectionConfig && sectionConfig.syncRowHeights) {
                    var rowHeightsByChunk = [];
                    for (var chunkI = 0; chunkI < chunksPerSection; chunkI++) {
                        var index = sectionI * chunksPerSection + chunkI;
                        var rowHeights = [];
                        var chunkEl = this.chunkElRefs.currentMap[index];
                        if (chunkEl) {
                            rowHeights = common.findElements(chunkEl, '.fc-scrollgrid-sync-table tr').map(function (rowEl) {
                                var max = getRowInnerMaxHeight(rowEl);
                                newHeightMap.set(rowEl, max);
                                return max;
                            });
                        }
                        else {
                            rowHeights = [];
                        }
                        rowHeightsByChunk.push(rowHeights);
                    }
                    var rowCnt = rowHeightsByChunk[0].length;
                    var isEqualRowCnt = true;
                    for (var chunkI = 1; chunkI < chunksPerSection; chunkI++) {
                        var isOuterContent = sectionConfig.chunks[chunkI] && sectionConfig.chunks[chunkI].outerContent !== undefined; // can be null
                        if (!isOuterContent && rowHeightsByChunk[chunkI].length !== rowCnt) { // skip outer content
                            isEqualRowCnt = false;
                            break;
                        }
                    }
                    if (!isEqualRowCnt) {
                        var chunkHeightSums = [];
                        for (var chunkI = 0; chunkI < chunksPerSection; chunkI++) {
                            chunkHeightSums.push(sumNumbers(rowHeightsByChunk[chunkI]) + rowHeightsByChunk[chunkI].length // add in border
                            );
                        }
                        var maxTotalSum = Math.max.apply(Math, chunkHeightSums);
                        for (var chunkI = 0; chunkI < chunksPerSection; chunkI++) {
                            var rowInChunkCnt = rowHeightsByChunk[chunkI].length;
                            var rowInChunkTotalHeight = maxTotalSum - rowInChunkCnt; // subtract border
                            var rowInChunkHeightOthers = Math.floor(rowInChunkTotalHeight / rowInChunkCnt); // height of non-first row. we do this to avoid rounding, because it's unreliable within a table
                            var rowInChunkHeightFirst = rowInChunkTotalHeight - rowInChunkHeightOthers * (rowInChunkCnt - 1); // whatever is leftover goes to the first row
                            var rowInChunkHeights = [];
                            var row = 0;
                            if (row < rowInChunkCnt) {
                                rowInChunkHeights.push(rowInChunkHeightFirst);
                                row++;
                            }
                            while (row < rowInChunkCnt) {
                                rowInChunkHeights.push(rowInChunkHeightOthers);
                                row++;
                            }
                            assignableHeights.push(rowInChunkHeights);
                        }
                    }
                    else {
                        for (var chunkI = 0; chunkI < chunksPerSection; chunkI++) {
                            assignableHeights.push([]);
                        }
                        for (var row = 0; row < rowCnt; row++) {
                            var rowHeightsAcrossChunks = [];
                            for (var chunkI = 0; chunkI < chunksPerSection; chunkI++) {
                                var h = rowHeightsByChunk[chunkI][row];
                                if (h != null) { // protect against outerContent
                                    rowHeightsAcrossChunks.push(h);
                                }
                            }
                            var maxHeight = Math.max.apply(Math, rowHeightsAcrossChunks);
                            for (var chunkI = 0; chunkI < chunksPerSection; chunkI++) {
                                assignableHeights[chunkI].push(maxHeight);
                            }
                        }
                    }
                }
                sectionRowMaxHeights.push(assignableHeights);
            }
            this.rowInnerMaxHeightMap = newHeightMap;
            return sectionRowMaxHeights;
        };
        ScrollGrid.prototype.computeScrollerDims = function () {
            var scrollbarWidth = common.getScrollbarWidths();
            var _a = this.getDims(), sectionCnt = _a[0], chunksPerSection = _a[1];
            var sideScrollI = (!this.context.isRtl || common.getIsRtlScrollbarOnLeft()) ? chunksPerSection - 1 : 0;
            var lastSectionI = sectionCnt - 1;
            var currentScrollers = this.clippedScrollerRefs.currentMap;
            var scrollerEls = this.scrollerElRefs.currentMap;
            var forceYScrollbars = false;
            var forceXScrollbars = false;
            var scrollerClientWidths = {};
            var scrollerClientHeights = {};
            for (var sectionI = 0; sectionI < sectionCnt; sectionI++) { // along edge
                var index = sectionI * chunksPerSection + sideScrollI;
                var scroller = currentScrollers[index];
                if (scroller && scroller.needsYScrolling()) {
                    forceYScrollbars = true;
                    break;
                }
            }
            for (var chunkI = 0; chunkI < chunksPerSection; chunkI++) { // along last row
                var index = lastSectionI * chunksPerSection + chunkI;
                var scroller = currentScrollers[index];
                if (scroller && scroller.needsXScrolling()) {
                    forceXScrollbars = true;
                    break;
                }
            }
            for (var sectionI = 0; sectionI < sectionCnt; sectionI++) {
                for (var chunkI = 0; chunkI < chunksPerSection; chunkI++) {
                    var index = sectionI * chunksPerSection + chunkI;
                    var scrollerEl = scrollerEls[index];
                    if (scrollerEl) {
                        var harnessEl = scrollerEl.parentNode; // TODO: weird way to get this. need harness b/c doesn't include table borders
                        scrollerClientWidths[index] = Math.floor(harnessEl.getBoundingClientRect().width - ((chunkI === sideScrollI && forceYScrollbars)
                            ? scrollbarWidth.y // use global because scroller might not have scrollbars yet but will need them in future
                            : 0));
                        scrollerClientHeights[index] = Math.floor(harnessEl.getBoundingClientRect().height - ((sectionI === lastSectionI && forceXScrollbars)
                            ? scrollbarWidth.x // use global because scroller might not have scrollbars yet but will need them in future
                            : 0));
                    }
                }
            }
            return { forceYScrollbars: forceYScrollbars, forceXScrollbars: forceXScrollbars, scrollerClientWidths: scrollerClientWidths, scrollerClientHeights: scrollerClientHeights };
        };
        ScrollGrid.prototype.updateStickyScrolling = function () {
            var isRtl = this.context.isRtl;
            var argsByKey = this.scrollerElRefs.getAll().map(function (scrollEl) { return [scrollEl, isRtl]; });
            var stickyScrollings = this.getStickyScrolling(argsByKey);
            stickyScrollings.forEach(function (stickyScrolling) { return stickyScrolling.updateSize(); });
            this.stickyScrollings = stickyScrollings;
        };
        ScrollGrid.prototype.destroyStickyScrolling = function () {
            this.stickyScrollings.forEach(destroyStickyScrolling);
        };
        ScrollGrid.prototype.updateScrollSyncers = function () {
            var _a = this.getDims(), sectionCnt = _a[0], chunksPerSection = _a[1];
            var cnt = sectionCnt * chunksPerSection;
            var scrollElsBySection = {};
            var scrollElsByColumn = {};
            var scrollElMap = this.scrollerElRefs.currentMap;
            for (var sectionI = 0; sectionI < sectionCnt; sectionI++) {
                var startIndex = sectionI * chunksPerSection;
                var endIndex = startIndex + chunksPerSection;
                scrollElsBySection[sectionI] = common.collectFromHash(scrollElMap, startIndex, endIndex, 1); // use the filtered
            }
            for (var col = 0; col < chunksPerSection; col++) {
                scrollElsByColumn[col] = this.scrollerElRefs.collect(col, cnt, chunksPerSection); // DON'T use the filtered
            }
            this.scrollSyncersBySection = this.getScrollSyncersBySection(scrollElsBySection);
            this.scrollSyncersByColumn = this.getScrollSyncersByColumn(scrollElsByColumn);
        };
        ScrollGrid.prototype.destroyScrollSyncers = function () {
            common.mapHash(this.scrollSyncersBySection, destroyScrollSyncer);
            common.mapHash(this.scrollSyncersByColumn, destroyScrollSyncer);
        };
        ScrollGrid.prototype.getChunkConfigByIndex = function (index) {
            var chunksPerSection = this.getDims()[1];
            var sectionI = Math.floor(index / chunksPerSection);
            var chunkI = index % chunksPerSection;
            var sectionConfig = this.props.sections[sectionI];
            return sectionConfig && sectionConfig.chunks[chunkI];
        };
        ScrollGrid.prototype.forceScrollLeft = function (col, scrollLeft) {
            var scrollSyncer = this.scrollSyncersByColumn[col];
            if (scrollSyncer) {
                scrollSyncer.forceScrollLeft(scrollLeft);
            }
        };
        ScrollGrid.prototype.forceScrollTop = function (sectionI, scrollTop) {
            var scrollSyncer = this.scrollSyncersBySection[sectionI];
            if (scrollSyncer) {
                scrollSyncer.forceScrollTop(scrollTop);
            }
        };
        ScrollGrid.prototype._handleChunkEl = function (chunkEl, key) {
            var chunkConfig = this.getChunkConfigByIndex(parseInt(key, 10));
            if (chunkConfig) { // null if section disappeared. bad, b/c won't null-set the elRef
                common.setRef(chunkConfig.elRef, chunkEl);
            }
        };
        ScrollGrid.prototype._handleScrollerEl = function (scrollerEl, key) {
            var chunkConfig = this.getChunkConfigByIndex(parseInt(key, 10));
            if (chunkConfig) { // null if section disappeared. bad, b/c won't null-set the elRef
                common.setRef(chunkConfig.scrollerElRef, scrollerEl);
            }
        };
        ScrollGrid.prototype.getDims = function () {
            var sectionCnt = this.props.sections.length;
            var chunksPerSection = sectionCnt ? this.props.sections[0].chunks.length : 0;
            return [sectionCnt, chunksPerSection];
        };
        return ScrollGrid;
    }(common.BaseComponent));
    ScrollGrid.addStateEquality({
        shrinkWidths: common.isArraysEqual,
        scrollerClientWidths: common.isPropsEqual,
        scrollerClientHeights: common.isPropsEqual
    });
    function sumNumbers(numbers) {
        var sum = 0;
        for (var _i = 0, numbers_1 = numbers; _i < numbers_1.length; _i++) {
            var n = numbers_1[_i];
            sum += n;
        }
        return sum;
    }
    function getRowInnerMaxHeight(rowEl) {
        var innerHeights = common.findElements(rowEl, '.fc-scrollgrid-sync-inner').map(getElHeight);
        if (innerHeights.length) {
            return Math.max.apply(Math, innerHeights);
        }
        return 0;
    }
    function getElHeight(el) {
        return el.offsetHeight; // better to deal with integers, for rounding, for PureComponent
    }
    function renderMacroColGroup(colGroupStats, shrinkWidths) {
        var children = colGroupStats.map(function (colGroupStat, i) {
            var width = colGroupStat.width;
            if (width === 'shrink') {
                width = colGroupStat.totalColWidth + common.sanitizeShrinkWidth(shrinkWidths[i]) + 1; // +1 for border :(
            }
            return ( // eslint-disable-next-line react/jsx-key
            common.createElement("col", { style: { width: width } }));
        });
        return common.createElement.apply(void 0, __spreadArrays(['colgroup', {}], children));
    }
    function compileColGroupStat(colGroupConfig) {
        var totalColWidth = sumColProp(colGroupConfig.cols, 'width'); // excludes "shrink"
        var totalColMinWidth = sumColProp(colGroupConfig.cols, 'minWidth');
        var hasShrinkCol = common.hasShrinkWidth(colGroupConfig.cols);
        var allowXScrolling = colGroupConfig.width !== 'shrink' && Boolean(totalColWidth || totalColMinWidth || hasShrinkCol);
        return {
            hasShrinkCol: hasShrinkCol,
            totalColWidth: totalColWidth,
            totalColMinWidth: totalColMinWidth,
            allowXScrolling: allowXScrolling,
            cols: colGroupConfig.cols,
            width: colGroupConfig.width
        };
    }
    function sumColProp(cols, propName) {
        var total = 0;
        for (var _i = 0, cols_1 = cols; _i < cols_1.length; _i++) {
            var col = cols_1[_i];
            var val = col[propName];
            if (typeof val === 'number') {
                total += val * (col.span || 1);
            }
        }
        return total;
    }
    var COL_GROUP_STAT_EQUALITY = {
        cols: common.isColPropsEqual
    };
    function isColGroupStatsEqual(stat0, stat1) {
        return common.compareObjs(stat0, stat1, COL_GROUP_STAT_EQUALITY);
    }
    // for memoizers...
    function initScrollSyncer(isVertical) {
        var scrollEls = [];
        for (var _i = 1; _i < arguments.length; _i++) {
            scrollEls[_i - 1] = arguments[_i];
        }
        return new ScrollSyncer(isVertical, scrollEls);
    }
    function destroyScrollSyncer(scrollSyncer) {
        scrollSyncer.destroy();
    }
    function initStickyScrolling(scrollEl, isRtl) {
        return new StickyScrolling(scrollEl, isRtl);
    }
    function destroyStickyScrolling(stickyScrolling) {
        stickyScrolling.destroy();
    }

    var plugin = common.createPlugin({
        deps: [
            premiumCommonPlugin
        ],
        scrollGridImpl: ScrollGrid
    });

    common.globalPlugins.push(plugin);

    exports.ScrollGrid = ScrollGrid;
    exports.default = plugin;
    exports.setScrollFromStartingEdge = setScrollFromStartingEdge;

    return exports;

}({}, FullCalendar, FullCalendarPremiumCommon));
