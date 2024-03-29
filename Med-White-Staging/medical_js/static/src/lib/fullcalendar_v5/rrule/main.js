/*!
FullCalendar v5.3.1
Docs & License: https://fullcalendar.io/
(c) 2020 Adam Shaw
*/
var FullCalendarRRule = (function (exports, common, rrule) {
    'use strict';

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

    var RRULE_EVENT_REFINERS = {
        rrule: common.identity,
        duration: common.createDuration
    };

    var recurring = {
        parse: function (refined, dateEnv) {
            if (refined.rrule != null) {
                var parsed = parseRRule(refined.rrule, dateEnv);
                if (parsed) {
                    return {
                        typeData: parsed.rrule,
                        allDayGuess: parsed.allDayGuess,
                        duration: refined.duration
                    };
                }
            }
            return null;
        },
        expand: function (rrule, framingRange) {
            // we WANT an inclusive start and in exclusive end, but the js rrule lib will only do either BOTH
            // inclusive or BOTH exclusive, which is stupid: https://github.com/jakubroztocil/rrule/issues/84
            // Workaround: make inclusive, which will generate extra occurences, and then trim.
            return rrule.between(framingRange.start, framingRange.end, true)
                .filter(function (date) { return date.valueOf() < framingRange.end.valueOf(); });
        }
    };
    var plugin = common.createPlugin({
        recurringTypes: [recurring],
        eventRefiners: RRULE_EVENT_REFINERS
    });
    function parseRRule(input, dateEnv) {
        var allDayGuess = null;
        var rrule$1;
        if (typeof input === 'string') {
            var preparseData = preparseRRuleStr(input, dateEnv);
            rrule$1 = rrule.rrulestr(preparseData.outStr);
            allDayGuess = preparseData.isTimeUnspecified;
        }
        else if (typeof input === 'object' && input) { // non-null object
            var refined = __assign({}, input); // copy
            if (typeof refined.dtstart === 'string') {
                var dtstartMeta = dateEnv.createMarkerMeta(refined.dtstart);
                if (dtstartMeta) {
                    refined.dtstart = dtstartMeta.marker;
                    allDayGuess = dtstartMeta.isTimeUnspecified;
                }
                else {
                    delete refined.dtstart;
                }
            }
            if (typeof refined.until === 'string') {
                refined.until = dateEnv.createMarker(refined.until);
            }
            if (refined.freq != null) {
                refined.freq = convertConstant(refined.freq);
            }
            if (refined.wkst != null) {
                refined.wkst = convertConstant(refined.wkst);
            }
            else {
                refined.wkst = (dateEnv.weekDow - 1 + 7) % 7; // convert Sunday-first to Monday-first
            }
            if (refined.byweekday != null) {
                refined.byweekday = convertConstants(refined.byweekday); // the plural version
            }
            rrule$1 = new rrule.RRule(refined);
        }
        if (rrule$1) {
            return { rrule: rrule$1, allDayGuess: allDayGuess };
        }
        return null;
    }
    function preparseRRuleStr(str, dateEnv) {
        var isTimeUnspecified = null;
        function processAndReplace(whole, introPart, datePart) {
            var res = dateEnv.parse(datePart);
            if (res) {
                if (res.isTimeUnspecified) {
                    isTimeUnspecified = true;
                }
                return introPart + formatRRuleDate(res.marker);
            }
            else {
                return whole;
            }
        }
        str = str.replace(/\b(DTSTART:)([^\n]*)/, processAndReplace);
        str = str.replace(/\b(EXDATE:)([^\n]*)/, processAndReplace);
        str = str.replace(/\b(UNTIL=)([^;]*)/, processAndReplace);
        return { outStr: str, isTimeUnspecified: isTimeUnspecified };
    }
    function formatRRuleDate(date) {
        return date.toISOString().replace(/[-:]/g, '').replace('.000', '');
    }
    function convertConstants(input) {
        if (Array.isArray(input)) {
            return input.map(convertConstant);
        }
        return convertConstant(input);
    }
    function convertConstant(input) {
        if (typeof input === 'string') {
            return rrule.RRule[input.toUpperCase()];
        }
        return input;
    }

    common.globalPlugins.push(plugin);

    exports.default = plugin;

    return exports;

}({}, FullCalendar, rrule));
